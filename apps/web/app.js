function navIcon(paths) {
  const body = paths.map((d) => `<path d="${d}"/>`).join("");
  return `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;
}

const HOME_ICON = navIcon(["M3 10.5 12 3l9 7.5", "M5 10v10h14V10"]);
const GROUPS = [
  ["热点", [
    ["/hot/today", "当日热点", navIcon(["M4 14a8 8 0 1 1 16 0", "M12 14v-4", "M2 18h20"])],
    ["/hot/news", "新闻爆点", navIcon(["M4 5h16v4", "M4 11h16", "M4 17h10"])],
  ]],
  ["创作", [
    ["/create/article", "一键成文", navIcon(["M13 3 6 14h6l-1 7 8-12h-6l0-6z"])],
    ["/create/cowrite", "协作成文", navIcon(["M12 20h9", "M16.5 3.5a2.1 2.1 0 1 1 3 3L7 19l-4 1 1-4L16.5 3.5z"])],
    ["/create/visual", "一键生图", navIcon(["M4 5h16v14H4z", "M4 15l4-4 3 3 3-4 6 5"])],
  ]],
  ["工具", [
    ["/tools/ask", "AI助手", navIcon(["M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"])],
    ["/tools/extract", "小红书内容提取", navIcon(["M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z", "M14 2v6h6", "M9 13h6", "M9 17h4"])],
    ["/tools/download", "视频下载", navIcon(["M12 3v12", "M7 10l5 5 5-5", "M5 21h14"])],
    ["/tools/review", "复盘", navIcon(["M3 3v18h18", "M7 16l4-6 4 3 5-7"])],
    ["/tools/metrics", "数据跟踪", navIcon(["M4 19V5", "M4 19h16", "M8 16v-4", "M12 16V8", "M16 16v-2"])],
  ]],
  ["资源", [
    ["/library/drafts", "草稿", navIcon(["M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z", "M14 2v6h6", "M8 13h8", "M8 17h5"])],
    ["/library/works", "成品库", navIcon(["M6 3h9l5 5v13H6z", "M15 3v5h5"])],
    ["/library/shelf", "书架", navIcon(["M4 19.5A2.5 2.5 0 0 1 6.5 17H20", "M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"])],
    ["/library/ideas", "灵感库", navIcon(["M9 18h6", "M10 21h4", "M12 3a6 6 0 0 0-3 11c.5.4.8 1 .8 1.6V17h4.4v-1.4c0-.6.3-1.2.8-1.6A6 6 0 0 0 12 3z"])],
    ["/library/videos", "视频库", navIcon(["M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z", "M10 9l6 3-6 3V9z"])],
  ]],
  ["设置", [
    ["/start", "账号配置", navIcon(["M12 21s-6-4.4-6-9a6 6 0 0 1 12 0c0 4.6-6 9-6 9z", "M12 11.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"])],
    ["/settings", "模型配置", navIcon(["M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z", "M12 3v2", "M12 19v2"])],
    ["/system", "系统设置", navIcon(["M4 6h16", "M10 12h4", "M6 18h12"])],
  ]],
];
const REDIRECTS = {
  "/materials": "/hot/today",
  "/topics": "/create/article?step=1",
  "/covers": "/create/visual",
  "/publish": "/create/article?step=6",
  "/reviews": "/tools/review",
  "/knowledge": "/library/shelf",
  "/methods": "/library/ideas",
  "/benchmark": "/hot/today",
  "/low-copy": "/create/article?step=1",
  "/low-image": "/create/visual",
  "/write": "/create/article?step=1",
  "/cowrite": "/create/cowrite",
  "/deai": "/create/article?step=3",
  "/wechat": "/create/article?step=1",
  "/wechat-layout": "/create/visual",
  "/image-account": "/create/article?step=6",
  "/image-clone": "/create/visual",
  "/post-image": "/create/article?step=4",
  "/skills": "/library/ideas",
  "/library/hits": "/hot/today",
  "/ask": "/tools/ask",
  "/videos": "/library/videos",
  "/video-library": "/library/videos",
  "/drafts": "/library/drafts",
};
const ARTICLE_STEPS = ["选题", "写作", "去AI味", "配图", "排版", "发布"];
const ARTICLE_STEP_LEDE = {
  1: "从素材池选一条，生成至少 5 个候选。失败素材不能进入选题。",
  2: "按模板生成 3 到 6 页草稿，不抄素材里的他人正文。",
  3: "改口吻和表达。已确认的版本不会因对话自动改掉。",
  4: "生成封面和各页卡片图。",
  5: "检查溢出，勾完七项后再进入发布。",
  6: "只对当前版本确认。未配置 MCP 时发布会记失败。",
};
const CHEVRON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="m6 9 6 6 6-6"/></svg>`;

const STEP_HREFS = ["/hot/today", "/create/article?step=1", "/create/article?step=1", "/create/article?step=2", "/create/article?step=4", "/create/article?step=6", "/tools/review", "/library/shelf"];
const STEP_NAME = { analyze: "适配", plan: "策划", draft: "文案", visual: "视觉", review: "确认", publish: "发布", retro: "复盘" };
const TEMPLATES = ["知识科普", "教程步骤", "观点分析", "经验分享"];
const DIMS = [
  ["heat", "热度"],
  ["account_match", "账号匹配"],
  ["own_history", "本账号历史"],
  ["strategy", "已确认策略"],
  ["difference", "差异"],
  ["cost", "制作成本"],
];
const PLATFORMS = ["小红书", "抖音", "哔哩哔哩", "微博", "知乎", "人工"];
const KINDS = ["链接", "截图说明", "文案", "竞品账号"];
const REVIEW_ITEMS = [
  ["facts", "事实"],
  ["originality", "原创"],
  ["quality", "内容质量"],
  ["images", "图片"],
  ["layout", "排版"],
  ["title", "标题"],
  ["rules", "平台规则"],
];
let view = document.querySelector("#view");
const toc = document.querySelector("#toc");
let probeMessage = "";
const HOT_COL_PAGE = 15;
const HOT_DOT = { 小红书: "#ff2442", 微博: "#e6162d", 知乎: "#0066ff", 抖音: "#111111", 哔哩哔哩: "#00a1d6", 人工: "oklch(0.48 0.11 168)" };
const HOT_STATUS_ZH = {
  source_unavailable: "采集器未启用",
  failed: "采集失败",
  partial: "部分成功",
  ok: "可用",
  mock_data: "模拟数据",
  browser_unavailable: "浏览器不可用",
  auth_required: "需要登录",
  empty: "没有采到条目",
};
const HOT_COLLECTOR_ZH = { "xiaohongshu-hot-daily": "小红书日榜" };
const XHS_FEED_CHANNELS = ["推荐", "穿搭", "美食", "彩妆", "影视", "职场", "情感", "家居", "游戏", "旅行", "健身", "视频"];
const PLATFORM_ALIASES = { xiaohongshu: "小红书", xhs: "小红书", douyin: "抖音", weibo: "微博", zhihu: "知乎", bilibili: "哔哩哔哩" };

function hotRowPlatform(row) {
  let name = String(row.platform || "").trim();
  if (name === "manual") name = "人工";
  if (PLATFORM_ALIASES[name]) name = PLATFORM_ALIASES[name];
  if (name) return name;
  if (row.collector === "xiaohongshu-hot-daily" || row.collector === "xiaohongshu-dailytop") return "小红书";
  if (String(row.title || "").startsWith("xiaohongshu-hot-daily")) return "小红书";
  if (row.origin === "manual") return "人工";
  return "未标";
}

function hotMaterialHeadline(row) {
  const title = String(row.title || "").trim();
  if (row.origin !== "collect") return title;
  const split = title.split(" · ");
  if (split.length < 2) return HOT_COLLECTOR_ZH[title] || title;
  const collector = split[0];
  return HOT_COLLECTOR_ZH[collector] || collector;
}

function hotMaterialStatus(row) {
  const code = row.error_code || row.status || "";
  if (row.origin === "collect" && row.title.includes(" · ")) {
    const tail = row.title.split(" · ").slice(1).join(" · ");
    if (!code || code === tail) return HOT_STATUS_ZH[tail] || tail;
  }
  return HOT_STATUS_ZH[code] || code;
}
const hotUi = { search: "", platform: "全部", channel: "推荐", period: "week", batches: {}, showCollect: false, lastMode: "" };

function hotCollectBody() {
  const keyword = hotUi.search.trim();
  const body = { capability: "hot_list", category: hotUi.channel || "推荐" };
  if (keyword) body.keyword = keyword;
  return body;
}

function hotFavs() {
  try {
    return new Set(JSON.parse(localStorage.getItem("xhs-hot-fav") || "[]"));
  } catch (error) {
    return new Set();
  }
}

function materialSelectable(row) {
  return (row.status === "ok" || (row.status === "partial" && row.url)) && row.login_free !== false;
}

function withinHotPeriod(iso, period) {
  if (!iso) return true;
  const ms = Date.now() - new Date(iso).getTime();
  const span = (period === "month" ? 30 : 7) * 86400000;
  return ms >= 0 && ms <= span;
}

function formatHotStamp(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16);
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getMonth() + 1}/${d.getDate()} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function hotPlatformLabel(name) {
  return name === "未标" ? "采集记录" : name;
}

function latestHotUpdate(rows) {
  if (!rows.length) return "—";
  let latest = rows[0].created_at || "";
  for (const row of rows) {
    if ((row.created_at || "") > latest) latest = row.created_at;
  }
  return formatHotStamp(latest);
}

function navCurrent(href, path) {
  if (href === path) return true;
  if (href === "/create/article" && path === "/create/article") return true;
  if (href === "/library/drafts" && (path === "/library/drafts" || (path.startsWith("/notes/") && articleCreateMode() === "quick"))) return true;
  if (href === "/create/cowrite" && (path === "/create/cowrite" || (path.startsWith("/notes/") && articleCreateMode() === "collab"))) return true;
  if (href === "/tools/review" && path === "/tools/review") return true;
  return false;
}

function articleCreateMode() {
  try {
    return sessionStorage.getItem("article-create-mode") || "quick";
  } catch (error) {
    return "quick";
  }
}

function articleWizardBase() {
  if (articleCreateMode() === "quick") {
    return "/create/article";
  }
  return location.pathname.startsWith("/create/cowrite") ? "/create/cowrite" : "/create/article";
}

function wizardBar(activeStep) {
  const label = articleWizardBase() === "/create/cowrite" ? "协作成文" : "一键成文";
  return `<nav class="wizard" aria-label="${label}">${ARTICLE_STEPS.map((name, index) => {
    const n = index + 1;
    return `<button type="button" class="wizard-step${n === activeStep ? " current" : ""}" data-wizard-step="${n}"><span class="wizard-num">${n}</span>${name}</button>`;
  }).join("")}</nav>`;
}

function quickWorkflowId() {
  return new URLSearchParams(location.search).get("workflow") || sessionStorage.getItem("quick-workflow-id") || "";
}

function cowriteWorkflowQuery() {
  const wf = quickWorkflowId();
  return wf ? `&workflow=${encodeURIComponent(wf)}` : "";
}

function quickWorkflowQuery() {
  return cowriteWorkflowQuery();
}

function cowriteMaxStep() {
  return Number(sessionStorage.getItem("cowrite-max-step") || 1);
}

function bumpCowriteMax(step) {
  if (step > cowriteMaxStep()) sessionStorage.setItem("cowrite-max-step", String(step));
}

function wizardBarCowrite(activeStep) {
  const max = Math.max(cowriteMaxStep(), activeStep);
  return `<nav class="wizard cowrite-wizard" aria-label="协作成文">${ARTICLE_STEPS.map((name, index) => {
    const n = index + 1;
    const done = n < activeStep || (n < max && n !== activeStep);
    const current = n === activeStep;
    const mark = done ? `<span class="wizard-check" aria-hidden="true">✓</span>` : `<span class="wizard-num">${n}</span>`;
    return `<button type="button" class="wizard-step${current ? " current" : ""}${done ? " done" : ""}" data-wizard-step="${n}">${mark}${name}</button>`;
  }).join("")}</nav>`;
}

async function cowriteAssistantHtml(step) {
  const noteId = sessionStorage.getItem("article-note-id");
  let title = sessionStorage.getItem("cowrite-topic-title") || "—";
  let words = 0;
  if (noteId) {
    try {
      const { data: note } = await api("GET", `/api/xhs/notes/${noteId}`);
      title = note.title || title;
      words = (note.pages || []).reduce((sum, page) => sum + String(page.text || "").length, 0);
    } catch (error) {
      /* keep cache */
    }
  }
  return `<aside class="card cowrite-aside">
    <h2 class="cowrite-aside-title">创作助手</h2>
    <p class="cowrite-aside-kv"><span>创作方式</span><span class="tag ok">协作成文</span></p>
    <p class="cowrite-aside-kv"><span>当前阶段</span><strong>${ARTICLE_STEPS[step - 1]}</strong></p>
    <hr class="cowrite-aside-hr" />
    <p class="cowrite-aside-label">作品</p>
    <p class="cowrite-aside-kv col"><span>文章标题</span><span class="cowrite-aside-val">${escapeHtml(title)}</span></p>
    <p class="cowrite-aside-kv"><span>正文字数</span><strong>${words}</strong></p>
    <p class="lede cowrite-aside-note">展示当前作品状态；保存写入本机服务，确认发布前可反复修改。</p>
  </aside>`;
}

function wireWizard() {
  const base = articleWizardBase();
  const extra = quickWorkflowQuery();
  document.querySelectorAll("[data-wizard-step]").forEach((button) => {
    button.onclick = () => go(`${base}?step=${button.dataset.wizardStep}${extra}`);
  });
}

function wireCowriteFooter(step) {
  document.getElementById("cowrite-back")?.addEventListener("click", () => {
    go(`/create/cowrite?step=${step - 1}${cowriteWorkflowQuery()}`);
  });
  document.getElementById("cowrite-next")?.addEventListener("click", () => {
    bumpCowriteMax(step + 1);
    go(`/create/cowrite?step=${step + 1}${cowriteWorkflowQuery()}`);
  });
}

function paintNav() {
  const path = location.pathname;
  let stored = {};
  try { stored = JSON.parse(localStorage.getItem("xhs-nav") || "{}"); } catch (error) { stored = {}; }
  const groups = GROUPS.map(([label, items]) => {
    const contains = items.some(([href]) => navCurrent(href, path));
    const expanded = contains || stored[label] !== false;
    const links = items.map(([href, name, icon]) => {
      const current = navCurrent(href, path);
      return `<a data-nav href="${href}" class="${current ? "current" : ""}">${icon}<span>${name}</span></a>`;
    }).join("");
    return `<button type="button" class="nav-group" aria-expanded="${expanded ? "true" : "false"}"><span>${label}</span>${CHEVRON}</button><div class="nav-items${expanded ? "" : " collapsed"}">${links}</div>`;
  }).join("");
  toc.innerHTML = `<a data-nav href="/" class="${path === "/" ? "current" : ""}">${HOME_ICON}<span>首页</span></a>${groups}`;
  toc.querySelectorAll(".nav-group").forEach((button) => {
    button.onclick = () => {
      const expanded = button.getAttribute("aria-expanded") === "true";
      button.setAttribute("aria-expanded", expanded ? "false" : "true");
      button.nextElementSibling.classList.toggle("collapsed", expanded);
      const name = button.querySelector("span").textContent;
      stored[name] = !expanded;
      localStorage.setItem("xhs-nav", JSON.stringify(stored));
    };
  });
}

async function api(method, path, body) {
  const response = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (response.status === 204) return { data: null, engine: "" };
  const data = await response.json().catch(() => ({}));
  if (response.status === 401) {
    signedIn = false;
    showLogin(data.error || "请先登录");
    throw new Error(data.error || "请先登录");
  }
  if (!response.ok) throw new Error(data.error || "请求失败");
  return { data, engine: response.headers.get("X-Engine") || "" };
}

let createPendingMaterialId = "";

function ensureCreateModeDialog() {
  if (document.getElementById("create-mode-dialog")) return;
  const wrap = document.createElement("div");
  wrap.id = "create-mode-dialog";
  wrap.className = "create-mode-dialog hidden";
  wrap.setAttribute("role", "dialog");
  wrap.setAttribute("aria-modal", "true");
  wrap.setAttribute("aria-labelledby", "create-mode-title");
  wrap.innerHTML = `
    <div class="create-mode-backdrop" data-create-close></div>
    <div class="create-mode-sheet card">
      <h2 id="create-mode-title">用哪种方式创作？</h2>
      <p class="lede">热点已带入，选一个入口继续。不会在这里开始生成或扣费。</p>
      <button type="button" class="create-mode-opt primary" data-create-mode="quick">
        <span class="create-mode-ico" aria-hidden="true">⚡</span>
        <span class="create-mode-body"><strong>一键成文</strong><small>选定选题后尽量少步自动生成草稿，适合先出稿再改</small></span>
      </button>
      <button type="button" class="create-mode-opt" data-create-mode="collab">
        <span class="create-mode-ico" aria-hidden="true">✍️</span>
        <span class="create-mode-body"><strong>协作成文</strong><small>逐步确认选题、大纲与正文，自己掌控每一步</small></span>
      </button>
      <button type="button" class="create-mode-opt" data-create-mode="visual">
        <span class="create-mode-ico" aria-hidden="true">🖼️</span>
        <span class="create-mode-body"><strong>一键生图</strong><small>写清楚画面提示词，生成封面或独立配图；可上传参考图锁主体</small></span>
      </button>
      <button type="button" class="ghost create-mode-cancel" data-create-close>取消</button>
    </div>`;
  document.body.appendChild(wrap);
  wrap.querySelectorAll("[data-create-close]").forEach((el) => {
    el.addEventListener("click", closeCreateModeDialog);
  });
  wrap.querySelectorAll("[data-create-mode]").forEach((el) => {
    el.addEventListener("click", () => confirmCreateMode(el.dataset.createMode));
  });
}

function openCreateModeDialog(materialId) {
  createPendingMaterialId = materialId;
  ensureCreateModeDialog();
  const dialog = document.getElementById("create-mode-dialog");
  dialog.classList.remove("hidden");
}

function closeCreateModeDialog() {
  createPendingMaterialId = "";
  document.getElementById("create-mode-dialog")?.classList.add("hidden");
}

