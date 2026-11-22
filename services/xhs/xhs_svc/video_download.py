"""通用视频下载（yt-dlp），参考 AI-workspace services/video-download。"""

from __future__ import annotations

import json
import mimetypes
import re
import shutil
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)


class JobCancelled(Exception):
    """yt-dlp progress hook：用户取消。"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_url(text: str) -> str | None:
    text = (text or "").strip()
    if not text:
        return None
    first = text.split()[0]
    if URL_RE.match(first):
        return first.rstrip(").,];}")
    match = URL_RE.search(text)
    return match.group(0).rstrip(").,];}") if match else None


class JobStore:
    def __init__(self, data_root: Path, max_workers: int = 2) -> None:
        self.downloads_dir = data_root / "videos" / "downloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir = data_root / "video-download"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / "jobs.json"
        self.lock = threading.RLock()
        self.jobs: dict[str, dict[str, Any]] = {}
        self.cancel_flags: dict[str, threading.Event] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="xhs-ydl")
        self._load()

    def _load(self) -> None:
        if not self.state_path.is_file():
            return
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            for job in raw.get("jobs") or []:
                if job.get("status") in ("queued", "downloading"):
                    job["status"] = "error"
                    job["error"] = "服务重启，任务中断"
                    job["updated_at"] = utc_now()
                self.jobs[job["id"]] = job
        except Exception:
            self.jobs = {}

    def _persist(self) -> None:
        payload = {"jobs": sorted(self.jobs.values(), key=lambda row: row.get("created_at", ""), reverse=True)}
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)

    def list_jobs(self) -> list[dict[str, Any]]:
        with self.lock:
            return sorted(self.jobs.values(), key=lambda row: row.get("created_at", ""), reverse=True)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self.lock:
            job = self.jobs.get(job_id)
            return dict(job) if job else None

    def create(self, url: str, audio_only: bool = False) -> dict[str, Any]:
        url = extract_url(url) or ""
        if not url:
            raise ValueError("请提供有效的 http(s) 链接")
        job_id = uuid.uuid4().hex[:12]
        now = utc_now()
        job = {
            "id": job_id,
            "url": url,
            "title": url,
            "status": "queued",
            "percent": 0.0,
            "speed": "",
            "eta": "",
            "filename": "",
            "filepath": "",
            "relative_path": "",
            "filesize": 0,
            "audio_only": bool(audio_only),
            "error": "",
            "created_at": now,
            "updated_at": now,
        }
        with self.lock:
            self.jobs[job_id] = job
            self.cancel_flags[job_id] = threading.Event()
            self._persist()
        self.executor.submit(self._run_job, job_id)
        return dict(job)

    def cancel(self, job_id: str) -> dict[str, Any] | None:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            flag = self.cancel_flags.get(job_id)
            if flag:
                flag.set()
            if job["status"] in ("queued", "downloading"):
                job["status"] = "cancelled"
                job["updated_at"] = utc_now()
                self._persist()
            return dict(job)

    def delete(self, job_id: str, remove_file: bool = False) -> bool:
        with self.lock:
            job = self.jobs.pop(job_id, None)
            flag = self.cancel_flags.pop(job_id, None)
            if flag:
                flag.set()
            if not job:
                return False
            if remove_file and job.get("filepath"):
                try:
                    Path(job["filepath"]).unlink(missing_ok=True)
                except OSError:
                    pass
            self._persist()
            return True

    def _update(self, job_id: str, **fields: Any) -> None:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            job.update(fields)
            job["updated_at"] = utc_now()
            if job.get("filepath"):
                try:
                    from xhs_svc.config import workspace_root

                    fp = Path(job["filepath"]).resolve()
                    root = workspace_root()
                    rel = fp.relative_to(root)
                    job["relative_path"] = rel.as_posix()
                except Exception:
                    job["relative_path"] = ""
            self._persist()

    def _run_job(self, job_id: str) -> None:
        job = self.get(job_id)
        if not job:
            return
        cancel = self.cancel_flags.get(job_id) or threading.Event()
        if cancel.is_set():
            return

        try:
            import yt_dlp
        except ImportError:
            self._update(
                job_id,
                status="error",
                error="未安装 yt-dlp。请执行：pip install yt-dlp",
            )
            return

        self._update(job_id, status="downloading", percent=0.0, error="")

        outtmpl = str(self.downloads_dir / "%(title).180B [%(id)s].%(ext)s")
        audio_only = bool(job.get("audio_only"))

        def hook(d: dict[str, Any]) -> None:
            if cancel.is_set():
                raise JobCancelled("cancelled")
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes") or 0
                cur = self.get(job_id) or {}
                percent = round(100.0 * done / total, 1) if total else float(cur.get("percent") or 0)
                self._update(
                    job_id,
                    percent=percent,
                    speed=d.get("_speed_str") or "",
                    eta=d.get("_eta_str") or "",
                    filename=Path(d.get("filename") or "").name or cur.get("filename") or "",
                    filesize=int(total or 0),
                )
            elif status == "finished":
                path = d.get("filename") or ""
                cur = self.get(job_id) or {}
                self._update(
                    job_id,
                    percent=99.0,
                    filename=Path(path).name if path else cur.get("filename") or "",
                    filepath=path,
                    speed="",
                    eta="",
                )

        opts: dict[str, Any] = {
            "outtmpl": outtmpl,
            "progress_hooks": [hook],
            "noprogress": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 3,
            "fragment_retries": 3,
            "concurrent_fragment_downloads": 3,
            "ignoreerrors": False,
        }
        has_ffmpeg = bool(shutil.which("ffmpeg"))
        if audio_only:
            opts["format"] = "bestaudio/best"
            if has_ffmpeg:
                opts["postprocessors"] = [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                ]
        elif has_ffmpeg:
            opts["format"] = "bv*+ba/b"
            opts["merge_output_format"] = "mp4"
        else:
            opts["format"] = "best*[ext=mp4]/best*[ext=webm]/best*/bv*"
            self._update(
                job_id,
                error="提示：本机未检测到 ffmpeg，画质/音轨可能受限；建议安装 ffmpeg",
            )

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(job["url"], download=True)
            if cancel.is_set():
                self._update(job_id, status="cancelled")
                return
            if not info:
                self._update(job_id, status="error", error="未能解析视频信息")
                return

            title = info.get("title") or job["url"]
            requested = info.get("requested_downloads") or []
            filepath = ""
            if requested:
                filepath = requested[0].get("filepath") or ""
            if not filepath:
                filepath = info.get("filepath") or info.get("_filename") or ""
            if not filepath:
                vid = info.get("id") or ""
                candidates = sorted(
                    self.downloads_dir.glob(f"*[{vid}].*") if vid else [],
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if candidates:
                    filepath = str(candidates[0])

            filename = Path(filepath).name if filepath else ""
            filesize = Path(filepath).stat().st_size if filepath and Path(filepath).exists() else 0
            self._update(
                job_id,
                status="done",
                percent=100.0,
                title=title,
                filename=filename,
                filepath=filepath,
                filesize=filesize,
                speed="",
                eta="",
                error="",
            )
        except JobCancelled:
            self._update(job_id, status="cancelled", error="")
        except Exception as exc:  # noqa: BLE001
            if cancel.is_set():
                self._update(job_id, status="cancelled", error="")
            else:
                msg = str(exc)[:500]
                if not has_ffmpeg and ("ffmpeg" in msg.lower() or "format is not available" in msg.lower()):
                    msg = "下载失败：本机缺少 ffmpeg。请安装 ffmpeg 后重试。"
                self._update(job_id, status="error", error=msg)


def ytdlp_available() -> dict[str, Any]:
    try:
        import yt_dlp

        version = getattr(yt_dlp, "version", None)
        ver = getattr(version, "__version__", None) if version else None
        return {"ok": True, "yt_dlp_version": ver, "ffmpeg": bool(shutil.which("ffmpeg"))}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "ffmpeg": bool(shutil.which("ffmpeg"))}


class VideoDownloadAPI:
    def __init__(self, data_root: Path) -> None:
        workers = max(1, int(__import__("os").environ.get("VIDEO_DOWNLOAD_WORKERS", "2")))
        self.store = JobStore(data_root, max_workers=workers)

    def handle(self, handler: BaseHTTPRequestHandler, method: str, path: str, query: str, body: bytes) -> bool:
        route = path.rstrip("/") or "/"
        if not route.startswith("/api/video-download"):
            return False

        if method == "OPTIONS":
            handler.send_response(204)
            handler.end_headers()
            return True

        if method == "GET" and route == "/api/video-download/deps":
            self._json(handler, 200, ytdlp_available())
            return True

        if method == "GET" and route == "/api/video-download/jobs":
            self._json(handler, 200, {"jobs": self.store.list_jobs()})
            return True

        match = re.fullmatch(r"/api/video-download/jobs/([^/]+)", route)
        if method == "GET" and match:
            job = self.store.get(match.group(1))
            if not job:
                self._json(handler, 404, {"error": "任务不存在"})
                return True
            self._json(handler, 200, job)
            return True

        match_file = re.fullmatch(r"/api/video-download/jobs/([^/]+)/file", route)
        if method == "GET" and match_file:
            job = self.store.get(match_file.group(1))
            if not job or job.get("status") != "done" or not job.get("filepath"):
                self._json(handler, 404, {"error": "文件不可用"})
                return True
            fp = Path(job["filepath"])
            if not fp.is_file():
                self._json(handler, 404, {"error": "文件已丢失"})
                return True
            data = fp.read_bytes()
            ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
            handler.send_response(200)
            handler.send_header("Content-Type", ctype)
            handler.send_header("Content-Length", str(len(data)))
            handler.send_header("Content-Disposition", 'attachment; filename="%s"' % fp.name.replace('"', ""))
            handler.end_headers()
            handler.wfile.write(data)
            return True

        if method == "POST" and route == "/api/video-download/jobs":
            payload = self._read_json(body)
            try:
                job = self.store.create(str(payload.get("url") or ""), audio_only=bool(payload.get("audio_only")))
            except ValueError as exc:
                self._json(handler, 400, {"error": str(exc)})
                return True
            self._json(handler, 201, job)
            return True

        match_cancel = re.fullmatch(r"/api/video-download/jobs/([^/]+)/cancel", route)
        if method == "POST" and match_cancel:
            job = self.store.cancel(match_cancel.group(1))
            if not job:
                self._json(handler, 404, {"error": "任务不存在"})
                return True
            self._json(handler, 200, job)
            return True

        if method == "DELETE" and match:
            qs = parse_qs(query or "")
            remove_file = "1" in (qs.get("remove_file") or []) or "true" in (qs.get("remove_file") or [])
            ok = self.store.delete(match.group(1), remove_file=remove_file)
            if not ok:
                self._json(handler, 404, {"error": "任务不存在"})
                return True
            self._json(handler, 200, {"ok": True})
            return True

        self._json(handler, 404, {"error": "not found"})
        return True

    @staticmethod
    def _read_json(body: bytes) -> dict[str, Any]:
        if not body:
            return {}
        try:
            data = json.loads(body.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _json(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(raw)))
        handler.end_headers()
        handler.wfile.write(raw)


_SERVICE: VideoDownloadAPI | None = None


def get_video_download_service(data_root: Path) -> VideoDownloadAPI:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = VideoDownloadAPI(data_root)
    return _SERVICE