#!/usr/bin/env bash
# 为容器镜像准备官方 Codex musl 二进制（不入库）。
# 宿主 macOS 上的 deploy/codex-bin/codex 不能进 Linux 容器。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CORE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$CORE_ROOT/deploy/codex-bin"
OUT="$OUT_DIR/codex-linux"
STAMP="$OUT_DIR/codex-linux.stamp"
CODEX_VERSION="${CODEX_VERSION:-rust-v0.150.1}"

info() { echo "[codex-bin] $*"; }
error() { echo "[codex-bin] ERROR: $*" >&2; }

detect_target() {
  local arch=""
  if command -v docker >/dev/null 2>&1; then
    if [[ "$(id -u)" -eq 0 ]]; then
      arch="$(docker info --format '{{.Architecture}}' 2>/dev/null || true)"
    else
      arch="$(sudo docker info --format '{{.Architecture}}' 2>/dev/null || true)"
    fi
  fi
  if [[ -z "$arch" ]]; then
    arch="$(uname -m)"
  fi
  case "$arch" in
    aarch64|arm64) echo "aarch64-unknown-linux-musl" ;;
    x86_64|amd64) echo "x86_64-unknown-linux-musl" ;;
    *)
      error "不支持的 Docker/CPU 架构: ${arch:-unknown}"
      return 1
      ;;
  esac
}

is_linux_elf() {
  local path="$1"
  [[ -f "$path" && -s "$path" ]] || return 1
  if command -v file >/dev/null 2>&1; then
    file -b "$path" | grep -qi 'ELF'
  else
    # ELF magic: 0x7f 'E' 'L' 'F'
    local magic
    magic="$(dd if="$path" bs=4 count=1 2>/dev/null | od -An -t x1 | tr -d ' \n')"
    [[ "$magic" == "7f454c46" ]]
  fi
}

stamp_matches() {
  [[ -f "$STAMP" ]] || return 1
  # Windows 可能写出 CRLF；勿用 -x（NTFS/Git Bash 常无执行位）
  local got
  got="$(tr -d '\r\n' < "$STAMP")"
  [[ "$got" == "$EXPECTED_STAMP" ]]
}

TARGET="$(detect_target)"
ASSET="codex-${TARGET}.tar.gz"
EXPECTED_STAMP="${CODEX_VERSION} ${TARGET}"

mkdir -p "$OUT_DIR"

# 本地已有 Linux ELF 则直接复用，不因 stamp 缺失/不一致再走 GitHub 下载。
# 版本升级时请删除 $OUT 后再打包。
if is_linux_elf "$OUT"; then
  if stamp_matches; then
    info "已就绪: $OUT ($(tr -d '\r\n' < "$STAMP"))"
  else
    info "沿用已有二进制并写入 stamp: $OUT ($EXPECTED_STAMP)"
    printf '%s\n' "$EXPECTED_STAMP" >"$STAMP"
  fi
  chmod +x "$OUT" 2>/dev/null || true
  exit 0
fi

URLS=(
  "https://github.com/openai/codex/releases/download/${CODEX_VERSION}/${ASSET}"
  "https://mirror.ghproxy.com/https://github.com/openai/codex/releases/download/${CODEX_VERSION}/${ASSET}"
  "https://ghproxy.net/https://github.com/openai/codex/releases/download/${CODEX_VERSION}/${ASSET}"
  "https://ghfast.top/https://github.com/openai/codex/releases/download/${CODEX_VERSION}/${ASSET}"
  "https://gitdl.cn/https://github.com/openai/codex/releases/download/${CODEX_VERSION}/${ASSET}"
)

TMPDIR="$(mktemp -d "${TMPDIR:-/tmp}/codex-bin.XXXXXX")"
ARCHIVE="$TMPDIR/$ASSET"
trap 'rm -rf "$TMPDIR"' EXIT

info "下载 ${CODEX_VERSION} ${ASSET} ..."
downloaded=0
for url in "${URLS[@]}"; do
  info "尝试 $url"
  if curl -fL --retry 2 --retry-delay 2 --connect-timeout 20 --max-time 600 -o "$ARCHIVE" "$url"; then
    downloaded=1
    break
  fi
  rm -f "$ARCHIVE"
done

if [[ "$downloaded" -ne 1 ]]; then
  # 网络失败时：若本地已有可用 ELF，降级沿用（避免编包被镜像站拖死）
  if is_linux_elf "$OUT"; then
    info "下载失败，沿用已有二进制: $OUT"
    printf '%s\n' "$EXPECTED_STAMP" >"$STAMP"
    chmod +x "$OUT" 2>/dev/null || true
    exit 0
  fi
  error "无法下载 Codex Linux 二进制。请手动将 musl 制品解压为:"
  error "  $OUT"
  error "版本: $CODEX_VERSION  目标: $TARGET"
  exit 1
fi

tar -xzf "$ARCHIVE" -C "$TMPDIR"

CANDIDATE=""
while IFS= read -r path; do
  base="$(basename "$path")"
  case "$base" in
    *.sigstore|*.md|*.txt) continue ;;
  esac
  if [[ "$base" == "codex" || "$base" == "codex-${TARGET}" ]]; then
    CANDIDATE="$path"
    break
  fi
done < <(find "$TMPDIR" -type f ! -name "$ASSET")

if [[ -z "$CANDIDATE" ]]; then
  CANDIDATE="$(find "$TMPDIR" -type f -name 'codex' | head -n1 || true)"
fi
if [[ -z "$CANDIDATE" ]]; then
  error "压缩包中未找到 codex 可执行文件"
  find "$TMPDIR" -type f | sed 's/^/[codex-bin]   /' >&2
  exit 1
fi

install -m 0755 "$CANDIDATE" "$OUT"
chmod +x "$OUT" 2>/dev/null || true
if ! is_linux_elf "$OUT"; then
  error "$OUT 不是 Linux ELF，拒绝写入镜像"
  rm -f "$OUT"
  exit 1
fi
printf '%s\n' "$EXPECTED_STAMP" >"$STAMP"
info "已安装 $OUT"
if command -v sha256sum >/dev/null 2>&1; then
  info "sha256 $(sha256sum "$OUT" | awk '{print $1}')"
else
  info "sha256 $(shasum -a 256 "$OUT" | awk '{print $1}')"
fi