async function confirmCreateMode(mode) {
  const materialId = createPendingMaterialId;
  closeCreateModeDialog();
  let workflowId = quickWorkflowId();
  if (!workflowId && materialId) {
    const { data: workflow } = await api("POST", "/api/xhs/workflows", { material_ids: [materialId] });
    workflowId = workflow.id;
  }
  if (!workflowId) return;
  sessionStorage.setItem("quick-workflow-id", workflowId);
  const wf = `workflow=${encodeURIComponent(workflowId)}`;
  if (mode === "quick") {
    sessionStorage.setItem("article-create-mode", "quick");
    go(`/create/article?${wf}`);
  } else if (mode === "collab") {
    sessionStorage.setItem("article-create-mode", "collab");
    go(`/create/cowrite?step=1&${wf}`);
  } else if (mode === "visual") {
    sessionStorage.setItem("quick-workflow-id", workflow.id);
    go(`/create/visual?${wf}`);
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function tag(status) {
  const ok = status === "ok" || status === "PUBLISHED" || status === "approved" || status === "selected";
  const bad = ["failed", "empty", "parse_failed", "auth_required", "FAILED", "REJECTED", "rejected", "source_unavailable"].includes(status);
  const kind = ok ? "ok" : bad ? "bad" : "wait";
  return `<span class="tag ${kind}">${escapeHtml(status || "")}</span>`;
}

function taskHref(task) {
  const artifacts = task.artifacts || {};
  if (artifacts.note_id && (task.step === "draft" || task.step === "visual")) return `/notes/${artifacts.note_id}`;
  if (task.step === "publish" || task.step === "review") return "/create/article?step=6";
  if (task.step === "retro") return "/tools/review";
  if (artifacts.note_id) return `/notes/${artifacts.note_id}`;
  return "/create/article?step=1";
}

function go(href) {
  history.pushState({}, "", href);
  render();
}

document.addEventListener("click", (event) => {
  const link = event.target.closest("a[data-nav]");
  if (!link) return;
  event.preventDefault();
  go(link.getAttribute("href"));
});
window.addEventListener("popstate", render);

let videoDownloadPoll = null;

function clearVideoDownloadPoll() {
  if (videoDownloadPoll) {
    clearInterval(videoDownloadPoll);
    videoDownloadPoll = null;
  }
  if (window.__xhsVdlPaste) {
    window.removeEventListener("paste", window.__xhsVdlPaste);
    window.__xhsVdlPaste = null;
  }
}

const VIDEO_URL_RE = /https?:\/\/[^\s<>"']+/i;

function extractVideoUrl(text) {
  const trimmed = String(text || "").trim();
  if (!trimmed) return null;
  const first = trimmed.split(/\s+/)[0];
  if (VIDEO_URL_RE.test(first)) return first.replace(/[).,;\]]+$/, "");
  const match = trimmed.match(VIDEO_URL_RE);
  return match ? match[0].replace(/[).,;\]]+$/, "") : null;
}

function videoJobStatusLabel(status) {
  const map = { queued: "排队中", downloading: "下载中", done: "完成", error: "失败", cancelled: "已取消" };
  return map[status] || status || "";
}

async function videoDownloadApi(method, path, body) {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "请求失败");
  return data;
}

let signedIn = false;

function showLogin(message) {
  document.body.classList.add("need-login");
  const gate = document.getElementById("login-gate");
  if (gate) gate.hidden = false;
  const err = document.getElementById("login-error");
  if (err && message) err.textContent = message;
}

function hideLogin() {
  document.body.classList.remove("need-login");
  const gate = document.getElementById("login-gate");
  if (gate) gate.hidden = true;
  const err = document.getElementById("login-error");
  if (err) err.textContent = "";
}

async function refreshAuth() {
  const response = await fetch("/api/xhs/auth/me", { credentials: "same-origin" });
  signedIn = response.ok;
  if (signedIn) hideLogin();
  else showLogin("");
  return signedIn;
}

async function render() {
  if (!signedIn) {
    const ok = await refreshAuth();
    if (!ok) return;
  }
  view = document.querySelector("#view");
  clearVideoDownloadPoll();
  const path = location.pathname;
  if (REDIRECTS[path]) {
    go(REDIRECTS[path]);
    return;
  }
  paintNav();
  document.querySelector("main")?.classList.toggle("home-active", path === "/" || path === "");
  view.innerHTML = "<p class='lede'>正在读取…</p>";
  try {
    if (path === "/" || path === "") await renderHome();
    else if (path === "/start") await renderStart();
    else if (path === "/hot/today" || path === "/hot/news") await renderHot(path === "/hot/news" ? "news" : "today");
    else if (path === "/create/article") await renderCreateArticle();
    else if (path === "/create/cowrite") {
      sessionStorage.setItem("article-create-mode", "collab");
      await renderCreateCowrite();
    }
    else if (path === "/create/visual") await renderCreateVisual();
    else if (path.startsWith("/notes/")) {
      const noteId = path.split("/")[2];
      if (sessionStorage.getItem("article-create-mode") !== "collab") {
        sessionStorage.setItem("article-create-mode", "quick");
        sessionStorage.setItem("article-note-id", noteId);
      }
      await renderNote(noteId);
    }
    else if (path === "/tools/ask") await renderToolAsk();
    else if (path === "/tools/extract") await renderToolExtract();
    else if (path === "/tools/download") await renderToolDownload();
    else if (path === "/tools/review") await renderReviews();
    else if (path === "/tools/metrics") await renderToolMetrics();
    else if (path === "/library/drafts") await renderLibraryDrafts();
    else if (path === "/library/works") await renderLibraryWorks();
    else if (path === "/library/shelf") await renderLibraryShelf();
    else if (path === "/library/ideas") await renderLibraryIdeas();
    else if (path === "/library/videos") await renderLibraryVideos();
    else if (path === "/settings") await renderSettings();
    else if (path === "/system") await renderSystem();
    else view.innerHTML = "<h1>没有这一页</h1>";
  } catch (error) {
    view.innerHTML = `<h1>没有完成</h1><p class="error">${escapeHtml(error.message)}</p>`;
  }
}

const HOME_ARROW = `<span class="home-arr" aria-hidden="true">↗</span>`;

function homeFeatCard(href, title, desc, mod, decorHtml) {
  return `<a class="home-feat home-feat--${mod}" data-nav href="${href}">
    <span class="home-feat-decor" aria-hidden="true">${decorHtml}</span>
    <span class="home-feat-copy">
      <strong>${escapeHtml(title)}</strong>
      <small>${escapeHtml(desc)}</small>
    </span>
    ${HOME_ARROW}
  </a>`;
}

function homeChip(href, title) {
  return `<a class="home-chip" data-nav href="${href}"><span>${escapeHtml(title)}</span>${HOME_ARROW}</a>`;
}

async function renderHome() {
  const [{ data }, notesRes] = await Promise.all([
    api("GET", "/api/xhs/workflows"),
    api("GET", "/api/xhs/notes").catch(() => ({ data: { notes: [] } })),
  ]);
  const tasks = data.workflows || [];
  const drafts = (notesRes.data.notes || []).filter((n) => (n.publish_status || "DRAFT") === "DRAFT");
  const draftCount = drafts.length;
  const latest = tasks[0];
  const stripText = latest
    ? `进行中的任务：${escapeHtml((latest.artifacts?.title ? `${latest.artifacts.title} · ` : "") + (STEP_NAME[latest.step] || latest.step))} ${tag(latest.state)}`
    : "热点采集、选题与成文有疑问时，可先到 AI 助手多轮对话（会链到草稿、热点与设置）。";
  const stripHref = latest ? taskHref(latest) : "/tools/ask";
  const stripCta = latest ? "继续任务" : "打开 AI 助手";
  const taskList = tasks.length
    ? tasks.slice(0, 4).map((task) => {
        const name = STEP_NAME[task.step] || task.step;
        const title = task.artifacts?.title ? `${task.artifacts.title} · ` : "";
        return `<li><a data-nav href="${taskHref(task)}">${escapeHtml(title + name)}</a> ${tag(task.state)}</li>`;
      }).join("")
    : `<li class="home-task-empty">还没有 workflow。<a data-nav href="/hot/today">去当日热点</a>勾选素材 → 热点分析。</li>`;
  view.innerHTML = `
    <div class="home-bento">
      <section class="home-top">
        <header class="home-hero">
          <p class="home-hero-eyebrow">Personal Workbench</p>
          <h1 class="home-hero-title">小红书运营台</h1>
          <p class="home-hero-lede">热点进站 → 一键或协作成文 → 草稿改稿 → 人工确认发布与复盘。采集与模型按你的配置运行。</p>
          <a class="home-hero-cta" data-nav href="/hot/today">从当日热点开始${HOME_ARROW}</a>
        </header>
        <div class="home-hero-feats">
          ${homeFeatCard("/create/article", "一键成文", "选定方向后直接出稿，改稿在草稿箱", "quick", '<span class="home-deco-aa">稿</span>')}
          ${homeFeatCard("/create/cowrite?step=1", "协作成文", "六步确认选题、正文、配图与发布", "cowrite", '<span class="home-deco-stack"></span>')}
        </div>
      </section>
      <section class="home-mid card">
        <h2 class="home-mid-title">热点 · 成文 · 资源</h2>
        <nav class="home-mid-chips" aria-label="快捷入口">
          ${homeChip("/hot/today", "当日热点")}
          ${homeChip("/hot/news", "新闻爆点")}
          ${homeChip("/library/drafts", draftCount ? `草稿 ${draftCount}` : "草稿")}
          ${homeChip("/library/works", "成品库")}
          ${homeChip("/library/ideas", "灵感库")}
          ${homeChip("/library/shelf", "书架")}
          ${homeChip("/create/visual", "一键生图")}
        </nav>
      </section>
      <section class="home-strip">
        <div class="home-strip-inner">
          <span class="home-strip-dot" aria-hidden="true"></span>
          <p class="home-strip-text">${stripText}</p>
          <a class="home-strip-cta" data-nav href="${escapeHtml(stripHref)}">${stripCta}${HOME_ARROW}</a>
        </div>
      </section>
      <section class="home-bottom">
        <div class="home-bottom-col">
          <a class="home-tool card" data-nav href="/create/visual">
            <strong>一键生图</strong>
            <small>封面与系列配图</small>
            ${HOME_ARROW}
          </a>
          <a class="home-tool card" data-nav href="/tools/extract">
            <strong>内容提取</strong>
            <small>笔记链接 → 结构化素材</small>
            ${HOME_ARROW}
          </a>
        </div>
        <div class="home-bottom-wide card">
          <div class="home-wide-head">
            <div>
              <h2>最近任务 &amp; 工具</h2>
              <p class="lede">侧栏可随时进入复盘、视频下载与模型配置。</p>
            </div>
            <a class="home-wide-link" data-nav href="/tools/ask">AI 助手${HOME_ARROW}</a>
          </div>
          <ul class="home-task-list">${taskList}</ul>
          <div class="home-wide-tools">
            ${homeChip("/tools/review", "复盘")}
            ${homeChip("/tools/metrics", "数据跟踪")}
            ${homeChip("/tools/download", "视频下载")}
            ${homeChip("/settings", "模型配置")}
          </div>
        </div>
      </section>
    </div>`;
}

async function renderStart() {
  const { data } = await api("GET", "/api/xhs/account");
  const types = (data.preferred_types || []).join("、") || "还没填";
  const avoid = (data.avoid || []).join("、") || "还没填";
  const readers = (data.target_audience || []).join("、") || "还没填";
  view.innerHTML = `
    <header class="page-head">
      <p class="eyebrow">// Account</p>
      <h1>账号配置</h1>
      <p class="lede">定位还是「${escapeHtml(data.positioning || "待确定")}」。这一页只读配置，不替你决定方向，也不自动发第一篇。</p>
    </header>
    <section class="card">
      <p>读者：${escapeHtml(readers)}</p>
      <p>内容类型：${escapeHtml(types)}</p>
      <p>语气：${escapeHtml(data.tone || "还没填")}</p>
      <p>避开：${escapeHtml(avoid)}</p>
      <div class="row"><a data-nav href="/hot/today">去当日热点</a><a data-nav href="/tools/ask">打开 AI 助手</a></div>
    </section>`;
}

function filterHotRows(rows, mode) {
  if (mode === "news") {
    return rows.filter((row) => {
      const platform = hotRowPlatform(row);
      if (platform === "小红书" && row.origin === "collect" && row.status === "ok") return false;
      return platform !== "小红书" || row.kind === "文案" || row.kind === "截图说明" || row.kind === "竞品账号";
    });
  }
  return rows.filter((row) => {
    const platform = hotRowPlatform(row);
    if (platform === "小红书") return true;
    const origin = String(row.origin || "");
    if (origin.includes("hot") || origin.includes("daily") || origin === "collect") return true;
    return origin === "manual" && materialSelectable(row) && platform === "小红书";
  });
}

async function renderHot(mode) {
  const news = mode === "news";
  if (hotUi.lastMode !== mode) {
    hotUi.platform = "全部";
    hotUi.search = "";
    hotUi.batches = {};
    if (!news) hotUi.channel = "推荐";
    if (mode === "news") hotUi.period = "week";
    hotUi.lastMode = mode;
  }
  const { data } = await api("GET", "/api/xhs/materials");
  const all = data.materials || [];
  const scoped = filterHotRows(all, mode);
  let pool = scoped;
  if (news) pool = pool.filter((row) => withinHotPeriod(row.created_at, hotUi.period));
  let notice = "";
  if (!pool.length) {
    const rest = all.length - scoped.length;
    if (!scoped.length && all.length) {
      notice = news
        ? "近时段内没有跨平台/人工线索。可改「近一月」或去「当日热点」看小红书采集。"
        : `当日热点下还没有小红书成功采集条目。${rest ? `素材池另有 ${all.length} 条（多在「新闻爆点」），此处不混显。` : "服务启动时会自动补采；也可点「热点采集」立即重试。"}`;
    } else if (news && scoped.length && !pool.length) {
      notice = "近一周没有匹配条目，可切换到「近一月」。";
      pool = scoped;
    }
  }
  const q = hotUi.search.trim().toLowerCase();
  const searched = q
    ? pool.filter((row) => {
        const hay = [row.title, row.url, row.platform, row.kind, row.origin, row.error_code].join(" ").toLowerCase();
        return hay.includes(q);
      })
    : pool;
  const platformCounts = {};
  for (const row of searched) {
    const name = hotRowPlatform(row);
    platformCounts[name] = (platformCounts[name] || 0) + 1;
  }
  const pillOrder = ["全部", ...PLATFORMS, ...Object.keys(platformCounts).filter((name) => !PLATFORMS.includes(name) && name !== "未标"), ...(platformCounts["未标"] ? ["未标"] : [])];
  const visible = hotUi.platform === "全部" ? searched : searched.filter((row) => hotRowPlatform(row) === hotUi.platform);
  const groups = {};
  for (const row of visible) {
    const name = hotRowPlatform(row);
    (groups[name] ||= []).push(row);
  }
  for (const list of Object.values(groups)) {
    list.sort((a, b) => String(b.created_at || "").localeCompare(String(a.created_at || "")));
  }
  const platformNames = Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length);
  const favs = hotFavs();
  const title = news ? "新闻爆点" : "当日热点";
  const lede = news
    ? "浏览素材池里最近一周或一月的跨平台线索。数据只来自真实入库记录，不会假装有外站热榜。"
    : "只展示小红书自动/采集入库的热点。默认按探索频道 Tab 采集；搜索框有词时按关键词采。点「热点采集」入库，失败不混模拟数据。";

  function hotRankTag(row, index) {
    const platform = hotRowPlatform(row);
    if (!materialSelectable(row)) return "";
    if (platform === "小红书") return `热搜 #${index + 1}`;
    return `热点 #${index + 1}`;
  }

  function hotItem(row, index) {
    const ok = materialSelectable(row);
    const headline = hotMaterialHeadline(row);
    const statusLabel = ok ? "" : hotMaterialStatus(row);
    const metaParts = [];
    const rank = hotRankTag(row, index);
    if (rank) metaParts.push(rank);
    if (row.kind) metaParts.push(row.kind);
    if (row.origin === "collect") metaParts.push("采集");
    else if (row.origin === "manual") metaParts.push("手动");
    else if (row.origin) metaParts.push(row.origin);
    if (row.search_keyword) metaParts.push(`关键词 ${row.search_keyword}`);
    else if (row.feed_channel) metaParts.push(`频道 ${row.feed_channel}`);
    metaParts.push(formatHotStamp(row.created_at));
    const sub = metaParts.join(" · ");
    const errMsg = row.error && !statusLabel.includes(row.error) ? row.error : "";
    const err = errMsg ? `<p class="hot-item-err">${escapeHtml(errMsg)}</p>` : "";
    const badge = statusLabel ? `<span class="tag bad">${escapeHtml(statusLabel)}</span>` : "";
    const favOn = favs.has(row.id);
    const titleInner = row.url
      ? `<a class="hot-item-link" href="${escapeHtml(row.url)}" target="_blank" rel="noreferrer" title="在小红书打开">${escapeHtml(headline)}</a>`
      : `<span class="hot-item-link">${escapeHtml(headline)}</span>`;
    return `<li class="hot-item${ok ? "" : " dim"}">
      <div class="hot-item-top">${badge}${titleInner}</div>
      <div class="hot-item-foot">
        <p class="hot-item-meta">${escapeHtml(sub)}</p>
        <div class="hot-item-actions">
          ${ok ? `<button type="button" class="hot-act primary" data-hot-analyze="${escapeHtml(row.id)}">热点分析</button>
          <button type="button" class="ghost hot-act" data-create="${escapeHtml(row.id)}">创作</button>` : `<span class="hot-muted">不可选题</span>`}
          <button type="button" class="ghost hot-fav${favOn ? " on" : ""}" data-fav="${escapeHtml(row.id)}" aria-pressed="${favOn ? "true" : "false"}" title="收藏到本机">★</button>
          <button type="button" class="ghost hot-act" data-delete="${escapeHtml(row.id)}">删除</button>
        </div>
      </div>
      ${err}
    </li>`;
  }

  function hotColumn(name, emptyHint) {
    const list = groups[name] || [];
    const dotColor = HOT_DOT[name] || "var(--muted-foreground)";
    const head = `<header class="hot-col-head">
        <span class="hot-dot" style="background:${dotColor}" aria-hidden="true"></span>
        <h2>${escapeHtml(hotPlatformLabel(name))}</h2>
        <span class="hot-col-count">${list.length} 条</span>
      </header>`;
    if (emptyHint && !list.length) {
      return `<section class="hot-col card hot-col-placeholder">
        ${head}
        <div class="hot-empty-col">
          <p>${escapeHtml(emptyHint)}</p>
          <button type="button" class="ghost hot-open-collect">热点采集</button>
        </div>
        <footer class="hot-col-foot">
          <span class="lede"></span>
          <div class="row"><button type="button" class="ghost" data-refresh-hot>刷新</button></div>
        </footer>
      </section>`;
    }
    const offset = hotUi.batches[name] || 0;
    const slice = list.slice(offset, offset + HOT_COL_PAGE);
    const rest = Math.max(0, list.length - offset - slice.length);
    return `<section class="hot-col card">
      ${head}
      <ul class="hot-list">
        ${slice.map((row, index) => hotItem(row, offset + index)).join("") || "<li class='hot-empty'>暂无条目</li>"}
      </ul>
      <footer class="hot-col-foot">
        <span class="lede">${rest ? `还有 ${rest} 条` : list.length > HOT_COL_PAGE ? "已到末尾" : ""}</span>
        <div class="row">
          ${list.length > HOT_COL_PAGE ? `<button type="button" class="ghost hot-batch" data-platform="${escapeHtml(name)}">换一批</button>` : ""}
          <button type="button" class="ghost" data-refresh-hot>刷新</button>
        </div>
      </footer>
    </section>`;
  }

  const emptyHints = {
    小红书: "还没有成功入库的热点。点工具栏「热点采集」选频道后开始采集。",
    微博: `近${hotUi.period === "month" ? "一月" : "一周"}内还没有微博素材入库。`,
    知乎: `近${hotUi.period === "month" ? "一月" : "一周"}内还没有知乎素材入库。`,
  };
  let plazaColumns = [...platformNames];
  if (!q && hotUi.platform === "全部" && !news && (!platformNames.length || (platformNames.length === 1 && platformNames[0] === "未标"))) {
    plazaColumns = ["小红书", ...(platformNames.includes("未标") ? ["未标"] : [])];
  } else if (!q && hotUi.platform === "全部" && platformNames.length === 1 && platformNames[0] === "未标" && news) {
    plazaColumns = ["微博", "知乎", "未标"];
  }
  let plazaClass = "hot-plaza";
  if (plazaColumns.length === 1) plazaClass = "hot-plaza one-col";
  else if (plazaColumns.length === 2) plazaClass = "hot-plaza two-col";
  else if (plazaColumns.length === 3) plazaClass = "hot-plaza three-col";

  view.innerHTML = `
    <header class="page-head hot-head">
      <div>
        <p class="eyebrow">// ${news ? "News" : "Today"}</p>
        <h1>${title}</h1>
        <p class="lede">${lede}</p>
        ${notice ? `<p class="hot-notice">${escapeHtml(notice)}</p>` : ""}
      </div>
      <p class="hot-stats">${new Set(searched.map(hotRowPlatform)).size} 个平台 · ${searched.length} 条 · 更新于 ${escapeHtml(latestHotUpdate(visible))}</p>
    </header>
  <div class="hot-toolbar card">
    <input id="hot-search" type="search" placeholder="${news ? "搜热点关键词…" : "搜关键词（筛列表；采集时有关键词则走搜索）"}" value="${escapeHtml(hotUi.search)}" />
    ${news ? `<div class="hot-period" role="tablist">
      <button type="button" class="pill${hotUi.period === "week" ? " active" : ""}" data-period="week">近一周</button>
      <button type="button" class="pill${hotUi.period === "month" ? " active" : ""}" data-period="month">近一月</button>
    </div>` : `<button type="button" class="primary" id="hot-toggle-collect">热点采集</button>`}
    <button type="button" class="ghost" id="hot-purge-failures">清空失败记录</button>
  </div>
  ${!news && hotUi.showCollect ? `<section class="card hot-collect-panel">
    <header class="hot-collect-head">
      <h2>热点采集</h2>
      <button type="button" class="ghost" id="hot-close-collect">收起</button>
    </header>
    <p class="lede">选探索频道（默认推荐）。顶栏有搜索词时，本次采集按关键词搜索，不再用频道 Tab。</p>
    <p class="lede hot-login-hint">Docker 采集依赖本机生成的 <code>data/xhs/browser-storage.json</code>。已在本机登录过：先 <code>python scripts/xhs.py browser-export</code>；未登录：<code>browser-login</code>（登录后务必在终端按 Enter）。</p>
    <div class="hot-channels" role="tablist" aria-label="小红书探索频道">
      ${XHS_FEED_CHANNELS.map((name) => `<button type="button" class="pill channel${hotUi.channel === name ? " active" : ""}" data-feed-channel="${escapeHtml(name)}">${escapeHtml(name)}</button>`).join("")}
    </div>
    <div class="row hot-collect-actions">
      <button type="button" class="primary" id="hot-collect-run">开始采集</button>
    </div>
    ${probeMessage ? `<p class="hot-collect-msg">${escapeHtml(probeMessage)}</p>` : ""}
  </section>` : ""}
  <div class="hot-pills" role="tablist">
    ${pillOrder.map((name) => {
      const count = name === "全部" ? searched.length : platformCounts[name] || 0;
      if (name !== "全部" && !count) return "";
      return `<button type="button" class="pill${hotUi.platform === name ? " active" : ""}" data-platform="${escapeHtml(name)}">${escapeHtml(hotPlatformLabel(name))}${count ? ` (${count})` : ""}</button>`;
    }).join("")}
  </div>
  <div class="${plazaClass}">
    ${(() => {
      const cols = plazaColumns.length ? plazaColumns : platformNames;
      if (!cols.length) {
        return `<section class="card hot-empty-card"><p>还没有热点。点工具栏「热点采集」选择频道后开始采集。</p>
        <div class="row"><button type="button" class="primary" id="hot-open-collect-inline">热点采集</button><a data-nav href="/system">系统设置</a></div></section>`;
      }
      return cols.map((name) => hotColumn(name, (groups[name] || []).length ? "" : emptyHints[name] || "")).join("");
    })()}
  </div>`;

  let searchTimer;
  document.querySelector("#hot-search")?.addEventListener("input", (event) => {
    hotUi.search = event.target.value;
    hotUi.batches = {};
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => renderHot(mode), 300);
  });
  view.querySelectorAll("[data-platform]").forEach((button) => {
    button.onclick = () => {
      hotUi.platform = button.dataset.platform;
      hotUi.batches = {};
      renderHot(mode);
    };
  });
  view.querySelectorAll("[data-feed-channel]").forEach((button) => {
    button.onclick = () => {
      hotUi.channel = button.dataset.feedChannel;
      renderHot(mode);
    };
  });
  view.querySelectorAll("[data-period]").forEach((button) => {
    button.onclick = () => {
      hotUi.period = button.dataset.period;
      hotUi.batches = {};
      renderHot(mode);
    };
  });
  const openCollect = () => {
    hotUi.showCollect = true;
    renderHot(mode);
  };
  document.querySelector("#hot-toggle-collect")?.addEventListener("click", openCollect);
  document.querySelector("#hot-close-collect")?.addEventListener("click", () => {
    hotUi.showCollect = false;
    renderHot(mode);
  });
  document.querySelector("#hot-purge-failures")?.addEventListener("click", async () => {
    if (!confirm("删除素材池里所有采集失败、且无链接的记录？")) return;
    const { data } = await api("POST", "/api/xhs/materials/purge-failures");
    probeMessage = data.deleted ? `已清空 ${data.deleted} 条失败记录` : "没有可清空的失败记录";
    renderHot(mode);
  });
  view.querySelectorAll(".hot-open-collect, #hot-open-collect-inline").forEach((button) => {
    button.onclick = openCollect;
  });
  view.querySelectorAll("[data-refresh-hot]").forEach((button) => {
    button.onclick = () => renderHot(mode);
  });
  view.querySelectorAll(".hot-batch").forEach((button) => {
    button.onclick = () => {
      const name = button.dataset.platform;
      const total = (groups[name] || []).length;
      const cur = hotUi.batches[name] || 0;
      const next = cur + HOT_COL_PAGE;
      hotUi.batches[name] = next >= total ? 0 : next;
      renderHot(mode);
    };
  });
  async function startWorkflow(id) {
    const { data: workflow } = await api("POST", "/api/xhs/workflows", { material_ids: [id] });
    sessionStorage.setItem("quick-workflow-id", workflow.id);
    openCreateModeDialog(id);
  }
  view.querySelectorAll("[data-hot-analyze]").forEach((button) => {
    button.onclick = () => startWorkflow(button.dataset.hotAnalyze);
  });
  view.querySelectorAll("[data-create]").forEach((button) => {
    button.onclick = () => openCreateModeDialog(button.dataset.create);
  });
  view.querySelectorAll("[data-fav]").forEach((button) => {
    button.onclick = () => {
      const set = hotFavs();
      const id = button.dataset.fav;
      if (set.has(id)) set.delete(id);
      else set.add(id);
      localStorage.setItem("xhs-hot-fav", JSON.stringify([...set]));
      renderHot(mode);
    };
  });
  view.querySelectorAll("[data-delete]").forEach((button) => {
    button.onclick = async () => {
      await api("DELETE", "/api/xhs/materials/" + button.dataset.delete);
      renderHot(mode);
    };
  });

  async function runHotCollect(body) {
    hotUi.showCollect = true;
    probeMessage = "采集中（后台 Playwright，约 20–60 秒）…";
    await renderHot(mode);
    const runBtn = document.querySelector("#hot-collect-run");
    if (runBtn) {
      runBtn.disabled = true;
      runBtn.textContent = "采集中…";
    }
    try {
      const { data: result } = await api("POST", "/api/xhs/collect", body);
      const cat = body.category || "推荐";
      const kw = body.keyword ? ` · 关键词 ${body.keyword}` : cat !== "推荐" ? ` · 频道 ${cat}` : "";
      probeMessage = `${result.status}${kw} · ${(result.error && result.error.code) || ""} · 条目 ${(result.items || []).length}`;
    } catch (error) {
      probeMessage = `采集请求失败：${error.message || error}`;
    }
    renderHot(mode);
  }
  document.querySelector("#hot-collect-run")?.addEventListener("click", () => runHotCollect(hotCollectBody()));
}

async function renderTopics(embedded) {
  const { data } = await api("GET", "/api/xhs/topics");
  const topics = data.topics || [];
  const head = embedded
    ? ""
    : `<header class="page-head">
      <p class="eyebrow">// Topics</p>
      <h1>适配与选题</h1>
      <p class="lede">定位还没定时，适配保持「中」，用来做小实验，不写成长期方向。选定后再按模板生成草稿。</p>
    </header>`;
  view.innerHTML = `${head}
    ${reportBlock(data.report)}
    <section class="card">
      ${topics.map((topic) => {
        const dims = (topic.plan && topic.plan.dimensions) || {};
        const selected = (topic.plan && topic.plan.template) || "教程步骤";
        const pages = (topic.plan && topic.plan.page_count) || 4;
        const source = topic.source || {};
        return `
        <article data-id="${escapeHtml(topic.id)}">
          <h2>${escapeHtml(topic.title)}</h2>
          <p>${tag(topic.status)} ${tag(topic.fit)} ${escapeHtml(topic.fit_reason)}</p>
          ${source.url ? `<p class="lede">来源 ${escapeHtml(source.platform || "")} <a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.url)}</a></p>` : `<p class="lede">来源 ${escapeHtml(source.title || "人工素材")}</p>`}
          <dl class="dims">${DIMS.map(([key, label]) => `<dt>${label}</dt><dd>${escapeHtml(dims[key] || "—")}</dd>`).join("")}</dl>
          ${topic.script ? `<pre class="answer">${escapeHtml(topic.script)}</pre>` : ""}
          <label>改写标题</label><input data-title value="${escapeHtml(topic.title)}" />
          <label>模板</label>
          <select data-template>${TEMPLATES.map((name) => `<option ${name === selected ? "selected" : ""}>${name}</option>`).join("")}</select>
          <label>页数</label>
          <select data-pages>${[3, 4, 5, 6].map((count) => `<option ${count === pages ? "selected" : ""}>${count}</option>`).join("")}</select>
          <p class="error" data-topic-error></p>
          <div class="row">
            <button type="button" data-select="${escapeHtml(topic.id)}">选定</button>
            <button class="ghost" type="button" data-reject="${escapeHtml(topic.id)}">否决</button>
            <button class="ghost" type="button" data-rename="${escapeHtml(topic.id)}">改写</button>
            <button class="ghost" type="button" data-plan="${escapeHtml(topic.id)}">写选题方案</button>
            <button class="ghost" type="button" data-draft="${escapeHtml(topic.id)}">按模板生成草稿</button>
          </div>
        </article>`;
      }).join("") || "<p>还没有选题。先从<a data-nav href=\"/hot/today\">当日热点</a>勾选素材。</p>"}
    </section>`;
  const inWizard = location.pathname === "/create/article" || location.pathname === "/create/cowrite";
  const wizardBase = articleWizardBase();
  function topicFields(id) {
    const article = view.querySelector(`article[data-id="${id}"]`);
    return {
      template: article.querySelector("[data-template]").value,
      page_count: Number(article.querySelector("[data-pages]").value),
      title: article.querySelector("[data-title]").value,
      error: article.querySelector("[data-topic-error]"),
    };
  }
  view.querySelectorAll("[data-select]").forEach((button) => {
    button.onclick = async () => {
      await api("POST", `/api/xhs/topics/${button.dataset.select}/select`);
      render();
    };
  });
  view.querySelectorAll("[data-reject]").forEach((button) => {
    button.onclick = async () => {
      await api("POST", `/api/xhs/topics/${button.dataset.reject}/reject`);
      render();
    };
  });
  view.querySelectorAll("[data-rename]").forEach((button) => {
    button.onclick = async () => {
      const fields = topicFields(button.dataset.rename);
      await api("PUT", `/api/xhs/topics/${button.dataset.rename}`, { title: fields.title });
      render();
    };
  });
  view.querySelectorAll("[data-plan]").forEach((button) => {
    button.onclick = async () => {
      const fields = topicFields(button.dataset.plan);
      await api("POST", `/api/xhs/topics/${button.dataset.plan}/plan`, { template: fields.template, page_count: fields.page_count });
      render();
    };
  });
  view.querySelectorAll("[data-draft]").forEach((button) => {
    button.onclick = async () => {
      const fields = topicFields(button.dataset.draft);
      try {
        const { data: note } = await api("POST", `/api/xhs/topics/${button.dataset.draft}/draft`, { template: fields.template, page_count: fields.page_count });
        sessionStorage.setItem("article-note-id", note.id);
        go(inWizard ? `${wizardBase}?step=2` : "/notes/" + note.id);
      } catch (error) {
        fields.error.textContent = error.message;
      }
    };
  });
}

function reportBlock(report) {
  if (!report || !(report.facts || []).length) return "";
  const line = (title, items) => `<p><strong>${title}</strong> ${escapeHtml((items || []).join(" "))}</p>`;
  return `<section class="card">${line("事实", report.facts)}${line("知识库", report.knowledge)}${line("判断", [report.judgment || ""])}</section>`;
}

async function renderNote(id, options) {
  const opts = options || {};
  const { data: note } = await api("GET", `/api/xhs/notes/${id}`);
  const quickDraft = !opts.embedded && articleCreateMode() === "quick";
  const head = opts.embedded
    ? ""
    : quickDraft
      ? `<header class="page-head draft-edit-head">
      <p class="eyebrow">// Draft</p>
      <h1>草稿改稿</h1>
      <p class="lede">${escapeHtml(note.title)} · 版本 ${note.version} · ${note.publish_status}</p>
      <p class="draft-edit-nav">
        <a data-nav href="/library/drafts">← 草稿箱</a>
        <a data-nav href="/create/article">再写一篇</a>
        <a data-nav href="/create/visual">配图</a>
        <a data-nav href="/library/works">成品库</a>
      </p>
    </header>`
      : `<header class="page-head">
      <p class="eyebrow">// Note</p>
      <h1>${escapeHtml(note.title)}</h1>
      <p class="lede">版本 ${note.version} · ${note.publish_status}${note.error ? " · " + note.error : ""}</p>
    </header>`;
  const stepHint = opts.embedded
    ? opts.step === 3
      ? "<p class='lede'>这一步改口吻。保存会升级版本并清除原确认。</p>"
      : opts.step === 4
        ? "<p class='lede'>点「生成封面并检查」出图。重新出图会使原确认失效。</p>"
        : opts.step === 5
          ? "<p class='lede'>勾选七项后点「提交确认」进入发布步。</p>"
          : ""
    : quickDraft
      ? "<p class='lede'>一键成文：改完分页后保存；可生成封面、勾选七项后提交确认。</p>"
      : "";
  view.innerHTML = `${head}${stepHint}
    <section class="card">
      ${note.direction && note.direction.concept ? `<p class="lede">${escapeHtml(note.direction.concept)}。${escapeHtml(note.direction.layout || "")}</p>` : ""}
      <form id="note">
        <label>标题</label><input name="title" value="${escapeHtml(note.title)}" />
        <label>摘要</label><textarea name="summary">${escapeHtml(note.summary || "")}</textarea>
        <label>标签</label><input name="tags" value="${escapeHtml((note.tags || []).join(" "))}" />
        <div class="pages" id="pages">
          ${(note.pages || []).map((page, index) => `
            <label class="page-card">
              <small>第 ${page.index || index + 1} 页 · ${escapeHtml(page.message || page.role || "")}</small>
              <textarea name="page">${escapeHtml(page.text || "")}</textarea>
              ${page.image ? `<object data="/files/${escapeHtml(page.image)}" type="image/svg+xml"></object>` : ""}
            </label>`).join("")}
        </div>
        <div class="row">
          <button type="submit">保存并升级版本</button>
          <button class="ghost" type="button" id="visual">生成封面并检查</button>
          <button class="ghost" type="button" id="submit">提交确认</button>
        </div>
      </form>
      <div class="review-list" id="review">
        ${REVIEW_ITEMS.map(([key, label]) => `<label><input type="checkbox" name="${key}" />${label}</label>`).join("")}
      </div>
      <p id="checks" class="lede">${escapeHtml(sessionStorage.getItem("note-checks-" + id) || "")}</p>
    </section>`;
  document.querySelector("#note").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.target);
    const texts = form.getAll("page");
    const pages = (note.pages || []).map((page, index) => ({ ...page, text: texts[index] }));
    const tags = String(form.get("tags") || "").split(/[\s,，]+/).filter(Boolean);
    await api("PUT", `/api/xhs/notes/${id}`, { title: form.get("title"), summary: form.get("summary"), tags, pages });
    render();
  });
  document.querySelector("#visual").onclick = async () => {
    const { data: visual } = await api("POST", `/api/xhs/notes/${id}/visual`);
    const text = (visual.checks || []).map((item) => `${item.item}：${item.issue}`).join("；") || "版面检查没有超出项";
    sessionStorage.setItem("note-checks-" + id, text);
    render();
  };
  document.querySelector("#submit").onclick = async () => {
    const checks = {};
    REVIEW_ITEMS.forEach(([key]) => {
      checks[key] = document.querySelector(`#review [name="${key}"]`).checked;
    });
    try {
      await api("POST", `/api/xhs/notes/${id}/submit`, { checks });
      const base = articleWizardBase();
      if (articleCreateMode() === "quick" && base === "/create/article") {
        go("/create/article?step=6");
      } else {
        go(`${base}?step=6${base === "/create/cowrite" ? cowriteWorkflowQuery() : ""}`);
      }
    } catch (error) {
      document.querySelector("#checks").textContent = error.message;
    }
  };
}

async function renderPublish(embedded) {
  const { data } = await api("GET", "/api/xhs/notes");
  const notes = (data.notes || []).filter((note) => ["WAITING_APPROVAL", "PUBLISHING", "PUBLISHED", "FAILED", "REJECTED"].includes(note.publish_status));
  const head = embedded
    ? ""
    : `<header class="page-head">
      <p class="eyebrow">// Publish</p>
      <h1>确认与发布</h1>
      <p class="lede">确认只覆盖这一篇的当前版本。本机没有配置小红书 MCP 时，发布会记为失败，不会假装已经发出。</p>
    </header>`;
  view.innerHTML = `${head}
    <section class="card">
      ${notes.map((note) => `
        <article>
          <h2>${escapeHtml(note.title)}</h2>
          <p>版本 ${note.version} ${tag(note.publish_status)}</p>
          ${note.review && note.review.facts ? `<p class="lede">这一版已勾选 ${REVIEW_ITEMS.filter(([key]) => note.review[key]).map(([, label]) => label).join("、")}</p>` : ""}
          ${(note.pages || []).map((page) => `<p class="lede">第 ${page.index} 页 ${escapeHtml(page.text || "")}</p>${page.image ? `<object data="/files/${escapeHtml(page.image)}" type="image/svg+xml"></object>` : ""}`).join("")}
          ${(note.publish_log || []).map((row) => `<p class="lede">${escapeHtml(row.created_at)} · 版本 ${row.version} · ${escapeHtml(row.status)} · ${escapeHtml(row.detail || "")}</p>`).join("")}
          ${note.error ? `<p class="error">${escapeHtml(note.error)}</p>` : ""}
          <div class="row">
            <button type="button" data-approve="${escapeHtml(note.id)}" data-version="${note.version}">确认这个版本</button>
            <button class="ghost" type="button" data-reject="${escapeHtml(note.id)}" data-version="${note.version}">退回</button>
            <button class="ghost" type="button" data-publish="${escapeHtml(note.id)}">发布</button>
          </div>
        </article>`).join("") || "<p>没有待确认的笔记。</p>"}
    </section>`;
  view.querySelectorAll("[data-approve]").forEach((button) => {
    button.onclick = async () => {
      await api("POST", "/api/xhs/approvals", { note_id: button.dataset.approve, version: Number(button.dataset.version), decision: "approve" });
      render();
    };
  });
  view.querySelectorAll("[data-reject]").forEach((button) => {
    button.onclick = async () => {
      await api("POST", "/api/xhs/approvals", { note_id: button.dataset.reject, version: Number(button.dataset.version), decision: "reject" });
      render();
    };
  });
  view.querySelectorAll("[data-publish]").forEach((button) => {
    button.onclick = async () => {
      await api("POST", `/api/xhs/notes/${button.dataset.publish}/publish`);
      render();
    };
  });
}

const QUICK_PREFS_KEY = "xhs-quick-article-prefs";
const DEFAULT_QUICK_PREFS = {
  persona: "自然写作",
  wordCount: 800,
  deai: "开启",
  coverRatio: "3:4",
  inlineImages: 2,
  imageRatio: "3:4",
  coverMode: "ai",
};

function loadQuickPrefs() {
  try {
    return { ...DEFAULT_QUICK_PREFS, ...JSON.parse(localStorage.getItem(QUICK_PREFS_KEY) || "{}") };
  } catch (error) {
    return { ...DEFAULT_QUICK_PREFS };
  }
}

function saveQuickPrefs(prefs) {
  localStorage.setItem(QUICK_PREFS_KEY, JSON.stringify(prefs));
}

function quickPrefsSummary(prefs) {
  const parts = [
    prefs.persona,
    `${prefs.wordCount}字`,
    prefs.deai === "开启" ? "去AI味" : "保留原文风",
    `${prefs.inlineImages}张配图`,
    `封面 ${prefs.coverRatio}`,
    prefs.coverMode === "ai" ? "AI封面" : "我的照片",
  ];
  return parts.join(" · ");
}

function openQuickSettingsDialog() {
  const prefs = loadQuickPrefs();
  let wrap = document.getElementById("quick-settings-dialog");
  if (!wrap) {
    wrap = document.createElement("div");
    wrap.id = "quick-settings-dialog";
    wrap.className = "quick-settings-dialog";
    document.body.appendChild(wrap);
  }
  wrap.classList.remove("hidden");
  wrap.innerHTML = `
    <div class="quick-settings-backdrop" data-quick-settings-close></div>
    <div class="quick-settings-sheet card">
      <header class="quick-settings-head">
        <h2>默认创作设置</h2>
        <button type="button" class="ghost quick-settings-x" data-quick-settings-close aria-label="关闭">×</button>
      </header>
      <p class="lede">保存一次，以后一键成文自动复用。</p>
      <form id="quick-settings-form" class="quick-settings-form">
        <label>写作人格<select name="persona"><option${prefs.persona === "自然写作" ? " selected" : ""}>自然写作</option><option${prefs.persona === "专业讲解" ? " selected" : ""}>专业讲解</option><option${prefs.persona === "闺蜜聊天" ? " selected" : ""}>闺蜜聊天</option></select></label>
        <label>目标字数<input name="wordCount" type="number" min="300" max="2000" step="100" value="${Number(prefs.wordCount) || 800}" /></label>
        <label>去 AI 味<select name="deai"><option${prefs.deai === "开启" ? " selected" : ""}>开启</option><option${prefs.deai === "关闭" ? " selected" : ""}>关闭</option></select></label>
        <label>封面比例<select name="coverRatio"><option${prefs.coverRatio === "3:4" ? " selected" : ""}>3:4</option><option${prefs.coverRatio === "1:1" ? " selected" : ""}>1:1</option><option${prefs.coverRatio === "4:5" ? " selected" : ""}>4:5</option></select></label>
        <label>文中配图数量<select name="inlineImages"><option value="0"${prefs.inlineImages === 0 ? " selected" : ""}>0 张</option><option value="1"${prefs.inlineImages === 1 ? " selected" : ""}>1 张</option><option value="2"${prefs.inlineImages === 2 ? " selected" : ""}>2 张</option><option value="3"${prefs.inlineImages === 3 ? " selected" : ""}>3 张</option></select></label>
        <label>配图比例<select name="imageRatio"><option${prefs.imageRatio === "3:4" ? " selected" : ""}>3:4</option><option${prefs.imageRatio === "1:1" ? " selected" : ""}>1:1</option><option${prefs.imageRatio === "4:3" ? " selected" : ""}>4:3</option></select></label>
      </form>
      <p class="lede quick-settings-note">排版由系统按小红书图文习惯自动选择。生成后可在第 2 步继续改稿。</p>
      <div class="quick-settings-actions">
        <button type="button" class="ghost" data-quick-settings-close>取消</button>
        <button type="button" class="primary" id="quick-settings-save">保存设置</button>
      </div>
    </div>`;
  wrap.querySelectorAll("[data-quick-settings-close]").forEach((el) => {
    el.onclick = () => wrap.classList.add("hidden");
  });
  document.getElementById("quick-settings-save").onclick = () => {
    const form = new FormData(document.getElementById("quick-settings-form"));
    const next = {
      ...loadQuickPrefs(),
      persona: String(form.get("persona") || "自然写作"),
      wordCount: Number(form.get("wordCount")) || 800,
      deai: String(form.get("deai") || "开启"),
      coverRatio: String(form.get("coverRatio") || "3:4"),
      inlineImages: Number(form.get("inlineImages")) || 0,
      imageRatio: String(form.get("imageRatio") || "3:4"),
    };
    saveQuickPrefs(next);
    wrap.classList.add("hidden");
    renderQuickArticle();
  };
}

function createWorkflowIdFromUrl() {
  return new URLSearchParams(location.search).get("workflow") || "";
}

function renderInspireGrid(lead) {
  const text = lead || "还没想好？从这里找选题";
  return `<div class="quick-inspire">
    <p class="quick-inspire-lead">${text}</p>
    <div class="quick-inspire-grid">
      <a class="quick-inspire-card" data-nav href="/hot/today"><strong>当日热点</strong><small>多平台当日热点</small></a>
      <a class="quick-inspire-card" data-nav href="/hot/news"><strong>新闻爆点</strong><small>资讯与爆点线索</small></a>
      <a class="quick-inspire-card" data-nav href="/library/ideas"><strong>灵感库</strong><small>已确认的方法与方向</small></a>
    </div>
  </div>`;
}

async function loadHotTopicForCreate(workflowId, draftKey) {
  let topicText = sessionStorage.getItem(draftKey) || "";
  let source = null;
  if (workflowId) {
    sessionStorage.setItem("quick-workflow-id", workflowId);
    try {
      const { data: wf } = await api("GET", `/api/xhs/workflows/${workflowId}`);
      const topics = wf.topics || [];
      if (topics[0] && !topicText) {
        topicText = String(topics[0].source?.title || topics[0].title || "").split("｜")[0].trim();
      }
      if (topics[0]?.source && (topics[0].source.title || topics[0].source.url)) {
        source = topics[0].source;
      } else if (wf.artifacts?.title) {
        if (!topicText) topicText = String(wf.artifacts.title).split("｜")[0].trim();
        if (!source) source = { title: wf.artifacts.title, url: "", platform: "小红书" };
      }
    } catch (error) {
      /* keep draft */
    }
  }
  return { topicText, source };
}

async function renderQuickArticle() {
  sessionStorage.setItem("article-create-mode", "quick");
  const params = new URLSearchParams(location.search);
  const workflowId = createWorkflowIdFromUrl();
  if (!workflowId) {
    sessionStorage.removeItem("quick-workflow-id");
    sessionStorage.removeItem("quick-topic-draft");
  }
  const prefs = loadQuickPrefs();
  let health = "检查中…";
  try {
    const { data: h } = await api("GET", "/api/xhs/health");
    health = h.ok ? "本机服务已连接" : "服务异常";
  } catch (error) {
    health = "连接失败，请确认已运行 redeploy";
  }
  const { topicText: loadedTopic, source } = await loadHotTopicForCreate(workflowId, "quick-topic-draft");
  let topicText = loadedTopic;
  if (!topicText) topicText = "";
  const topicLen = topicText.length;
  const sourceLabel = source?.platform ? hotPlatformLabel(hotRowPlatform({ platform: source.platform })) : "热点";
  const sourceTitle = source?.title ? escapeHtml(source.title) : "还没有绑定热点";
  const sourceUrl = source?.url ? escapeHtml(source.url) : "";
  const coverAi = prefs.coverMode !== "photo";
  view.innerHTML = `
    <header class="page-head quick-article-head">
      <div>
        <p class="eyebrow">// Quick</p>
        <h1>一键成文</h1>
        <p class="lede">选好题目，剩下的交给后台；成稿后可再走排版与发布步。</p>
      </div>
      <p class="quick-health" id="quick-health">${escapeHtml(health)}</p>
    </header>
    <section class="card quick-step-card">
      <p class="quick-step-num">01</p>
      <h2 class="quick-step-title">今天想写什么？</h2>
      <label class="quick-field-label">文章主题</label>
      <div class="quick-topic-wrap">
        <textarea id="quick-topic" maxlength="240" placeholder="输入想写的小红书选题，或沿用下方已选热点标题">${escapeHtml(topicText)}</textarea>
        <div class="quick-topic-meta">
          <span id="quick-topic-count">${topicLen} / 240</span>
          <button type="button" class="ghost" id="quick-topic-clear">清空</button>
        </div>
      </div>
      <motionstub></motionstub>
    </section>
    <section class="card quick-step-card">
      <p class="quick-step-num">02</p>
      <h2 class="quick-step-title">封面想怎么做？</h2>
      <div class="quick-cover-pick">
        <button type="button" class="quick-cover-opt${coverAi ? " on" : ""}" data-cover-mode="ai">
          <span class="quick-cover-radio" aria-hidden="true"></span>
          <span><strong>AI 自动生成</strong><small>按文章内容生成小红书封面</small></span>
        </button>
        <button type="button" class="quick-cover-opt${!coverAi ? " on" : ""}" data-cover-mode="photo">
          <span class="quick-cover-radio" aria-hidden="true"></span>
          <span><strong>使用我的照片</strong><small>保留人物特征，换场景和姿势（后续支持）</small></span>
        </button>
      </div>
      <p class="quick-prefs-lead">其他设置沿用上次保存的偏好</p>
      <div class="quick-prefs-bar">
        <span id="quick-prefs-summary">${escapeHtml(quickPrefsSummary(prefs))}</span>
        <button type="button" class="ghost" id="quick-open-settings">修改设置 ›</button>
      </div>
    </section>
    <footer class="quick-submit-bar card">
      <button type="button" class="primary quick-generate" id="quick-generate">生成草稿并进入改稿 →</button>
      <p id="quick-gen-msg" class="lede"></p>
    </footer>`;
  view.querySelector(".quick-step-card motionstub").outerHTML = `
    ${
      source
        ? `<div class="quick-source">
      <div class="quick-source-main">
        <span class="tag ok">已选择选题</span>
        <span class="tag ok">${escapeHtml(sourceLabel)}</span>
        <strong class="quick-source-title">${sourceTitle}</strong>
        ${sourceUrl ? `<a class="quick-source-link" href="${sourceUrl}" target="_blank" rel="noreferrer">查看原文</a>` : ""}
      </div>
      <a class="ghost quick-source-change" data-nav href="/hot/today">更换</a>
    </div>`
        : ""
    }
    ${renderInspireGrid()}`;
  const topicEl = document.getElementById("quick-topic");
  const countEl = document.getElementById("quick-topic-count");
  topicEl.addEventListener("input", () => {
    const n = topicEl.value.length;
    countEl.textContent = `${n} / 240`;
    sessionStorage.setItem("quick-topic-draft", topicEl.value);
  });
  document.getElementById("quick-topic-clear")?.addEventListener("click", () => {
    topicEl.value = "";
    countEl.textContent = "0 / 240";
    sessionStorage.removeItem("quick-topic-draft");
  });
  document.querySelectorAll("[data-cover-mode]").forEach((btn) => {
    btn.onclick = () => {
      const mode = btn.dataset.coverMode;
      const p = loadQuickPrefs();
      p.coverMode = mode;
      saveQuickPrefs(p);
      document.querySelectorAll(".quick-cover-opt").forEach((el) => el.classList.toggle("on", el.dataset.coverMode === mode));
      document.getElementById("quick-prefs-summary").textContent = quickPrefsSummary(p);
    };
  });
  document.getElementById("quick-open-settings")?.addEventListener("click", openQuickSettingsDialog);
  document.getElementById("quick-generate")?.addEventListener("click", () => runQuickGenerate(workflowId || sessionStorage.getItem("quick-workflow-id") || ""));
}

async function ensureQuickWorkflowId(topicText) {
  let workflowId = createWorkflowIdFromUrl() || sessionStorage.getItem("quick-workflow-id") || "";
  if (workflowId) {
    try {
      await api("GET", `/api/xhs/workflows/${workflowId}`);
      return workflowId;
    } catch (error) {
      workflowId = "";
    }
  }
  const { data: wf } = await api("POST", "/api/xhs/workflows/quick", { title: topicText });
  sessionStorage.setItem("quick-workflow-id", wf.id);
  return wf.id;
}

async function runQuickGenerate(workflowId) {
  const msg = document.getElementById("quick-gen-msg");
  const btn = document.getElementById("quick-generate");
  const topicText = (document.getElementById("quick-topic")?.value || "").trim();
  if (!topicText) {
    if (msg) msg.textContent = "请先填写文章主题。";
    return;
  }
  btn.disabled = true;
  btn.textContent = "生成中…";
  if (msg) msg.textContent = "正在调用模型与 xhs-content 技能生成草稿…";
  const prefs = loadQuickPrefs();
  const pageCount = prefs.wordCount >= 1000 ? 6 : prefs.wordCount >= 700 ? 5 : 4;
  const template = prefs.persona === "专业讲解" ? "知识科普" : prefs.persona === "闺蜜聊天" ? "经验分享" : "经验分享";
  sessionStorage.setItem("article-create-mode", "quick");
  try {
    const wfId = await ensureQuickWorkflowId(topicText);
    const { data: wf } = await api("GET", `/api/xhs/workflows/${wfId}`);
    let topics = wf.topics || [];
    if (!topics.length) throw new Error("没有可用选题，请从热点重新进入或刷新页面");
    let topic = topics.find((t) => (t.status || "") === "selected") || topics[0];
    await api("PUT", `/api/xhs/topics/${topic.id}`, { title: topicText });
    await api("POST", `/api/xhs/topics/${topic.id}/select`);
    await api("POST", `/api/xhs/topics/${topic.id}/plan`, { template, page_count: pageCount });
    const { data: note, engine } = await api("POST", `/api/xhs/topics/${topic.id}/draft`, {
      template,
      page_count: pageCount,
      use_llm: true,
      quick_prefs: prefs,
    });
    saveQuickPrefs(prefs);
    sessionStorage.setItem("article-note-id", note.id);
    sessionStorage.removeItem("quick-topic-draft");
    sessionStorage.removeItem("cowrite-max-step");
    if (msg) msg.textContent = engine ? `草稿已生成（${engine}）` : "草稿已生成";
    sessionStorage.setItem("article-create-mode", "quick");
    go(`/notes/${note.id}`);
  } catch (error) {
    if (msg) msg.textContent = error.message || String(error);
    btn.disabled = false;
    btn.textContent = "生成草稿并进入改稿 →";
  }
}

async function renderCowriteStep1() {
  const prefs = loadQuickPrefs();
  const workflowId = createWorkflowIdFromUrl();
  if (!workflowId) {
    sessionStorage.removeItem("quick-workflow-id");
    sessionStorage.removeItem("cowrite-topic-title");
    sessionStorage.removeItem("cowrite-topic-id");
  }
  let topics = [];
  if (workflowId) {
    sessionStorage.setItem("quick-workflow-id", workflowId);
    try {
      const { data: wf } = await api("GET", `/api/xhs/workflows/${workflowId}`);
      topics = wf.topics || [];
    } catch (error) {
      topics = [];
    }
  }
  const defaultTopic = topics[0] ? String(topics[0].source?.title || topics[0].title).split("｜")[0].trim() : "";
  const selectedTopicId = sessionStorage.getItem("cowrite-topic-id") || topics[0]?.id || "";
  view.innerHTML = `
    <section class="card cowrite-block">
      <h2>今天想写什么？</h2>
      <label class="quick-field-label">文章主题</label>
      <textarea id="cowrite-topic" maxlength="240" placeholder="输入选题标题，或从下方候选里选一条">${escapeHtml(sessionStorage.getItem("cowrite-topic-title") || defaultTopic)}</textarea>
      <div class="cowrite-form-grid">
        <label>写作人格
          <select id="cowrite-persona">
            <option value="自然写作"${prefs.persona === "自然写作" ? " selected" : ""}>自然写作</option>
            <option value="专业讲解"${prefs.persona === "专业讲解" ? " selected" : ""}>专业讲解</option>
            <option value="闺蜜聊天"${prefs.persona === "闺蜜聊天" ? " selected" : ""}>闺蜜聊天</option>
          </select>
        </label>
        <div class="cowrite-word-pick">
          <span class="quick-field-label">文章字数</span>
          <div class="cowrite-pills" role="group">
            ${[1200, 1800, 2500].map((n) => `<button type="button" class="pill${Number(prefs.wordCount) === n ? " active" : ""}" data-word-count="${n}">${n}</button>`).join("")}
          </div>
          <p class="lede">AI 会按目标字数 ±30 字成稿。</p>
        </div>
      </div>
      <label class="quick-field-label">写作补充要求</label>
      <textarea id="cowrite-extra" class="cowrite-extra" placeholder="可选：语气、禁忌词、必须提到的点">${escapeHtml(sessionStorage.getItem("cowrite-extra") || "")}</textarea>
      <button type="button" class="primary cowrite-start" id="cowrite-start">开始共创</button>
    </section>
    <section class="card cowrite-block">
      ${renderInspireGrid("没有选题？从真实数据源里找灵感")}
    </section>
    ${topics.length ? `<section class="card cowrite-block">
      <h3>候选选题（热点分析）</h3>
      <ul class="cowrite-topic-list">
        ${topics.slice(0, 8).map((t) => {
          const src = t.source || {};
          const on = t.id === selectedTopicId ? " cowrite-topic-on" : "";
          return `<li class="cowrite-topic-item${on}" data-topic-id="${escapeHtml(t.id)}">
            <p class="cowrite-topic-item-title">${escapeHtml((src.title || t.title || "").split("｜")[0])}</p>
            <p class="lede">${escapeHtml(t.fit || "")} · ${escapeHtml(t.fit_reason || "")}</p>
          </li>`;
        }).join("")}
      </ul>
    </section>` : `<p class="lede">还没有 workflow。请从<a data-nav href="/hot/today">当日热点</a>点「热点分析」进入。</p>`}
  `;
  let activeTopicId = selectedTopicId;
  view.querySelectorAll("[data-word-count]").forEach((btn) => {
    btn.onclick = () => {
      view.querySelectorAll("[data-word-count]").forEach((b) => b.classList.toggle("active", b === btn));
    };
  });
  view.querySelectorAll(".cowrite-topic-item").forEach((item) => {
    item.onclick = () => {
      activeTopicId = item.dataset.topicId;
      sessionStorage.setItem("cowrite-topic-id", activeTopicId);
      const t = topics.find((row) => row.id === activeTopicId);
      const title = t ? String(t.source?.title || t.title).split("｜")[0].trim() : "";
      document.getElementById("cowrite-topic").value = title;
      sessionStorage.setItem("cowrite-topic-title", title);
      view.querySelectorAll(".cowrite-topic-item").forEach((el) => el.classList.toggle("cowrite-topic-on", el.dataset.topicId === activeTopicId));
    };
  });
  document.getElementById("cowrite-start")?.addEventListener("click", async () => startCowriteFromStep1(workflowId, activeTopicId, topics));
}

async function startCowriteFromStep1(workflowId, topicId, topics) {
  const btn = document.getElementById("cowrite-start");
  const topicText = (document.getElementById("cowrite-topic")?.value || "").trim();
  if (!topicText) {
    alert("请填写文章主题");
    return;
  }
  if (!workflowId || !topicId) {
    alert("请先从热点进入，或点选一条候选选题");
    return;
  }
  const persona = document.getElementById("cowrite-persona")?.value || "自然写作";
  const wordCount = Number(view.querySelector("[data-word-count].active")?.dataset.wordCount || 1200);
  const extra = (document.getElementById("cowrite-extra")?.value || "").trim();
  sessionStorage.setItem("cowrite-topic-title", topicText);
  sessionStorage.setItem("cowrite-topic-id", topicId);
  sessionStorage.setItem("cowrite-extra", extra);
  saveQuickPrefs({ ...loadQuickPrefs(), persona, wordCount });
  const template = persona === "专业讲解" ? "知识科普" : "经验分享";
  const pageCount = wordCount >= 2000 ? 6 : wordCount >= 1500 ? 5 : 4;
  btn.disabled = true;
  btn.textContent = "准备中…";
  try {
    await api("PUT", `/api/xhs/topics/${topicId}`, { title: topicText });
    await api("POST", `/api/xhs/topics/${topicId}/select`);
    await api("POST", `/api/xhs/topics/${topicId}/plan`, { template, page_count: pageCount });
    const { data: note } = await api("POST", `/api/xhs/topics/${topicId}/draft`, { template, page_count: pageCount });
    sessionStorage.setItem("article-note-id", note.id);
    bumpCowriteMax(2);
    sessionStorage.setItem("article-create-mode", "collab");
    go(`/create/cowrite?step=2${cowriteWorkflowQuery()}`);
  } catch (error) {
    alert(error.message || String(error));
    btn.disabled = false;
    btn.textContent = "开始共创";
  }
}

async function renderCowriteStep2(noteId) {
  const title = sessionStorage.getItem("cowrite-topic-title") || "";
  view.innerHTML = `
    <section class="card cowrite-topic-banner">
      <p class="cowrite-banner-label">本次选题</p>
      <h2>${escapeHtml(title)}</h2>
    </section>
    <div id="cowrite-note-host" class="cowrite-note-host"></div>`;
  const host = document.getElementById("cowrite-note-host");
  const root = view;
  view = host;
  await renderNote(noteId, { embedded: true, step: 2 });
  view = root;
  const empty = !host.querySelector("#note");
  if (empty) {
    host.innerHTML = `<section class="card cowrite-ai-empty">
      <div class="cowrite-ai-head"><h2>AI 共创</h2><button type="button" class="ghost" disabled>手动编辑</button></div>
      <p class="lede">先定标题，再定大纲，最后落正文。每步你确认后再继续。</p>
      <button type="button" class="primary" id="cowrite-draft-again">开始创作</button>
    </section>`;
    document.getElementById("cowrite-draft-again")?.addEventListener("click", () => render());
  }
}

async function renderCowriteStepPlaceholder(step, noteId) {
  const hints = {
    3: { title: "去 AI 味", body: "保留观点，改表达。确认后再写正文。", action: "生成去 AI 味备选", btn: "cowrite-deai" },
    4: { title: "配图", body: "生成封面与文中配图。比例与风格可在下一步精调。", action: "生成封面图", btn: "cowrite-visual" },
    5: { title: "排版", body: "把图文排成更适合小红书阅读的版式。", action: "生成排版", btn: "cowrite-layout" },
  };
  const hint = hints[step];
  view.innerHTML = `
    <section class="card cowrite-placeholder">
      <header class="cowrite-ph-head">
        <div>
          <h2>${hint.title}</h2>
          <p class="lede">${hint.body}</p>
        </div>
        <button type="button" class="primary" id="${hint.btn}">${hint.action}</button>
      </header>
      <div id="cowrite-note-host" class="cowrite-note-host"></div>
    </section>`;
  document.getElementById(hint.btn)?.addEventListener("click", async () => {
    if (step === 4) await api("POST", `/api/xhs/notes/${noteId}/visual`);
    render();
  });
  const host = document.getElementById("cowrite-note-host");
  const root = view;
  view = host;
  await renderNote(noteId, { embedded: true, step });
  view = root;
}

async function renderCreateCowrite() {
  sessionStorage.setItem("article-create-mode", "collab");
  const step = Math.min(6, Math.max(1, Number(new URLSearchParams(location.search).get("step") || 1)));
  bumpCowriteMax(step);
  const assistant = await cowriteAssistantHtml(step);
  view.innerHTML = `
    <header class="page-head cowrite-head">
      <div>
        <p class="eyebrow">// Cowrite</p>
        <h1>协作成文</h1>
        <p class="lede">逐步共创小红书图文，作品会自动保存。创作时保持本页打开，关闭后也可继续。</p>
      </div>
    </header>
    ${wizardBarCowrite(step)}
    <div class="cowrite-layout">
      <div id="cowrite-panel" class="cowrite-panel"></div>
      ${assistant}
    </div>
    <footer class="cowrite-foot card">
      <div class="cowrite-foot-actions">
        ${step > 1 ? `<button type="button" class="ghost" id="cowrite-back">上一步</button>` : "<span></span>"}
        ${step < 6 ? `<button type="button" class="primary" id="cowrite-next">继续下一步 →</button>` : `<a class="primary cowrite-finish" data-nav href="/library/works">查看成品库</a>`}
      </div>
    </footer>`;
  wireWizard();
  wireCowriteFooter(step);
  const panel = document.getElementById("cowrite-panel");
  const root = view;
  view = panel;
  try {
    if (step === 1) await renderCowriteStep1();
    else {
      const noteId = sessionStorage.getItem("article-note-id");
      if (!noteId && step > 1) {
        panel.innerHTML = `<p class="lede">请先在「选题」点「开始共创」。</p><a data-nav href="/create/cowrite?step=1${cowriteWorkflowQuery()}">去选题</a>`;
      } else if (step === 2) await renderCowriteStep2(noteId);
      else if (step === 6) await renderCowriteStepPublish();
      else if (step >= 3 && step <= 5) await renderCowriteStepPlaceholder(step, noteId);
    }
  } finally {
    view = root;
  }
}

async function renderCowriteStepPublish() {
  view.innerHTML = `<section class="card cowrite-publish-wrap"><h2>最后检查，然后交付</h2><p class="lede">确认标题、配图与排版后发布。未配置 MCP 时会记录失败状态。</p><div id="cowrite-publish-host"></div></section>`;
  const host = document.getElementById("cowrite-publish-host");
  const root = view;
  view = host;
  await renderPublish(true);
  view = root;
}

const VISUAL_GEN_PREFS_KEY = "xhs-visual-gen-prefs";
const VISUAL_GEN_LAST_KEY = "xhs-visual-gen-last";
const VISUAL_GEN_TOPIC_DRAFT_KEY = "visual-gen-topic-draft";
const VISUAL_ASPECTS = [
  { id: "3:4", label: "竖版 3:4" },
  { id: "1:1", label: "方形 1:1" },
  { id: "4:3", label: "横版 4:3" },
  { id: "16:9", label: "宽屏 16:9" },
];
const VISUAL_STYLE_TAGS = ["写实摄影", "插画海报", "封面配图", "主体一致"];

function loadVisualGenPrefs() {
  try {
    return { ...{ aspect: "3:4", count: 1, prompt: "" }, ...JSON.parse(localStorage.getItem(VISUAL_GEN_PREFS_KEY) || "{}") };
  } catch (error) {
    return { aspect: "3:4", count: 1, prompt: "" };
  }
}

function saveVisualGenPrefs(prefs) {
  localStorage.setItem(VISUAL_GEN_PREFS_KEY, JSON.stringify(prefs));
}

function visualGenCreditCost(count) {
  return Math.max(1, Number(count) || 1) * 2;
}

function wireVisualGenForm(prefs, last) {
  const topicEl = document.getElementById("visual-gen-topic");
  const topicCountEl = document.getElementById("visual-gen-topic-count");
  const promptEl = document.getElementById("visual-gen-prompt");
  const countEl = document.getElementById("visual-gen-count");
  const aspectEl = document.getElementById("visual-gen-aspect");
  const creditEl = document.getElementById("visual-gen-credit");
  const refInput = document.getElementById("visual-gen-ref");
  const refPreview = document.getElementById("visual-gen-ref-preview");
  const refDrop = document.getElementById("visual-gen-ref-drop");
  const charCount = document.getElementById("visual-gen-char");

  topicEl?.addEventListener("input", () => {
    const n = topicEl.value.length;
    if (topicCountEl) topicCountEl.textContent = `${n} / 240`;
    sessionStorage.setItem(VISUAL_GEN_TOPIC_DRAFT_KEY, topicEl.value);
  });
  document.getElementById("visual-gen-topic-clear")?.addEventListener("click", () => {
    if (!topicEl) return;
    topicEl.value = "";
    if (topicCountEl) topicCountEl.textContent = "0 / 240";
    sessionStorage.removeItem(VISUAL_GEN_TOPIC_DRAFT_KEY);
  });

  function syncCredit() {
    const n = Number(countEl?.value || 1);
    if (creditEl) creditEl.textContent = `本次消耗 ${visualGenCreditCost(n)} 积分 · 失败逐张退还`;
  }

  function syncChar() {
    const len = (promptEl?.value || "").length;
    if (charCount) charCount.textContent = `${len} / 1000 字`;
  }

  promptEl?.addEventListener("input", () => {
    syncChar();
    saveVisualGenPrefs({ ...loadVisualGenPrefs(), prompt: promptEl.value });
  });
  countEl?.addEventListener("change", () => {
    syncCredit();
    saveVisualGenPrefs({ ...loadVisualGenPrefs(), count: Number(countEl.value) || 1 });
  });
  aspectEl?.addEventListener("change", () => {
    saveVisualGenPrefs({ ...loadVisualGenPrefs(), aspect: aspectEl.value });
  });
  syncChar();
  syncCredit();

  const refClearBtn = document.getElementById("visual-gen-ref-clear");

  function clearVisualGenRef() {
    sessionStorage.removeItem("visual-gen-ref-data");
    if (refInput) refInput.value = "";
    if (refPreview) refPreview.replaceChildren();
    refDrop?.classList.remove("has-image");
    refClearBtn?.classList.add("hidden");
  }

  function showVisualGenRef(dataUrl) {
    if (refPreview) {
      const img = document.createElement("img");
      img.src = dataUrl;
      img.alt = "参考图";
      refPreview.replaceChildren(img);
    }
    refDrop?.classList.add("has-image");
    refClearBtn?.classList.remove("hidden");
  }

  const storedRef = sessionStorage.getItem("visual-gen-ref-data");
  if (storedRef) {
    showVisualGenRef(storedRef);
  }

  refClearBtn?.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    clearVisualGenRef();
  });

  refDrop?.addEventListener("click", () => refInput?.click());
  refInput?.addEventListener("change", () => {
    const file = refInput.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      alert("参考图请小于 10MB");
      refInput.value = "";
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = String(reader.result || "");
      sessionStorage.setItem("visual-gen-ref-data", dataUrl);
      showVisualGenRef(dataUrl);
    };
    reader.readAsDataURL(file);
  });

  document.querySelectorAll("[data-visual-style]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tag = btn.dataset.visualStyle || "";
      const cur = promptEl.value.trim();
      promptEl.value = cur ? `${cur}，${tag}` : tag;
      syncChar();
      saveVisualGenPrefs({ ...loadVisualGenPrefs(), prompt: promptEl.value });
    });
  });

  document.getElementById("visual-gen-submit")?.addEventListener("click", async () => {
    const theme = (topicEl?.value || "").trim();
    let prompt = (promptEl?.value || "").trim();
    if (!theme && !prompt) {
      alert("请填写图片主题或画面提示词");
      topicEl?.focus();
      return;
    }
    const fullPrompt = theme && prompt ? `${theme}。${prompt}` : theme || prompt;
    const btn = document.getElementById("visual-gen-submit");
    const aspect = aspectEl?.value || "3:4";
    const count = Number(countEl?.value || 1);
    const ref = sessionStorage.getItem("visual-gen-ref-data") || "";
    btn.disabled = true;
    btn.textContent = "生成中…";
    try {
      const { data } = await api("POST", "/api/xhs/images/generate", { prompt: fullPrompt, theme: theme || null, aspect, count, reference: ref || null });
      sessionStorage.setItem(VISUAL_GEN_LAST_KEY, JSON.stringify(data));
      saveVisualGenPrefs({ ...loadVisualGenPrefs(), prompt, aspect, count });
      render();
    } catch (error) {
      alert(error.message || String(error));
      btn.disabled = false;
      btn.textContent = "生成图片 →";
    }
  });

  if (last?.images?.length) {
    /* results already in DOM from renderCreateVisual */
  }
}

function visualGenResultsHtml(last) {
  if (!last?.images?.length) return "";
  return `<section class="card visual-gen-results">
    <header class="visual-gen-results-head">
      <h2>生成结果</h2>
      <p class="lede">批次 ${escapeHtml(last.batch || "")} · 共 ${last.images.length} 张</p>
    </header>
    <div class="visual-gen-gallery">
      ${last.images.map((img) => `
        <figure class="visual-gen-figure">
          <object data="/files/${escapeHtml(img.path)}" type="image/svg+xml" aria-label="生成图 ${img.index}"></object>
          <figcaption><a href="/files/${escapeHtml(img.path)}" download>下载</a></figcaption>
        </figure>`).join("")}
    </div>
  </section>`;
}

async function renderCreateVisual() {
  const prefs = loadVisualGenPrefs();
  let last = null;
  try {
    last = JSON.parse(sessionStorage.getItem(VISUAL_GEN_LAST_KEY) || "null");
  } catch (error) {
    last = null;
  }
  const workflowId = createWorkflowIdFromUrl();
  if (!workflowId) {
    sessionStorage.removeItem("quick-workflow-id");
    sessionStorage.removeItem(VISUAL_GEN_TOPIC_DRAFT_KEY);
  }
  const { topicText, source } = await loadHotTopicForCreate(workflowId, VISUAL_GEN_TOPIC_DRAFT_KEY);
  const topicLen = topicText.length;
  const sourceLabel = source?.platform ? hotPlatformLabel(hotRowPlatform({ platform: source.platform })) : "热点";
  const sourceTitle = source?.title ? escapeHtml(String(source.title).split("｜")[0]) : "";
  const sourceUrl = source?.url ? escapeHtml(source.url) : "";
  const sourceBlock = sourceTitle
    ? `<div class="quick-source visual-gen-source">
        <div class="quick-source-main">
          <span class="tag ok">已选择选题</span>
          <span class="tag ok">${escapeHtml(sourceLabel)}</span>
          <strong class="quick-source-title">${sourceTitle}</strong>
          ${sourceUrl ? `<a class="quick-source-link" href="${sourceUrl}" target="_blank" rel="noreferrer">查看原文</a>` : ""}
        </div>
        <a class="ghost quick-source-change" data-nav href="/hot/today">更换</a>
      </div>`
    : "";
  const hasRef = !!sessionStorage.getItem("visual-gen-ref-data");
  view.innerHTML = `
    <header class="page-head visual-gen-head">
      <div>
        <p class="eyebrow">// Visual</p>
        <h1>一键生图</h1>
        <p class="lede">写清楚画面，交给模型。上传参考图可锁定同一个主体，多张图不再各画各的。一张 2 积分。</p>
      </div>
      <span class="visual-gen-mode-tag">提示词生图</span>
    </header>
    <section class="card visual-gen-form">
      <h2 class="visual-gen-step-title">今天要画什么？</h2>
      <label class="quick-field-label">图片主题</label>
      <div class="quick-topic-wrap">
        <textarea id="visual-gen-topic" maxlength="240" placeholder="输入配图主题，或沿用下方已选热点标题">${escapeHtml(topicText)}</textarea>
        <div class="quick-topic-meta">
          <span id="visual-gen-topic-count">${topicLen} / 240</span>
          <button type="button" class="ghost" id="visual-gen-topic-clear">清空</button>
        </div>
      </div>
      ${sourceBlock}
      <div class="visual-gen-ref-row">
        <div>
          <p class="visual-gen-label">参考图 <span class="visual-gen-opt">选填 · 锁主体</span></p>
        </div>
        <p class="lede visual-gen-ref-hint">上传后，多张图里是同一个物件</p>
        <button type="button" class="ghost visual-gen-ref-clear${hasRef ? "" : " hidden"}" id="visual-gen-ref-clear">清空参考图</button>
      </div>
      <div class="visual-gen-ref-wrap">
        <button type="button" class="visual-gen-ref-drop${hasRef ? " has-image" : ""}" id="visual-gen-ref-drop">
          <span class="visual-gen-ref-plus" aria-hidden="true">+</span>
          <span class="visual-gen-ref-txt">点这里上传参考图<br /><small>PNG / JPG / WebP，≤10MB</small></span>
          <span id="visual-gen-ref-preview" class="visual-gen-ref-preview"></span>
        </button>
        <input type="file" id="visual-gen-ref" accept="image/png,image/jpeg,image/webp" hidden />
      </div>
      <div class="visual-gen-prompt-head">
        <label class="visual-gen-label" for="visual-gen-prompt">画面提示词</label>
        <span id="visual-gen-char" class="visual-gen-char">0 / 1000 字</span>
      </div>
      <textarea id="visual-gen-prompt" maxlength="1000" rows="6" placeholder="小红书笔记配图风：奶油白底 + 手绘小贴纸，打工人在窗边捧咖啡，上方留白放标题；莫兰迪色系、柔光、轻微胶片颗粒，3:4 竖图，干净不抢戏，适合首图封面。">${escapeHtml(prefs.prompt || "")}</textarea>
      <footer class="visual-gen-toolbar">
        <label>画幅
          <select id="visual-gen-aspect">
            ${VISUAL_ASPECTS.map((a) => `<option value="${a.id}"${prefs.aspect === a.id ? " selected" : ""}>${a.label}</option>`).join("")}
          </select>
        </label>
        <label>张数
          <select id="visual-gen-count">
            ${[1, 2, 3, 4].map((n) => `<option value="${n}"${Number(prefs.count) === n ? " selected" : ""}>${n} 张</option>`).join("")}
          </select>
        </label>
        <p id="visual-gen-credit" class="visual-gen-credit lede">本次消耗 ${visualGenCreditCost(prefs.count)} 积分 · 失败逐张退还</p>
        <div class="visual-gen-submit-wrap">
          <button type="button" class="primary visual-gen-submit" id="visual-gen-submit">生成图片 →</button>
          <p class="lede visual-gen-submit-hint">提示词越具体，画面越贴近你想要的样子</p>
        </div>
      </footer>
    </section>
    ${renderInspireGrid("还没想好画什么？先去热点或灵感库找方向")}
    ${visualGenResultsHtml(last)}
    ${!last?.images?.length ? `<section class="card visual-gen-hero">
      <div class="visual-gen-hero-ico" aria-hidden="true">🖼</div>
      <h2>一句话，出一组图</h2>
      <p class="lede">把画面、风格、画幅写清楚，剩下的交给模型。传一张参考图，多张图里就是同一个物件。</p>
      <div class="visual-gen-tags">
        ${VISUAL_STYLE_TAGS.map((tag) => `<button type="button" class="pill" data-visual-style="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`).join("")}
      </div>
    </section>` : ""}`;
  wireVisualGenForm(prefs, last);
}

async function renderArticleWizard(variant) {
  const isCollab = variant === "collab";
  if (!isCollab) {
    sessionStorage.setItem("article-create-mode", "quick");
  }
  const title = isCollab ? "协作成文" : "一键成文";
  const eyebrow = isCollab ? "// Cowrite" : "// Quick";
  const step = Math.min(6, Math.max(1, Number(new URLSearchParams(location.search).get("step") || 1)));
  const extra = !isCollab && step === 1 ? "一键模式：选定后可尽快生成草稿，再按需修改。" : "";
  const lede = [ARTICLE_STEP_LEDE[step], extra].filter(Boolean).join(" ");
  const base = isCollab ? "/create/cowrite" : "/create/article";
  const modeBadge = isCollab
    ? ""
    : `<p class="quick-mode-badge"><span class="tag ok">一键成文</span><span class="lede">模型 + xhs-writer 等 Skill · 非协作逐步共创</span></p>`;
  const quickFoot =
    !isCollab && step >= 2 && step <= 5
      ? `<footer class="quick-wizard-foot card">
          <div class="quick-wizard-foot-actions">
            <button type="button" class="ghost" id="quick-wizard-back">← 重新选题</button>
            <button type="button" class="primary" id="quick-wizard-next">${step < 6 ? "进入下一步 →" : "去发布"}</button>
          </div>
        </footer>`
      : "";
  view.innerHTML = `
    <header class="page-head">
      <p class="eyebrow">${eyebrow}</p>
      <h1>${title}</h1>
      <p class="lede">${lede}</p>
      ${modeBadge}
    </header>
    ${wizardBar(step)}
    <div id="wizard-panel" class="wizard-panel"></div>
    ${quickFoot}`;
  wireWizard();
  if (!isCollab) {
    document.getElementById("quick-wizard-back")?.addEventListener("click", () => {
      const q = quickWorkflowQuery();
      go(q ? `/create/article?${q.slice(1)}` : "/create/article");
    });
    document.getElementById("quick-wizard-next")?.addEventListener("click", () => {
      go(`/create/article?step=${step + 1}${quickWorkflowQuery()}`);
    });
  }
  const panel = document.getElementById("wizard-panel");
  const root = view;
  view = panel;
  try {
    if (step === 1) await renderTopics(true);
    else if (step === 6) await renderPublish(true);
    else {
      const noteId = sessionStorage.getItem("article-note-id");
      if (!noteId) {
        panel.innerHTML = `<p class="lede">请先在第 1 步选定选题并生成草稿。</p><p><a data-nav href="${base}?step=1">去选题</a></p>`;
      } else {
        await renderNote(noteId, { embedded: true, step });
      }
    }
  } finally {
    view = root;
  }
}

async function renderCreateArticle() {
  sessionStorage.setItem("article-create-mode", "quick");
  const step = Number(new URLSearchParams(location.search).get("step") || 0);
  const noteId = sessionStorage.getItem("article-note-id");
  if (step >= 2 && step <= 5) {
    if (noteId) {
      go(`/notes/${noteId}`);
      return;
    }
    go("/library/drafts");
    return;
  }
  if (step === 6) {
    await renderPublish(false);
    return;
  }
  if (!createWorkflowIdFromUrl()) {
    sessionStorage.removeItem("quick-workflow-id");
    sessionStorage.removeItem("quick-topic-draft");
  }
  await renderQuickArticle();
}

const ASK_PREFS_KEY = "xhs-ask-prefs";
const ASK_SESSIONS_KEY = "xhs-ask-sessions-v1";
const ASK_ACTIVE_KEY = "xhs-ask-active-session";
const ASK_LOG_KEY = "xhs-ask-log";

let askSessionsCache = [];
let askActiveId = "";
let askRunning = false;

function loadAskPrefs() {
  try {
    return { useKnowledge: true, useWeb: false, mode: "general", ...JSON.parse(localStorage.getItem(ASK_PREFS_KEY) || "{}") };
  } catch (error) {
    return { useKnowledge: true, useWeb: false, mode: "general" };
  }
}

function saveAskPrefs(prefs) {
  localStorage.setItem(ASK_PREFS_KEY, JSON.stringify(prefs));
}

function askUid(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function newAskSession() {
  const now = new Date().toISOString();
  const id = askUid("xhs-chat");
  return { id, title: "新对话", messages: [], createdAt: now, updatedAt: now, agentSessionKey: id };
}

function titleFromAskPrompt(prompt) {
  const t = String(prompt || "")
    .trim()
    .replace(/\s+/g, " ");
  return t.length > 28 ? `${t.slice(0, 28)}…` : t || "新对话";
}

function migrateAskLogToSessions() {
  try {
    const log = JSON.parse(sessionStorage.getItem(ASK_LOG_KEY) || "[]");
    if (!Array.isArray(log) || !log.length) return [];
    const session = newAskSession();
    session.messages = log.map((item) => ({
      role: item.role === "user" ? "user" : "assistant",
      text: item.text || "",
      meta: item.meta || "",
      href: item.href || "",
    }));
    const firstUser = session.messages.find((m) => m.role === "user");
    if (firstUser) session.title = titleFromAskPrompt(firstUser.text);
    sessionStorage.removeItem(ASK_LOG_KEY);
    return [session];
  } catch (error) {
    return [];
  }
}

function loadAskSessions() {
  try {
    const raw = localStorage.getItem(ASK_SESSIONS_KEY);
    let rows = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(rows) || !rows.length) rows = migrateAskLogToSessions();
    return rows
      .filter((s) => s && s.id)
      .map((s) => ({
        id: s.id,
        title: s.title || "新对话",
        messages: Array.isArray(s.messages) ? s.messages : [],
        createdAt: s.createdAt || new Date().toISOString(),
        updatedAt: s.updatedAt || s.createdAt || new Date().toISOString(),
        agentSessionKey: s.agentSessionKey || s.id,
      }));
  } catch (error) {
    return migrateAskLogToSessions();
  }
}

function saveAskSessions(sessions) {
  localStorage.setItem(ASK_SESSIONS_KEY, JSON.stringify(sessions.slice(0, 40)));
}

function getActiveAskSession() {
  return askSessionsCache.find((s) => s.id === askActiveId) || null;
}

function touchAskSession(mutator, bumpToTop) {
  const idx = askSessionsCache.findIndex((s) => s.id === askActiveId);
  if (idx < 0) return;
  const copy = {
    ...askSessionsCache[idx],
    messages: askSessionsCache[idx].messages.map((m) => ({ ...m })),
  };
  mutator(copy);
  copy.updatedAt = new Date().toISOString();
  const next = [...askSessionsCache];
  next[idx] = copy;
  if (bumpToTop && idx > 0) {
    next.splice(idx, 1);
    next.unshift(copy);
  }
  askSessionsCache = next;
  saveAskSessions(askSessionsCache);
}

function formatAskSessionTime(iso) {
  try {
    return new Date(iso).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    return "";
  }
}

function formatAskMeta(turn) {
  const bits = [];
  if (turn.engine) bits.push(`引擎 ${turn.engine}`);
  if (turn.use_knowledge === false) bits.push("未查知识库");
  else if ((turn.events || []).includes("mcp__knowledge__search")) bits.push("知识库");
  if (turn.use_web || (turn.events || []).includes("mcp__web_search__search")) bits.push("联网");
  if (turn.mode === "xhs_soft") bits.push("小红书软文");
  const sources = (turn.sources || []).map((s) => s.path || s.title).filter(Boolean);
  if (sources.length) bits.push(`引用 ${sources.length} 条`);
  return bits.join(" · ");
}

function renderAskSessionList() {
  const list = document.getElementById("ask-session-list");
  if (!list) return;
  list.innerHTML = askSessionsCache
    .map(
      (s) => `<li class="ask-session-item${s.id === askActiveId ? " active" : ""}" data-ask-session="${escapeHtml(s.id)}">
        <div class="ask-session-title">${escapeHtml(s.title || "新对话")}</div>
        <div class="ask-session-meta">${escapeHtml(formatAskSessionTime(s.updatedAt))}</div>
        <button type="button" class="ask-session-del" data-ask-delete="${escapeHtml(s.id)}" title="删除" aria-label="删除会话">×</button>
      </li>`,
    )
    .join("");
}

function paintAskThread() {
  const active = getActiveAskSession();
  const log = active?.messages || [];
  const thread = document.getElementById("ask-thread");
  if (!thread) return;
  thread.innerHTML = log.length
    ? log
        .map((item, index) => {
          const meta = item.meta ? `<p class="lede ask-meta">${escapeHtml(item.meta)}</p>` : "";
          const href = item.href ? `<div><a data-nav href="${escapeHtml(item.href)}">打开相关步骤</a></div>` : "";
          const copy =
            item.role === "assistant" && item.text
              ? `<button type="button" class="ghost ask-copy" data-copy-idx="${index}">复制回答</button>`
              : "";
          const label = item.role === "user" ? "你" : "助手";
          return `<article class="bubble ${item.role}"><div class="ask-bubble-role">${label}</div>${escapeHtml(item.text || "")}${meta}${href}${copy}</article>`;
        })
        .join("")
    : `<div class="ask-empty">
        <h2>有什么想聊的？</h2>
        <p class="lede">可查运营书架、开联网补充，或选「生成小红书软文」按图文结构出要点。</p>
        <div class="chips ask-chips">
          <button type="button" class="ghost" data-ask-prompt="根据知识库里的选题方法，如何判断一个热点适不适合做小红书图文？">选题方法</button>
          <button type="button" class="ghost" data-ask-prompt="把「久坐腰痛」这类话题写成小红书软文的标题和分镜要点。">软文示例</button>
          <button type="button" class="ghost" data-ask-prompt="最近 AI 应用有哪些值得关注的方向？请结合联网信息简述，并标注待核实。">联网热点</button>
        </div>
      </div>`;
  thread.scrollTop = thread.scrollHeight;
  thread.querySelectorAll(".ask-copy").forEach((btn) => {
    btn.onclick = async () => {
      const row = log[Number(btn.dataset.copyIdx)];
      try {
        await navigator.clipboard.writeText(row?.text || "");
        const statusEl = document.getElementById("ask-status");
        if (statusEl) statusEl.textContent = "已复制到剪贴板";
      } catch (error) {
        const statusEl = document.getElementById("ask-status");
        if (statusEl) statusEl.textContent = "复制失败";
      }
    };
  });
  thread.querySelectorAll("[data-ask-prompt]").forEach((btn) => {
    btn.onclick = () => {
      const send = document.getElementById("ask-form")?.__sendAsk;
      if (typeof send === "function") send(btn.dataset.askPrompt || "");
    };
  });
}

async function renderToolAsk() {
  const prefs = loadAskPrefs();
  askSessionsCache = loadAskSessions();
  if (!askSessionsCache.length) {
    const created = newAskSession();
    askSessionsCache = [created];
    saveAskSessions(askSessionsCache);
  }
  askActiveId = localStorage.getItem(ASK_ACTIVE_KEY) || "";
  if (!askSessionsCache.some((s) => s.id === askActiveId)) {
    askActiveId = askSessionsCache[0].id;
  }
  localStorage.setItem(ASK_ACTIVE_KEY, askActiveId);
  askRunning = false;

  view.innerHTML = `
    <header class="page-head ask-head">
      <div>
        <p class="eyebrow">// Assistant</p>
        <h1>AI助手</h1>
        <p class="lede">多会话保存在本机浏览器；同一对话内多轮会问 agent-core（session_id）。回答需人工核实后再发布。</p>
      </div>
    </header>
    <div class="ask-layout card">
      <aside class="ask-sessions" aria-label="对话列表">
        <button type="button" class="primary ask-new-session" id="ask-new-session">新对话</button>
        <ul id="ask-session-list" class="ask-session-list"></ul>
      </aside>
      <div class="ask-main">
        <section class="ask-toolbar">
          <label class="ask-toggle"><input type="checkbox" id="ask-knowledge"${prefs.useKnowledge ? " checked" : ""} /> 查询知识库</label>
          <label class="ask-toggle"><input type="checkbox" id="ask-web"${prefs.useWeb ? " checked" : ""} /> 联网补充</label>
          <div class="ask-modes" role="group" aria-label="输出模式">
            <button type="button" class="pill ask-mode${prefs.mode === "general" ? " active" : ""}" data-ask-mode="general">通用</button>
            <button type="button" class="pill ask-mode${prefs.mode === "xhs_soft" ? " active" : ""}" data-ask-mode="xhs_soft">生成小红书软文</button>
          </div>
        </section>
        <section class="chat-card ask-card">
          <div class="thread ask-thread" id="ask-thread"></div>
          <form id="ask-form" class="composer">
            <textarea name="prompt" placeholder="输入问题，Enter 发送；Shift+Enter 换行" ${askRunning ? "disabled" : ""}></textarea>
            <button type="submit" id="ask-send" ${askRunning ? "disabled" : ""}>发送</button>
          </form>
          <p id="ask-status" class="lede ask-status"></p>
        </section>
      </div>
    </div>`;

  renderAskSessionList();
  paintAskThread();

  function readPrefsFromDom() {
    return {
      useKnowledge: !!document.getElementById("ask-knowledge")?.checked,
      useWeb: !!document.getElementById("ask-web")?.checked,
      mode: document.querySelector(".ask-mode.active")?.dataset.askMode || "general",
    };
  }

  function selectAskSession(id) {
    if (askRunning || id === askActiveId) return;
    askActiveId = id;
    localStorage.setItem(ASK_ACTIVE_KEY, askActiveId);
    const statusEl = document.getElementById("ask-status");
    if (statusEl) statusEl.textContent = "";
    renderAskSessionList();
    paintAskThread();
  }

  function deleteAskSession(id) {
    if (askRunning) return;
    askSessionsCache = askSessionsCache.filter((s) => s.id !== id);
    if (!askSessionsCache.length) {
      const created = newAskSession();
      askSessionsCache = [created];
      askActiveId = created.id;
    } else if (askActiveId === id) {
      askActiveId = askSessionsCache[0].id;
    }
    localStorage.setItem(ASK_ACTIVE_KEY, askActiveId);
    saveAskSessions(askSessionsCache);
    renderAskSessionList();
    paintAskThread();
  }

  function createAskSession() {
    if (askRunning) return;
    const created = newAskSession();
    askSessionsCache = [created, ...askSessionsCache];
    askActiveId = created.id;
    localStorage.setItem(ASK_ACTIVE_KEY, askActiveId);
    saveAskSessions(askSessionsCache);
    renderAskSessionList();
    paintAskThread();
    document.querySelector("#ask-form textarea")?.focus();
  }

  document.getElementById("ask-new-session")?.addEventListener("click", createAskSession);
  document.getElementById("ask-session-list")?.addEventListener("click", (event) => {
    const del = event.target.closest("[data-ask-delete]");
    if (del) {
      event.stopPropagation();
      deleteAskSession(del.dataset.askDelete || "");
      return;
    }
    const row = event.target.closest("[data-ask-session]");
    if (row) selectAskSession(row.dataset.askSession || "");
  });

  document.getElementById("ask-knowledge")?.addEventListener("change", () => saveAskPrefs(readPrefsFromDom()));
  document.getElementById("ask-web")?.addEventListener("change", () => saveAskPrefs(readPrefsFromDom()));
  document.querySelectorAll(".ask-mode").forEach((btn) => {
    btn.onclick = () => {
      document.querySelectorAll(".ask-mode").forEach((el) => el.classList.toggle("active", el === btn));
      saveAskPrefs(readPrefsFromDom());
    };
  });

  async function sendAsk(promptRaw) {
    const text = String(promptRaw || "").trim();
    if (!text || askRunning) return;
    const active = getActiveAskSession();
    if (!active) return;
    const prefsNow = readPrefsFromDom();
    saveAskPrefs(prefsNow);
    const statusEl = document.getElementById("ask-status");
    const sendBtn = document.getElementById("ask-send");
    const textarea = document.querySelector("#ask-form textarea");
    askRunning = true;
    if (sendBtn) sendBtn.disabled = true;
    if (textarea) textarea.disabled = true;

    const priorHistory = active.messages.map((m) => ({
      role: m.role,
      content: m.text || "",
    }));

    touchAskSession((s) => {
      if (!s.messages.length) s.title = titleFromAskPrompt(text);
      s.messages.push({ role: "user", text, meta: "", href: "" });
      s.messages.push({ role: "assistant", text: "正在整理…", meta: "", href: "" });
    }, true);
    renderAskSessionList();
    paintAskThread();
    if (statusEl) statusEl.textContent = "生成中…";
    try {
      const { data: turn, engine } = await api("POST", "/api/xhs/turns", {
        prompt: text,
        workflow_note: "",
        use_knowledge: prefsNow.useKnowledge,
        use_web: prefsNow.useWeb,
        mode: prefsNow.mode,
        session_id: active.agentSessionKey,
        history: priorHistory,
      });
      const meta = formatAskMeta({ ...turn, engine: engine || turn.engine });
      touchAskSession((s) => {
        const last = s.messages[s.messages.length - 1];
        if (last?.role === "assistant") {
          last.text = turn.answer || "";
          last.meta = meta;
          last.href = turn.href || "";
        }
      }, false);
      if (statusEl) statusEl.textContent = meta || "完成";
    } catch (error) {
      touchAskSession((s) => {
        const last = s.messages[s.messages.length - 1];
        if (last?.role === "assistant") last.text = error.message || String(error);
      }, false);
      if (statusEl) statusEl.textContent = "";
    }
    askRunning = false;
    if (sendBtn) sendBtn.disabled = false;
    if (textarea) textarea.disabled = false;
    paintAskThread();
  }

  const form = document.getElementById("ask-form");
  if (form) form.__sendAsk = sendAsk;
  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const prompt = new FormData(event.target).get("prompt");
    sendAsk(prompt);
    event.target.reset();
  });
  const textarea = document.querySelector("#ask-form textarea");
  textarea?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendAsk(event.target.value);
      event.target.value = "";
    }
  });
}

async function renderToolExtract() {
  probeMessage = "";
  view.innerHTML = `
    <header class="page-head"><p class="eyebrow">// Tools</p><h1>小红书内容提取</h1><p class="lede">搜索、详情、评论。采集器未启用时只记失败，不产生笔记。</p></header>
    <section class="card">
      <label>关键词或笔记链接</label><input id="keyword" placeholder="用于搜索、详情、评论" />
      <div class="row">
        <button class="ghost" id="probe-search" type="button">关键词搜索</button>
        <button class="ghost" id="probe-detail" type="button">笔记详情</button>
        <button class="ghost" id="probe-comments" type="button">评论</button>
      </div>
      <p id="probe" class="lede"></p>
      <p><a data-nav href="/hot/today">素材仍进热点池</a></p>
    </section>`;
  async function probe(body) {
    const { data: result } = await api("POST", "/api/xhs/collect", body);
    document.querySelector("#probe").textContent = `${result.status} · ${(result.error && result.error.code) || ""} · 条目 ${(result.items || []).length}`;
  }
  const keyword = () => document.querySelector("#keyword").value.trim();
  document.querySelector("#probe-search").onclick = () => probe({ capability: "search", keyword: keyword() });
  document.querySelector("#probe-detail").onclick = () => probe({ capability: "note_detail", note_url: keyword() });
  document.querySelector("#probe-comments").onclick = () => probe({ capability: "comments", note_url: keyword() });
}

async function renderToolDownload() {
  let deps = { ok: false, error: "加载中…" };
  let jobs = [];
  try {
    deps = await videoDownloadApi("GET", "/api/video-download/deps");
    const res = await videoDownloadApi("GET", "/api/video-download/jobs");
    jobs = res.jobs || [];
  } catch (error) {
    deps = { ok: false, error: error.message || String(error) };
  }
  const depsBadge = deps.ok
    ? `<span class="tag ok">yt-dlp ${escapeHtml(deps.yt_dlp_version || "就绪")}${deps.ffmpeg ? " · ffmpeg" : " · 缺 ffmpeg"}</span>`
    : `<span class="tag bad">引擎不可用</span>`;
  const activeCount = jobs.filter((j) => j.status === "queued" || j.status === "downloading").length;
  view.innerHTML = `
    <header class="page-head vdl-head">
      <div>
        <p class="eyebrow">// Tools</p>
        <h1>视频下载</h1>
        <p class="lede">粘贴公开视频链接即可下载（yt-dlp），文件落在本机 <code>data/xhs/videos/downloads/</code>，可在<a data-nav href="/library/videos">视频库</a>预览。</p>
      </div>
      <div class="vdl-badges">${depsBadge}${activeCount ? `<span class="tag wait">${activeCount} 进行中</span>` : ""}</div>
    </header>
    <section class="card vdl-form">
      <div class="vdl-input-row">
        <input id="vdl-url" type="url" placeholder="粘贴视频链接，如 B 站 / YouTube / 抖音…" />
        <button type="button" class="primary" id="vdl-download">下载</button>
        <button type="button" class="ghost" id="vdl-clipboard">剪贴板</button>
      </div>
      <div class="vdl-toggles">
        <label class="vdl-toggle"><input type="checkbox" id="vdl-auto-paste" checked /> 粘贴链接后自动下载</label>
        <label class="vdl-toggle"><input type="checkbox" id="vdl-audio-only" /> 仅音频 (mp3)</label>
      </div>
      <p id="vdl-notice" class="lede"></p>
      ${!deps.ok ? `<p class="error">引擎未就绪：执行 <code>pip install yt-dlp</code>，建议安装 ffmpeg，并重启 <code>python scripts/redeploy.py</code>。</p><p class="error">${escapeHtml(deps.error || "")}</p>` : ""}
      ${deps.ok && !deps.ffmpeg ? `<p class="lede vdl-warn">未检测到 ffmpeg，部分站点可能无法合并音视频。</p>` : ""}
    </section>
    <div class="vdl-queue-head">
      <h2>下载队列</h2>
      <button type="button" class="ghost" id="vdl-refresh">刷新</button>
    </div>
    <div id="vdl-queue-host"></div>
    <details class="card vdl-xhs-archive">
      <summary>小红书笔记归档（XHS-Downloader）</summary>
      <p class="lede">选定笔记链接，把图片/视频归档到 data/xhs/（需在 collectors 里启用 xhs_downloader）。</p>
      <label>笔记链接</label>
      <input id="note-url" placeholder="https://www.xiaohongshu.com/explore/…" />
      <div class="row"><button type="button" class="ghost" id="probe-archive">归档</button></div>
      <p id="probe" class="lede"></p>
    </details>`;

  function renderJobList(list) {
    const host = document.getElementById("vdl-queue-host");
    if (!host) return;
    if (!list.length) {
      host.innerHTML = `<section class="card vdl-empty"><p>还没有任务。复制一个视频链接，在本页 Ctrl+V 即可开始。</p></section>`;
      return;
    }
    host.innerHTML = `<div class="vdl-queue"></div>`;
    const queue = host.querySelector(".vdl-queue");
    queue.innerHTML = list
      .map((job) => {
        const st = job.status;
        const tagKind = st === "done" ? "ok" : st === "error" ? "bad" : st === "downloading" ? "wait" : "";
        const bar =
          st === "downloading" || st === "queued"
            ? `<div class="vdl-progress"><div class="vdl-progress-meta"><span>${Number(job.percent || 0).toFixed(1)}%${job.speed ? ` · ${escapeHtml(job.speed)}` : ""}${job.eta ? ` · ETA ${escapeHtml(job.eta)}` : ""}</span><span>${formatBytes(job.filesize)}</span></div><div class="vdl-progress-track"><div class="vdl-progress-bar" style="width:${Math.min(100, Math.max(2, job.percent || 0))}%"></div></div></div>`
            : "";
        const actions = [];
        if (st === "done") {
          actions.push(`<a class="primary" href="/api/video-download/jobs/${escapeHtml(job.id)}/file" download="${escapeHtml(job.filename || "video")}">保存</a>`);
        }
        if (st === "queued" || st === "downloading") {
          actions.push(`<button type="button" class="ghost" data-vdl-cancel="${escapeHtml(job.id)}">取消</button>`);
        }
        actions.push(`<button type="button" class="ghost" data-vdl-delete="${escapeHtml(job.id)}" data-vdl-rmfile="${st === "done" ? "1" : "0"}">删除</button>`);
        return `<article class="card vdl-job">
          <header class="vdl-job-head">
            <div>
              <span class="tag ${tagKind}">${escapeHtml(videoJobStatusLabel(st))}</span>
              ${job.audio_only ? `<span class="tag">音频</span>` : ""}
              <h3>${escapeHtml(job.title || job.url)}</h3>
              <a class="vdl-job-link" href="${escapeHtml(job.url)}" target="_blank" rel="noreferrer">${escapeHtml(job.url)}</a>
            </div>
            <div class="row">${actions.join("")}</div>
          </header>
          ${bar}
          ${st === "done" && job.filename ? `<p class="lede">${escapeHtml(job.filename)}${job.filesize ? ` · ${formatBytes(job.filesize)}` : ""}</p>` : ""}
          ${st === "error" && job.error ? `<p class="error">${escapeHtml(job.error)}</p>` : ""}
        </article>`;
      })
      .join("");
    queue.querySelectorAll("[data-vdl-cancel]").forEach((btn) => {
      btn.onclick = async () => {
        await videoDownloadApi("POST", `/api/video-download/jobs/${btn.dataset.vdlCancel}/cancel`);
        await refreshJobs();
      };
    });
    queue.querySelectorAll("[data-vdl-delete]").forEach((btn) => {
      btn.onclick = async () => {
        const q = btn.dataset.vdlRmfile === "1" ? "?remove_file=1" : "";
        await videoDownloadApi("DELETE", `/api/video-download/jobs/${btn.dataset.vdlDelete}${q}`);
        await refreshJobs();
      };
    });
  }

  renderJobList(jobs);

  async function refreshJobs() {
    try {
      const res = await videoDownloadApi("GET", "/api/video-download/jobs");
      jobs = res.jobs || [];
      renderJobList(jobs);
      const n = jobs.filter((j) => j.status === "queued" || j.status === "downloading").length;
      const badgeHost = view.querySelector(".vdl-badges");
      if (badgeHost) {
        const extra = badgeHost.querySelector(".tag.wait");
        if (n && !extra) badgeHost.insertAdjacentHTML("beforeend", `<span class="tag wait">${n} 进行中</span>`);
        else if (!n && extra) extra.remove();
        else if (extra) extra.textContent = `${n} 进行中`;
      }
    } catch (error) {
      document.getElementById("vdl-notice").textContent = error.message || String(error);
    }
  }

  videoDownloadPoll = setInterval(() => {
    if (jobs.some((j) => j.status === "queued" || j.status === "downloading")) refreshJobs();
  }, 1500);

  const urlInput = document.getElementById("vdl-url");
  const noticeEl = document.getElementById("vdl-notice");
  let lastPaste = "";
  let busy = false;

  async function enqueue(raw, source) {
    const link = extractVideoUrl(raw);
    if (!link) {
      noticeEl.textContent = "未识别到有效链接";
      return;
    }
    if (source !== "manual" && lastPaste === link) return;
    lastPaste = link;
    urlInput.value = link;
    const audioOnly = document.getElementById("vdl-audio-only")?.checked;
    busy = true;
    document.getElementById("vdl-download").disabled = true;
    noticeEl.textContent = source === "manual" ? "开始下载…" : "已捕获链接，开始下载…";
    try {
      await videoDownloadApi("POST", "/api/video-download/jobs", { url: link, audio_only: !!audioOnly });
      noticeEl.textContent = "已加入下载队列";
      await refreshJobs();
    } catch (error) {
      noticeEl.textContent = "";
      noticeEl.className = "error";
      noticeEl.textContent = error.message || String(error);
    } finally {
      busy = false;
      document.getElementById("vdl-download").disabled = false;
    }
  }

  document.getElementById("vdl-download").onclick = () => enqueue(urlInput.value, "manual");
  urlInput.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") enqueue(urlInput.value, "manual");
  });
  document.getElementById("vdl-clipboard").onclick = async () => {
    try {
      const text = await navigator.clipboard.readText();
      const link = extractVideoUrl(text);
      if (!link) {
        noticeEl.textContent = "剪贴板里没有链接";
        return;
      }
      if (document.getElementById("vdl-auto-paste")?.checked) await enqueue(link, "clipboard");
      else {
        urlInput.value = link;
        noticeEl.textContent = "已从剪贴板填入链接";
      }
    } catch (error) {
      noticeEl.textContent = "无法读取剪贴板，请直接 Ctrl+V";
    }
  };
  document.getElementById("vdl-refresh").onclick = () => refreshJobs();

  const onPaste = (ev) => {
    const text = ev.clipboardData?.getData("text") || "";
    const link = extractVideoUrl(text);
    if (!link) return;
    const target = ev.target;
    const inField = target && (target.id === "vdl-url" || target.id === "note-url");
    if (inField && target.id === "vdl-url") {
      if (document.getElementById("vdl-auto-paste")?.checked) {
        ev.preventDefault();
        enqueue(link, "paste");
      }
      return;
    }
    if (!inField && document.getElementById("vdl-auto-paste")?.checked) {
      ev.preventDefault();
      enqueue(link, "paste");
    } else if (!inField) {
      urlInput.value = link;
      noticeEl.textContent = "已粘贴链接，点击下载即可";
    }
  };
  window.__xhsVdlPaste = onPaste;
  window.addEventListener("paste", onPaste);

  document.getElementById("probe-archive")?.addEventListener("click", async () => {
    const note_url = document.getElementById("note-url")?.value.trim();
    const probe = document.getElementById("probe");
    try {
      const { data: result } = await api("POST", "/api/xhs/collect", { capability: "media_archive", note_url });
      probe.textContent = `${result.status} · ${(result.error && result.error.code) || ""}`;
    } catch (error) {
      probe.textContent = error.message || String(error);
    }
  });
}

async function renderToolMetrics() {
  const { data } = await api("GET", "/api/xhs/notes");
  const notes = data.notes || [];
  const top = await api("GET", "/api/xhs/metrics/top");
  view.innerHTML = `
    <header class="page-head"><p class="eyebrow">// Metrics</p><h1>数据跟踪</h1><p class="lede">只用本账号录入的指标，不用别人的爆款当结论。</p></header>
  <section class="card">
    <h2>收藏最高</h2>
    <ul>${(top.data.notes || []).map((row) => `<li>${escapeHtml(row.title)} · 收藏 ${row.collects}</li>`).join("") || "<li>还没有可排序的收藏数</li>"}</ul>
  </section>
  <section class="card">
    ${notes.map((note) => `<article><h2>${escapeHtml(note.title)}</h2>
      <form data-metric="${escapeHtml(note.id)}">
        <label>曝光</label><input name="exposure" />
        <label>阅读</label><input name="reads" />
        <label>点赞</label><input name="likes" />
        <label>收藏</label><input name="collects" />
        <label>评论</label><input name="comments" />
        <label>涨粉</label><input name="followers" placeholder="可空" />
        <button type="submit">录入</button>
      </form></article>`).join("") || "<p>还没有笔记。</p>"}
  </section>`;
  view.querySelectorAll("form[data-metric]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(form).entries());
      await api("POST", `/api/xhs/notes/${form.dataset.metric}/metrics`, payload);
      render();
    });
  });
}

async function renderLibraryDrafts() {
  const { data } = await api("GET", "/api/xhs/notes");
  const drafts = (data.notes || []).filter((note) => (note.publish_status || "DRAFT") === "DRAFT");
  view.innerHTML = `
    <header class="page-head">
      <p class="eyebrow">// Drafts</p>
      <h1>草稿</h1>
      <p class="lede">「创作 → 一键成文」产出的文案先进草稿箱；在此打开继续改稿，不走协作成文六步向导。</p>
    </header>
    <section class="card draft-library-actions">
      <a class="primary" data-nav href="/create/article">一键成文</a>
    </section>
    <section class="card">
      ${drafts.length ? drafts.map((note) => {
        const words = (note.pages || []).reduce((n, p) => n + String(p.text || "").length, 0);
        return `<article class="draft-library-item">
          <h2>${escapeHtml(note.title)}</h2>
          <p class="lede">版本 ${note.version} · 约 ${words} 字 · ${escapeHtml(note.updated_at || note.created_at || "")}</p>
          <a data-nav href="/notes/${escapeHtml(note.id)}" class="draft-open" data-draft-open="${escapeHtml(note.id)}">继续改稿</a>
        </article>`;
      }).join("") : "<p class='lede'>还没有草稿。<a data-nav href=\"/create/article\">去一键成文</a></p>"}
    </section>`;
  view.querySelectorAll("[data-draft-open]").forEach((link) => {
    link.addEventListener("click", () => {
      sessionStorage.setItem("article-create-mode", "quick");
      sessionStorage.setItem("article-note-id", link.dataset.draftOpen || "");
    });
  });
}

async function renderLibraryWorks() {
  const { data } = await api("GET", "/api/xhs/notes");
  const notes = data.notes || [];
  view.innerHTML = `
    <header class="page-head"><p class="eyebrow">// Library</p><h1>成品库</h1><p class="lede">本账号写过和待发布的笔记。</p></header>
    <section class="card">${notes.map((note) => `<article><h2>${escapeHtml(note.title)}</h2><p>${tag(note.publish_status)} 版本 ${note.version}</p><a data-nav href="/notes/${escapeHtml(note.id)}">打开</a></article>`).join("") || "<p>还没有笔记。</p>"}</section>`;
}

async function renderLibraryShelf() {
  await renderKnowledge({ title: "书架", shelf: true });
}

function formatBytes(size) {
  const n = Number(size) || 0;
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

async function renderLibraryVideos() {
  const { data } = await api("GET", "/api/xhs/library/videos");
  const videos = data.videos || [];
  view.innerHTML = `
    <header class="page-head">
      <p class="eyebrow">// Library</p>
      <h1>视频库</h1>
      <p class="lede">本机 <code>data/xhs/videos/downloads/</code>（yt-dlp）及笔记归档产生的视频。在<a data-nav href="/tools/download">视频下载</a>粘贴链接即可入库。</p>
    </header>
  <section class="card">
      ${videos.length ? `<p class="lede">共 ${videos.length} 个视频文件</p>
      <div class="video-library-grid">
        ${videos.map((row) => `
          <article class="video-library-card">
            <video class="video-library-player" controls preload="metadata" src="/files/${escapeHtml(row.path)}"></video>
            <h2>${escapeHtml(row.title)}</h2>
            <p class="lede video-library-meta">
              ${escapeHtml(row.name)} · ${formatBytes(row.size_bytes)}
              ${row.source === "archive" ? " · 笔记归档" : " · 本机目录"}
            </p>
            ${row.url ? `<a class="quick-source-link" href="${escapeHtml(row.url)}" target="_blank" rel="noreferrer">原笔记</a>` : ""}
            <div class="row">
              <a class="ghost" href="/files/${escapeHtml(row.path)}" download="${escapeHtml(row.name)}">下载</a>
            </div>
          </article>`).join("")}
      </div>` : `<p>还没有视频。请先在「工具 → 视频下载」归档笔记里的视频；下载器就绪后会写入本机目录。</p>
      <div class="row"><a data-nav class="primary" href="/tools/download">去视频下载</a></div>`}
    </section>`;
}

async function renderLibraryIdeas() {
  const { data } = await api("GET", "/api/xhs/knowledge/docs");
  const docs = data.docs || [];
  const methods = docs.filter((doc) => String(doc.path || "").includes("operation"));
  view.innerHTML = `
    <header class="page-head"><p class="eyebrow">// Library</p><h1>灵感库</h1><p class="lede">选题方法与已入库方法。待确认文稿在复盘里确认后才进书架。</p></header>
    <section class="card">${methods.map((doc) => `<article><h2>${escapeHtml(doc.title)}</h2><p class="lede">${escapeHtml(doc.path)}</p></article>`).join("") || "<p>还没有方法文档。</p>"}
      <p class="lede">五条固定做法见<a data-nav href="/library/ideas#methods">运营方法说明</a>。</p>
      <div id="methods">${renderMethodsHtml()}</div>
    </section>`;
}

function renderMethodsHtml() {
  const skills = [
    ["热点与素材", "只有状态正常的公开笔记和人工放入的材料能进入分析。"],
    ["适配分析", "定位未定时，结论是小规模实验。"],
    ["图文生产", "不把素材里的他人正文抄进待发布稿。"],
    ["视觉", "封面和版式分开做。"],
    ["审核与复盘", "确认只对当前版本有效。"],
  ];
  return skills.map(([title, text]) => `<p><strong>${title}</strong> ${text}</p>`).join("");
}

async function renderReviews() {
  const { data } = await api("GET", "/api/xhs/notes");
  const notes = data.notes || [];
  const top = await api("GET", "/api/xhs/metrics/top");
  view.innerHTML = `
    <header class="page-head">
      <p class="eyebrow">// Review</p>
      <h1>复盘</h1>
      <p class="lede">只用本账号这篇笔记的指标。复盘稿确认之后才能被检索。</p>
    </header>
    <div class="grid">
      <section class="card" id="list">
        ${notes.map((note) => `
          <article>
            <h2>${escapeHtml(note.title)}</h2>
            <p class="lede">${(note.metrics || []).length ? `最近收藏 ${note.metrics[0].collects ?? "空"}` : "还没有指标"}</p>
            <form data-metric="${escapeHtml(note.id)}">
              <label>曝光</label><input name="exposure" />
              <label>阅读</label><input name="reads" />
              <label>点赞</label><input name="likes" />
              <label>收藏</label><input name="collects" />
              <label>评论</label><input name="comments" />
              <label>涨粉</label><input name="followers" placeholder="可空" />
              <div class="row">
                <button type="submit">录入指标</button>
                <button class="ghost" type="button" data-review="${escapeHtml(note.id)}">写复盘稿</button>
                <button class="ghost" type="button" data-case="${escapeHtml(note.id)}">沉淀为案例</button>
                <button class="ghost" type="button" data-confirm="${escapeHtml(note.id)}">确认入库</button>
              </div>
            </form>
          </article>`).join("") || "<p>还没有笔记。</p>"}
      </section>
      <section class="card">
        <h2>收藏最高</h2>
        <div class="row"><button type="button" id="cycle">写周期报告</button><button class="ghost" type="button" id="confirm-last">确认刚才那份文稿</button></div>
        <ul>${(top.data.notes || []).map((row) => `<li>${escapeHtml(row.title)} · 收藏 ${row.collects}</li>`).join("") || "<li>还没有可排序的收藏数</li>"}</ul>
        <p id="confirmed" class="lede"></p>
      </section>
    </div>`;
  view.querySelectorAll("form[data-metric]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(form).entries());
      await api("POST", `/api/xhs/notes/${form.dataset.metric}/metrics`, payload);
      render();
    });
  });
  const confirmed = document.querySelector("#confirmed");
  view.querySelectorAll("[data-review]").forEach((button) => {
    button.onclick = async () => {
      try {
        const { data: review } = await api("POST", `/api/xhs/notes/${button.dataset.review}/review`);
        confirmed.textContent = `复盘稿已写成 ${review.path}，确认后才会进入检索。`;
        confirmed.dataset.path = review.path;
      } catch (error) {
        confirmed.textContent = error.message;
      }
    };
  });
  view.querySelectorAll("[data-case]").forEach((button) => {
    button.onclick = async () => {
      try {
        const { data: item } = await api("POST", `/api/xhs/notes/${button.dataset.case}/case`);
        confirmed.textContent = `案例已写成 ${item.path}，确认后才会进入检索。`;
        confirmed.dataset.path = item.path;
      } catch (error) {
        confirmed.textContent = error.message;
      }
    };
  });
  document.querySelector("#confirm-last").onclick = async () => {
    try {
      if (!confirmed.dataset.path) throw new Error("先写复盘、案例或周期报告");
      await api("POST", "/api/xhs/knowledge/confirm", { path: confirmed.dataset.path });
      confirmed.textContent = "已确认，下一轮提问可以检索到它。";
    } catch (error) {
      confirmed.textContent = error.message;
    }
  };
  document.querySelector("#cycle").onclick = async () => {
    try {
      const { data: item } = await api("POST", "/api/xhs/reviews/cycle");
      confirmed.textContent = `周期报告已写成 ${item.path}，确认后才会进入检索。`;
      confirmed.dataset.path = item.path;
    } catch (error) {
      confirmed.textContent = error.message;
    }
  };
  view.querySelectorAll("[data-confirm]").forEach((button) => {
    button.onclick = async () => {
      try {
        const remembered = confirmed.dataset.path || "";
        const pending = remembered.includes(button.dataset.confirm) ? remembered : `inbox/pending/review-${button.dataset.confirm}.md`;
        await api("POST", "/api/xhs/knowledge/confirm", { path: pending });
        confirmed.textContent = "已确认，下一轮提问可以检索到它。";
      } catch (error) {
        confirmed.textContent = error.message;
      }
    };
  });
}

async function renderKnowledge(options) {
  const opts = options || {};
  const { data } = await api("GET", "/api/xhs/knowledge/docs");
  const docs = data.docs || [];
  const title = opts.title || "知识库";
  const lede = opts.shelf
    ? "已确认的方法、策略与复盘。配置了 Embedding 并重建索引后按向量检索，否则按关键词。"
    : "只有已确认的文档会进入检索。配置了 Embedding 并重建索引后，用向量匹配；否则按关键词。";
  view.innerHTML = `
    <header class="page-head">
      <p class="eyebrow">// Knowledge</p>
      <h1>${title}</h1>
      <p class="lede">${lede}</p>
    </header>
    <div class="grid">
      <section class="card">
        <form id="doc">
          <label>标题</label><input name="title" required />
          <label>正文</label><textarea name="body" required placeholder="方法、案例或策略。确认后的复盘也会出现在列表里。"></textarea>
          <div class="row"><button type="submit">放入知识库</button><button class="ghost" type="button" id="reindex">重建向量索引</button></div>
        </form>
        <p id="doc-note" class="lede"></p>
        <label>试检索</label><input id="q" placeholder="输入问题" />
        <div class="row"><button class="ghost" type="button" id="search">检索</button></div>
        <div id="hits"></div>
      </section>
      <section class="card">
        ${docs.map((doc) => `<article><h2>${escapeHtml(doc.title)}</h2><p class="lede">${escapeHtml(doc.path)} · ${tag(doc.status)} · ${doc.chunks || 0} 段</p></article>`).join("") || "<p>还没有已入库的文档。</p>"}
      </section>
    </div>`;
  const note = document.querySelector("#doc-note");
  document.querySelector("#doc").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.target);
    try {
      const { data: result } = await api("POST", "/api/xhs/knowledge/documents", { title: form.get("title"), body: form.get("body") });
      note.textContent = result.embed_error ? `已入库。向量没有建成：${result.embed_error}` : `已入库，向量 ${result.embedded || 0} 段。`;
      render();
    } catch (error) {
      note.textContent = error.message;
    }
  });
  document.querySelector("#reindex").onclick = async () => {
    try {
      const { data: result } = await api("POST", "/api/xhs/knowledge/reindex");
      note.textContent = `已重建 ${result.embedded} 段。`;
      render();
    } catch (error) {
      note.textContent = error.message;
    }
  };
  document.querySelector("#search").onclick = async () => {
    const q = document.querySelector("#q").value.trim();
    const { data: result } = await api("GET", "/api/xhs/knowledge/retrieve?q=" + encodeURIComponent(q));
    const hits = result.sources || [];
    document.querySelector("#hits").innerHTML = hits.length
      ? hits.map((item) => `<article><h2>${escapeHtml(item.title)}</h2><p class="lede">${item.match === "embedding" ? "向量" : "关键词"} · ${escapeHtml(item.path)}</p><pre class="answer">${escapeHtml(item.excerpt || "")}</pre></article>`).join("")
      : "<p class='lede'>没有命中。</p>";
  };
}

const EMBED_PRESETS = [
  ["DashScope", "openai_compatible", "https://dashscope.aliyuncs.com/compatible-mode/v1", "text-embedding-v3", 1024],
  ["OpenAI", "openai_compatible", "https://api.openai.com/v1", "text-embedding-3-small", 1536],
  ["Ollama", "openai_compatible", "http://127.0.0.1:11434/v1", "nomic-embed-text", 768],
  ["Mock", "mock", "", "mock", 1536],
];
const LLM_PRESETS = [
  ["DashScope", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"],
  ["DeepSeek", "https://api.deepseek.com", "deepseek-chat"],
  ["OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"],
  ["Ollama", "http://127.0.0.1:11434/v1", "qwen2.5:7b"],
];
const AGENT_ENGINE_CORE = "agent-core";
const AGENT_ENGINE_CODEX = "codex";

function engineSelectable(routing, name) {
  if (name === AGENT_ENGINE_CORE) return true;
  const item = (routing?.engines || []).find((e) => e.name === name);
  return Boolean(item?.enabled && item?.available);
}

function describeAgentEngine(routing) {
  if (!routing || routing.offline) {
    return routing?.error || "agent-core 未就绪；请先运行 python scripts/redeploy.py";
  }
  const parts = (routing.engines || []).map((e) => {
    const tag = e.available ? "可用" : e.enabled ? "未就绪" : "未启用";
    return `${e.name}（${tag}）`;
  });
  return parts.join(" · ") || "已连接 agent-core";
}

async function renderSettings() {
  const embed = (await api("GET", "/api/xhs/settings/embedding")).data;
  const llm = (await api("GET", "/api/xhs/settings/llm")).data;
  const routing = (await api("GET", "/api/xhs/settings/agent-engine")).data;
  let engine = routing.default_engine || AGENT_ENGINE_CORE;
  if (engine === AGENT_ENGINE_CODEX && !engineSelectable(routing, AGENT_ENGINE_CODEX)) {
    engine = AGENT_ENGINE_CORE;
  }
  const codexDisabled = !engineSelectable(routing, AGENT_ENGINE_CODEX);
  let settingsTab = "agent";
  try {
    settingsTab = localStorage.getItem("xhs-settings-tab") || "agent";
  } catch (error) {
    settingsTab = "agent";
  }
  if (!["agent", "embed", "llm"].includes(settingsTab)) settingsTab = "agent";
  view.innerHTML = `
    <header class="page-head">
      <p class="eyebrow">// Models</p>
      <h1>模型配置</h1>
      <p class="lede">三个 Tab：智能体引擎、Embedding、对话模型。AI助手优先走 agent-core（Docker 宿主机默认 8082）；直连模型读下方对话配置。</p>
    </header>
    <p id="settings-note" class="lede"></p>
    <div class="settings-tabs ask-modes" role="tablist">
      <button type="button" class="pill${settingsTab === "agent" ? " active" : ""}" data-settings-tab="agent" role="tab">智能体引擎</button>
      <button type="button" class="pill${settingsTab === "embed" ? " active" : ""}" data-settings-tab="embed" role="tab">Embedding</button>
      <button type="button" class="pill${settingsTab === "llm" ? " active" : ""}" data-settings-tab="llm" role="tab">对话模型</button>
    </div>
    <section class="card settings-panel${settingsTab === "agent" ? "" : " hidden"}" id="settings-panel-agent">
      <h2>智能体引擎</h2>
      <p class="lede" id="agent-engine-status">${escapeHtml(describeAgentEngine(routing))}</p>
      <p class="lede">为 AI助手与运营对话（<code>xhs_ops</code>）指定默认执行引擎，与 AI-workspace 设置页一致。</p>
      <label class="engine-choice${engine === AGENT_ENGINE_CORE ? " is-on" : ""}">
        <input type="radio" name="agent-engine" value="${AGENT_ENGINE_CORE}" ${engine === AGENT_ENGINE_CORE ? "checked" : ""} />
        <span>
          <strong>内置 agent-core</strong>
          <small>自研本地引擎，使用上方「对话模型」配置</small>
        </span>
      </label>
      <label class="engine-choice${engine === AGENT_ENGINE_CODEX ? " is-on" : ""}${codexDisabled ? " is-disabled" : ""}">
        <input type="radio" name="agent-engine" value="${AGENT_ENGINE_CODEX}" ${engine === AGENT_ENGINE_CODEX ? "checked" : ""} ${codexDisabled ? "disabled" : ""} />
        <span>
          <strong>Codex</strong>
          <small>${codexDisabled ? "需 agent-core 中启用并配置 Codex 二进制" : "官方 Codex 二进制（推荐，若已配置）"}</small>
        </span>
      </label>
      <div class="row">
        <button type="button" id="engine-save" ${routing.offline ? "disabled" : ""}>保存引擎</button>
      </div>
    </section>
    <section class="card settings-panel${settingsTab === "embed" ? "" : " hidden"}" id="settings-panel-embed">
      <h2>Embedding</h2>
      <div class="row">${EMBED_PRESETS.map(([name]) => `<button class="ghost" type="button" data-embed-preset="${name}">${name}</button>`).join("")}</div>
      <label>提供方</label><select id="embed-provider"><option value="openai_compatible">openai_compatible</option><option value="mock">mock</option></select>
      <label>地址</label><input id="embed-base" placeholder="https://.../v1" value="${escapeHtml(embed.baseUrl || "")}" />
      <label>模型</label><input id="embed-model" value="${escapeHtml(embed.defaultModel || "")}" />
      <label>维度</label><input id="embed-dim" value="${escapeHtml(embed.dimension || 1536)}" />
      <label>密钥</label><input id="embed-key" type="password" value="${escapeHtml(embed.apiKey || "")}" placeholder="留空或掩码表示不改" />
      <div class="row"><button type="button" id="embed-save">保存 Embedding</button><button class="ghost" type="button" id="embed-test">连通测试</button></div>
    </section>
    <section class="card settings-panel${settingsTab === "llm" ? "" : " hidden"}" id="settings-panel-llm">
      <h2>对话模型</h2>
      <p class="lede">保存后请点「连接测试」。DeepSeek 常用模型名 <code>deepseek-chat</code>，地址示例 <code>https://api.deepseek.com</code>（服务会自动补 <code>/v1</code>）。</p>
      <div class="row">${LLM_PRESETS.map(([name]) => `<button class="ghost" type="button" data-llm-preset="${name}">${name}</button>`).join("")}</div>
      <label>地址</label><input id="llm-base" placeholder="https://.../v1" value="${escapeHtml(llm.baseUrl || "")}" />
      <label>模型</label><input id="llm-model" value="${escapeHtml(llm.model || "")}" />
      <label>温度</label><input id="llm-temp" value="${escapeHtml(llm.temperature || 0.3)}" />
      <label>密钥</label><input id="llm-key" type="password" value="${escapeHtml(llm.apiKey || "")}" placeholder="留空或掩码表示不改" />
      <div class="row"><button type="button" id="llm-save">保存模型</button><button class="ghost" type="button" id="llm-test">连通测试</button></div>
    </section>`;
  document.querySelector("#embed-provider").value = embed.provider || "openai_compatible";
  const note = document.querySelector("#settings-note");
  document.querySelectorAll("[data-settings-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      const tab = button.dataset.settingsTab;
      try {
        localStorage.setItem("xhs-settings-tab", tab);
      } catch (error) {
        /* ignore */
      }
      document.querySelectorAll("[data-settings-tab]").forEach((el) => {
        el.classList.toggle("active", el.dataset.settingsTab === tab);
      });
      document.querySelectorAll(".settings-panel").forEach((panel) => {
        panel.classList.toggle("hidden", !panel.id.endsWith(tab));
      });
    });
  });
  let selectedEngine = engine;
  document.querySelectorAll('input[name="agent-engine"]').forEach((input) => {
    input.addEventListener("change", () => {
      selectedEngine = input.value;
      document.querySelectorAll(".engine-choice").forEach((row) => {
        const radio = row.querySelector('input[type="radio"]');
        row.classList.toggle("is-on", radio && radio.checked);
      });
    });
  });
  document.querySelector("#engine-save")?.addEventListener("click", async () => {
    try {
      const { data: saved } = await api("PUT", "/api/xhs/settings/agent-engine", {
        default_engine: selectedEngine,
      });
      note.textContent = `默认引擎已设为 ${saved.default_engine || selectedEngine}（AI助手走 agent-core）。`;
      const status = document.querySelector("#agent-engine-status");
      if (status) status.textContent = describeAgentEngine(saved);
    } catch (error) {
      note.textContent = error.message;
    }
  });
  document.querySelectorAll("[data-embed-preset]").forEach((button) => {
    button.onclick = () => {
      const preset = EMBED_PRESETS.find((item) => item[0] === button.dataset.embedPreset);
      document.querySelector("#embed-provider").value = preset[1];
      document.querySelector("#embed-base").value = preset[2];
      document.querySelector("#embed-model").value = preset[3];
      document.querySelector("#embed-dim").value = preset[4];
    };
  });
  document.querySelectorAll("[data-llm-preset]").forEach((button) => {
    button.onclick = () => {
      const preset = LLM_PRESETS.find((item) => item[0] === button.dataset.llmPreset);
      document.querySelector("#llm-base").value = preset[1];
      document.querySelector("#llm-model").value = preset[2];
    };
  });
  document.querySelector("#embed-save").onclick = async () => {
    try {
      await api("PUT", "/api/xhs/settings/embedding", {
        provider: document.querySelector("#embed-provider").value,
        baseUrl: document.querySelector("#embed-base").value,
        defaultModel: document.querySelector("#embed-model").value,
        dimension: Number(document.querySelector("#embed-dim").value),
        apiKey: document.querySelector("#embed-key").value,
      });
      note.textContent = "Embedding 已保存。到知识库页重建索引后，检索才会改用向量。";
    } catch (error) {
      note.textContent = error.message;
    }
  };
  document.querySelector("#embed-test").onclick = async () => {
    try {
      const { data } = await api("POST", "/api/xhs/settings/embedding/test");
      note.textContent = `Embedding 可用，维度 ${data.dimension}。`;
    } catch (error) {
      note.textContent = error.message;
    }
  };
  document.querySelector("#llm-save").onclick = async () => {
    try {
      const { data: saved } = await api("PUT", "/api/xhs/settings/llm", {
        baseUrl: document.querySelector("#llm-base").value,
        model: document.querySelector("#llm-model").value,
        temperature: Number(document.querySelector("#llm-temp").value),
        apiKey: document.querySelector("#llm-key").value,
      });
      note.textContent = saved.deployEnvSyncWarn
        ? `对话模型已保存。${saved.deployEnvSyncWarn}`
        : saved.deployEnvSynced
          ? "对话模型已保存，并已同步到 deploy/.env。若用 Docker，请执行 python scripts/xhs.py start 或 docker compose up -d agent-core 使 agent-core 读新密钥。"
          : "对话模型已保存。";
    } catch (error) {
      note.textContent = error.message;
    }
  };
  document.querySelector("#llm-test").onclick = async () => {
    try {
      const { data } = await api("POST", "/api/xhs/settings/llm/test", {
        baseUrl: document.querySelector("#llm-base").value,
        model: document.querySelector("#llm-model").value,
        temperature: Number(document.querySelector("#llm-temp").value),
        apiKey: document.querySelector("#llm-key").value,
      });
      note.textContent = `模型有回复：${data.reply}`;
    } catch (error) {
      note.textContent = error.message;
    }
  };
}

async function renderSystem() {
  const health = await api("GET", "/health");
  const { data: sys } = await api("GET", "/api/xhs/system");
  const enabled = sys.collectors_enabled || [];
  view.innerHTML = `
    <header class="page-head">
      <p class="eyebrow">// System</p>
      <h1>系统设置</h1>
      <p class="lede">运行参数和配置文件位置。改账号或采集策略请编辑 YAML，重启服务后生效。</p>
    </header>
    <section class="card">
      <p>服务：${health.data && health.data.ok ? "正常" : "异常"}</p>
      <p>数据目录：${escapeHtml(sys.data_dir)}</p>
      <p>账号配置：${escapeHtml(sys.configs.account)}</p>
      <p>采集配置：${escapeHtml(sys.configs.collectors)}</p>
      <p>采集器：${enabled.length ? escapeHtml(enabled.join("、")) : "全部关闭"}（共 ${sys.collectors_total} 项）</p>
      <p>自动发布：${sys.auto_publish ? "开" : "关"}</p>
      <p>agent-core：${sys.agent_core ? `运行中，默认引擎 ${escapeHtml(sys.agent_engine_default || "agent-core")}` : "未连接（Docker 默认查 8082）"}</p>
      <p>小红书 MCP：${sys.xhs_mcp ? "已配置环境变量" : "未配置"}</p>
      <p id="system-note" class="lede"></p>
      <div class="row">
        <button type="button" id="reimport">重新扫描知识库目录</button>
      </div>
    </section>`;
  document.querySelector("#reimport").onclick = async () => {
    const note = document.querySelector("#system-note");
    try {
      const { data: result } = await api("POST", "/api/xhs/knowledge/import");
      note.textContent = `已扫描 ${result.imported} 篇，向量 ${result.embedded || 0} 段。${result.embed_error || ""}`;
    } catch (error) {
      note.textContent = error.message;
    }
  };
}

document.getElementById("login-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const err = document.getElementById("login-error");
  if (err) err.textContent = "";
  const fields = new FormData(form);
  const response = await fetch("/api/xhs/auth/login", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: String(fields.get("username") || "").trim(),
      password: String(fields.get("password") || ""),
    }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (err) err.textContent = data.error || "登录失败";
    return;
  }
  signedIn = true;
  hideLogin();
  render();
});

document.getElementById("logout-btn")?.addEventListener("click", async () => {
  await fetch("/api/xhs/auth/logout", { method: "POST", credentials: "same-origin" });
  signedIn = false;
  const viewEl = document.querySelector("#view");
  if (viewEl) viewEl.innerHTML = "";
  showLogin("");
});

render();
