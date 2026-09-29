/* AEOS 架构全景 · 修复版交互脚本（无 CDN 依赖） */
(function () {
  "use strict";

  const DIAGRAMS = {
    full: {
      title: "完整架构（原生直驱模型）",
      desc: "Trade AI / GoodJob 为本项目能力域，Hermes 进程内直驱；无外挂桥。黄/红仍表示通道侧偏弱项。",
      svg: buildFullSvg()
    },
    simplified: {
      title: "简化分层视图",
      desc: "从接入到存储的主数据流，突出控制面与执行面。",
      svg: buildSimplifiedSvg()
    },
    component: {
      title: "组件详解",
      desc: "前端 / 控制面 / 编排 / 资产 / 存储的组件级拆解。",
      svg: buildComponentSvg()
    },
    trade: {
      title: "外贸 7 步履约闭环",
      desc: "拓客⑤ / CRM⑥ 已并入优丁能力域，Hermes 原生直驱；WhatsApp 仅为可选通道，入站事件仍偏弱。",
      svg: buildTradeSvg()
    },
    orchestration: {
      title: "编排层架构（原生直驱）",
      desc: "Hermes 调度主权 → 契约插槽 → 进程内 native_acquisition / native_fulfillment，无外挂 HTTP 桥。",
      svg: buildOrchestrationSvg()
    },
    dataflow: {
      title: "数据流与修复闭环",
      desc: "绿=本项目能力域原生路径 + 本轮已补齐的入站总线/证据分析；无代码级架构断点。",
      svg: buildDataFlowSvg()
    }
  };

  const problemFilterMap = {
    all: () => true,
    fixed: (el) => el.dataset.status === "fixed",
    partial: (el) => el.dataset.status === "partial",
    open: (el) => el.dataset.status === "open",
    p0: (el) => el.dataset.priority === "p0",
    p1: (el) => el.dataset.priority === "p1",
    p2: (el) => el.dataset.priority === "p2"
  };

  function esc(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function node(x, y, w, h, label, sub, fill, stroke) {
    const lines = [];
    if (label) lines.push(label);
    if (sub) {
      if (Array.isArray(sub)) sub.forEach((s) => lines.push(s));
      else lines.push(sub);
    }
    const startY = y + h / 2 - ((lines.length - 1) * 8);
    const text = lines.map((line, i) =>
      `<text x="${x + w / 2}" y="${startY + i * 15}" text-anchor="middle" dominant-baseline="central" fill="#F4F2EC" font-size="${i === 0 ? 12 : 10}" font-weight="${i === 0 ? 600 : 400}">${esc(line)}</text>`
    ).join("");
    return `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="8" fill="${fill}" stroke="${stroke}" stroke-width="1.2"/>${text}</g>`;
  }

  function cluster(x, y, w, h, title) {
    return `<g>
      <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="rgba(74,155,140,0.06)" stroke="rgba(74,155,140,0.35)" stroke-width="1" stroke-dasharray="4 4"/>
      <text x="${x + 14}" y="${y + 20}" fill="#4A9B8C" font-size="12" font-weight="700">${esc(title)}</text>
    </g>`;
  }

  function arrow(x1, y1, x2, y2, color, dashed, label) {
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;
    const dash = dashed ? ' stroke-dasharray="5 4"' : "";
    const labelSvg = label
      ? `<text x="${midX}" y="${midY - 6}" text-anchor="middle" fill="${color}" font-size="9">${esc(label)}</text>`
      : "";
    return `<g>
      <path d="M ${x1} ${y1} L ${x2} ${y2}" fill="none" stroke="${color}" stroke-width="1.4"${dash} marker-end="url(#arrow-${color.replace('#','')})"/>
      ${labelSvg}
    </g>`;
  }

  function markers(colors) {
    return `<defs>${colors.map((c) => `
      <marker id="arrow-${c.replace('#','')}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="${c}"/>
      </marker>`).join("")}</defs>`;
  }

  function wrapSvg(inner, width, height) {
    return `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AEOS 架构图" font-family="Segoe UI, PingFang SC, Microsoft YaHei, sans-serif">
      <rect width="${width}" height="${height}" fill="#10192A"/>
      ${markers(["#4A9B8C", "#2F9E6B", "#D18B2F", "#D4554A", "#3D7EA6"])}
      ${inner}
    </svg>`;
  }

  function buildFullSvg() {
    const colors = {
      mintFill: "#245e54",
      okFill: "#245c43",
      warnFill: "#6b4d22",
      gapFill: "#6b2e2a",
      infoFill: "#1f4560",
      mintStroke: "#4A9B8C",
      okStroke: "#6FCF97",
      warnStroke: "#E0B15C",
      gapStroke: "#F08A80",
      infoStroke: "#7EB6D8"
    };

    let g = "";
    // Row 1 access
    g += cluster(20, 20, 1240, 92, "用户接入层");
    g += node(40, 42, 280, 52, "官网 :3000", "Vite 运行源 · 暖米白/砖橙", colors.mintFill, colors.mintStroke);
    g += node(340, 42, 280, 52, "超管后台 :5174", "Nuxt3 · 薄荷绿 #4A9B8C", colors.mintFill, colors.mintStroke);
    g += node(640, 42, 280, 52, "SEO管理 :5173", "独立 Node 管理系统", colors.mintFill, colors.mintStroke);
    g += node(940, 42, 280, 52, "负载/路由/统一登录", "TenantMiddleware · JWT 同步", colors.mintFill, colors.mintStroke);

    // Row 2 control plane
    g += cluster(20, 130, 600, 150, "核心控制面 backend:8001");
    g += node(40, 158, 270, 48, "FastAPI 主服务", "uvicorn · run.py", colors.mintFill, colors.mintStroke);
    g += node(330, 158, 270, 48, "中间件链", "CORS / Session / OTel / 租户", colors.mintFill, colors.mintStroke);
    g += node(40, 218, 270, 48, "路由自动发现", "150 模块 · 1207+ 端点", colors.mintFill, colors.mintStroke);
    g += node(330, 218, 270, 48, "服务/模型层", "42 子系统 · 93 ORM · 229 表", colors.mintFill, colors.mintStroke);

    g += cluster(640, 130, 620, 150, "AEOS 核心编排层");
    g += node(660, 158, 280, 48, "DeepSeek Harness", "Cordis JSON-RPC · 认知沙箱", colors.mintFill, colors.mintStroke);
    g += node(960, 158, 280, 48, "Hermes Control Plane", "DAG Supervisor · JsonPath · Saga", colors.infoFill, colors.infoStroke);
    g += node(660, 218, 280, 48, "DAG Governor", "DFS/Kahn · 100 节点上限", colors.warnFill, colors.warnStroke);
    g += node(960, 218, 280, 48, "ExecutorRegistry", "已注册 37+ 执行器", colors.okFill, colors.okStroke);

    // Row 3 executors
    g += cluster(20, 300, 1240, 120, "本项目能力域 · Hermes 原生直驱（无外挂桥）");
    g += node(40, 328, 280, 72, "本项目拓客 ⑤", ["trade_ai_agent 契约插槽", "native_acquisition · 无外桥"], colors.okFill, colors.okStroke);
    g += node(340, 328, 280, 72, "DeerFlow", ["研报/内容/SEO 发布", "content_publish 已挂接"], colors.okFill, colors.okStroke);
    g += node(640, 328, 280, 72, "本项目 CRM ⑥", ["goodjob_crm 契约插槽", "native_fulfillment · 无外桥"], colors.okFill, colors.okStroke);
    g += node(940, 328, 280, 72, "Site / Calc Engine", ["22 参数核价 · BOQ", "services/calculators"], colors.mintFill, colors.mintStroke);

    // Row 4 assets + async + evidence + external
    g += cluster(20, 440, 400, 150, "智能资产 · PSSP");
    g += node(40, 468, 360, 44, "76 技能 / 309 角色 / 286 SOP", "PSSP = Persona ⊕ Skill ⊕ SOP ⊕ Context", colors.infoFill, colors.infoStroke);
    g += node(40, 524, 360, 44, "Experience Engine", "evolution_experiences + win/loss 闭环", colors.okFill, colors.okStroke);

    g += cluster(440, 440, 280, 150, "异步任务与调度");
    g += node(460, 468, 240, 44, "Celery 分布式队列", "celery / deerflow / cross_border", colors.mintFill, colors.mintStroke);
    g += node(460, 524, 240, 44, "Beat + APScheduler", "rank/geo/hermes_patrol/ops", colors.mintFill, colors.mintStroke);

    g += cluster(740, 440, 240, 150, "取证与证据");
    g += node(760, 468, 200, 44, "Browser Runtime", "Playwright 沙箱", colors.mintFill, colors.mintStroke);
    g += node(760, 524, 200, 44, "EvidenceAnalyzer", "自动分析 ✅ 已接通", colors.okFill, colors.okStroke);

    g += cluster(1000, 440, 260, 150, "外部与分发");
    g += node(1020, 468, 220, 44, "WhatsApp 通道", "入站事件总线 ✅ 已接通", colors.okFill, colors.okStroke);
    g += node(1020, 524, 220, 44, "n8n :5678", "content-publish-dispatch ✅", colors.okFill, colors.okStroke);

    // Row 5 storage
    g += cluster(20, 610, 1240, 86, "数据存储层");
    g += node(40, 636, 280, 42, "PostgreSQL 15.8", "localhost:5433 · 229 表", colors.infoFill, colors.infoStroke);
    g += node(340, 636, 280, 42, "Redis 5.0", "localhost:6379 · 缓存/队列", colors.infoFill, colors.infoStroke);
    g += node(640, 636, 280, 42, "MinIO 对象存储", "9000/9001 · 文件/单证", colors.infoFill, colors.infoStroke);
    g += node(940, 636, 280, 42, "Qdrant 向量库", "6333 · AI 知识库", colors.infoFill, colors.infoStroke);

    // arrows
    g += arrow(180, 94, 180, 158, "#4A9B8C", false, "HTTP");
    g += arrow(180, 266, 780, 328, "#4A9B8C", false, "服务层→编排");
    g += arrow(800, 266, 480, 328, "#2F9E6B", false, "TaskGraph");
    g += arrow(1100, 266, 780, 328, "#2F9E6B", false, "契约分发");
    g += arrow(220, 400, 220, 468, "#2F9E6B", false, "PSSP");
    g += arrow(480, 400, 480, 468, "#4A9B8C", false, "异步");
    g += arrow(860, 400, 860, 468, "#D18B2F", false, "取证");
    g += arrow(1130, 400, 1130, 468, "#2F9E6B", false, "入站总线 ✅");
    g += arrow(220, 610, 220, 636, "#3D7EA6", false, "存储");

    return wrapSvg(g, 1280, 720);
  }

  function buildSimplifiedSvg() {
    const layers = [
      ["用户接入", "官网 / 超管 / SEO 后台", "#245e54", "#4A9B8C"],
      ["核心控制面", "FastAPI · 路由 · 服务 · ORM", "#245e54", "#4A9B8C"],
      ["编排层", "Harness → Hermes → Governor", "#1f4560", "#7EB6D8"],
      ["业务执行器", "TradeAI / DeerFlow / GoodJob / Calc", "#245c43", "#6FCF97"],
      ["智能资产", "技能 · 角色 · SOP · PSSP", "#1f4560", "#7EB6D8"],
      ["异步与分发", "Celery · n8n · Webhook", "#245e54", "#4A9B8C"],
      ["数据存储", "PG / Redis / MinIO / Qdrant", "#1f4560", "#7EB6D8"]
    ];
    let g = "";
    layers.forEach((layer, i) => {
      const y = 30 + i * 90;
      g += node(80, y, 560, 64, layer[0], layer[1], layer[2], layer[3]);
      if (i < layers.length - 1) {
        g += arrow(360, y + 64, 360, y + 90, "#4A9B8C", false, "");
      }
    });
    g += arrow(640, 320, 760, 320, "#2F9E6B", false, "契约/任务");
    g += node(760, 288, 420, 64, "已接通亮点", ["Trade AI Agent + GoodJob CRM 适配器", "Experience 反馈挂接 · n8n 发布"], "#245c43", "#6FCF97");
    g += arrow(640, 500, 760, 500, "#D18B2F", true, "仍缺口");
    g += node(760, 468, 420, 64, "残余缺口", ["WhatsApp 入站事件总线", "证据自动分析管道"], "#6b4d22", "#E0B15C");
    return wrapSvg(g, 1220, 700);
  }

  function buildComponentSvg() {
    let g = "";
    g += cluster(20, 20, 380, 220, "前端组件");
    g += node(40, 50, 340, 40, "官网组件", "Vite 运行源", "#245e54", "#4A9B8C");
    g += node(40, 105, 340, 40, "超管后台组件", "Nuxt3", "#245e54", "#4A9B8C");
    g += node(40, 160, 340, 40, "SEO 管理组件", "独立 Node", "#245e54", "#4A9B8C");

    g += cluster(430, 20, 380, 220, "后端服务");
    g += node(450, 50, 340, 40, "FastAPI 主服务", "backend:8001", "#1f4560", "#7EB6D8");
    g += node(450, 105, 340, 40, "42 个子系统服务", "660+ 服务模块", "#1f4560", "#7EB6D8");
    g += node(450, 160, 340, 40, "150 个路由模块", "/api/v1/*", "#1f4560", "#7EB6D8");

    g += cluster(840, 20, 400, 220, "数据与任务");
    g += node(860, 50, 360, 40, "93 个 ORM 模型", "SQLAlchemy 2.0", "#6b4d22", "#E0B15C");
    g += node(860, 105, 360, 40, "229 张数据库表", "PostgreSQL 15.8", "#6b4d22", "#E0B15C");
    g += node(860, 160, 360, 40, "18+ Celery 任务", "3 队列调度", "#6b4d22", "#E0B15C");

    g += cluster(20, 270, 1220, 200, "编排与执行（修复后）");
    g += node(40, 305, 360, 130, "Hermes 编排", ["调度主权 D3", "进程内直驱执行器", "JsonPath 数据总线", "Saga 补偿"], "#1f4560", "#7EB6D8");
    g += node(440, 305, 360, 130, "原生能力域（已融合）", ["拓客⑤ native_acquisition", "CRM⑥ native_fulfillment", "native_crm_executor 插槽", "无外挂 HTTP 桥"], "#245c43", "#6FCF97");
    g += node(840, 305, 360, 130, "本轮已补齐", ["WhatsApp 入站事件总线 ✅", "证据自动分析管道 ✅", "真环境凭证仍属运维", "非架构断点"], "#245c43", "#6FCF97");

    g += arrow(210, 240, 620, 305, "#4A9B8C", false, "");
    g += arrow(620, 240, 620, 305, "#4A9B8C", false, "");
    g += arrow(1040, 240, 1040, 305, "#3D7EA6", false, "");
    return wrapSvg(g, 1260, 500);
  }

  function buildTradeSvg() {
    const steps = [
      ["1 询盘捕获", "Trade AI Agent 统一收件箱", "#245c43", "#6FCF97"],
      ["2 需求核算", "BOQ + 22 参数核价", "#245e54", "#4A9B8C"],
      ["3 形式发票", "GoodJob PI Generator", "#245c43", "#6FCF97"],
      ["4 定金核销", "支付验证 / 状态机", "#245e54", "#4A9B8C"],
      ["5 生产跟单", "订单进度与异常", "#245e54", "#4A9B8C"],
      ["6 发运单证", "CI / PL / 报关草单", "#245c43", "#6FCF97"],
      ["7 尾款物流", "结算 + 证据链", "#245e54", "#4A9B8C"]
    ];
    let g = "";
    steps.forEach((s, i) => {
      const x = 40 + i * 175;
      g += node(x, 80, 155, 70, s[0], s[1], s[2], s[3]);
      if (i < steps.length - 1) g += arrow(x + 155, 115, x + 175, 115, "#4A9B8C", false, "");
    });
    g += node(40, 220, 420, 70, "Hermes 履约模板", ["_fulfillment_graph 8 节点", "进程内直驱本项目能力域"], "#1f4560", "#7EB6D8");
    g += node(500, 220, 360, 70, "本项目 CRM 原生直驱", ["native_fulfillment PI/CI/PL", "优丁 PG 真相 · 无外桥"], "#245c43", "#6FCF97");
    g += node(900, 220, 300, 70, "WhatsApp 通道", ["入站事件总线 ✅", "whatsapp_events API"], "#245c43", "#6FCF97");
    g += arrow(250, 150, 250, 220, "#7EB6D8", false, "编排");
    g += arrow(680, 150, 680, 220, "#6FCF97", false, "执行");
    g += arrow(1050, 150, 1050, 220, "#E0B15C", true, "缺口");
    return wrapSvg(g, 1260, 330);
  }

  function buildOrchestrationSvg() {
    let g = "";
    g += node(40, 40, 220, 70, "DeepSeek Harness", "外层认知沙箱", "#245e54", "#4A9B8C");
    g += node(320, 40, 240, 70, "Hermes DAG Supervisor", "TaskGraph Spec JSON", "#1f4560", "#7EB6D8");
    g += node(620, 40, 220, 70, "DAG Governor", "DFS / Kahn · ≤100", "#6b4d22", "#E0B15C");
    g += node(900, 40, 260, 70, "ExecutorRegistry", "能力白名单 + 审批", "#245e54", "#4A9B8C");

    g += node(40, 180, 260, 70, "accio 执行器", "销售执行", "#245e54", "#4A9B8C");
    g += node(340, 180, 260, 70, "deerflow 执行器", "研报/内容/发布", "#245e54", "#4A9B8C");
    g += node(640, 180, 260, 70, "本项目拓客 ⑤", ["trade_ai_agent 插槽", "native 原生直驱 · 无外桥"], "#245c43", "#6FCF97");
    g += node(940, 180, 260, 70, "本项目 CRM ⑥", ["goodjob_crm 插槽", "native_fulfillment · 无外桥"], "#245c43", "#6FCF97");

    g += node(40, 320, 520, 70, "PSSP 组装", "Agent = Persona ⊕ Skill ⊕ SOP ⊕ Context", "#1f4560", "#7EB6D8");
    g += node(620, 320, 580, 70, "执行反馈 / Saga", "结果回写 · 失败补偿 · 经验沉淀", "#245c43", "#6FCF97");

    g += arrow(260, 75, 320, 75, "#4A9B8C", false, "JSON-RPC");
    g += arrow(560, 75, 620, 75, "#4A9B8C", false, "拓扑校验");
    g += arrow(840, 75, 900, 75, "#4A9B8C", false, "分发");
    g += arrow(1030, 110, 1030, 180, "#2F9E6B", false, "契约");
    g += arrow(770, 110, 770, 180, "#2F9E6B", false, "契约");
    g += arrow(470, 110, 470, 180, "#4A9B8C", false, "契约");
    g += arrow(170, 110, 170, 180, "#4A9B8C", false, "契约");
    g += arrow(170, 250, 170, 320, "#7EB6D8", false, "组装");
    g += arrow(910, 250, 910, 320, "#6FCF97", false, "反馈");
    g += arrow(620, 355, 320, 355, "#D18B2F", true, "Saga 补偿回写");
    return wrapSvg(g, 1260, 430);
  }

  function buildDataFlowSvg() {
    let g = "";
    // domestic + overseas dual track
    g += node(40, 40, 260, 64, "国内集采漏斗", "DomesticInquiry + 企微", "#245e54", "#4A9B8C");
    g += node(40, 130, 260, 64, "海外外贸 7 步", "询盘 → PI → 发运", "#245e54", "#4A9B8C");
    g += node(40, 220, 260, 64, "B2B 平台收件箱", "Alibaba / MIC / GS", "#245e54", "#4A9B8C");

    g += node(360, 130, 260, 64, "本项目 CRM ⑥", "goodjob · native_fulfillment", "#245c43", "#6FCF97");
    g += node(360, 40, 260, 64, "本项目拓客 ⑤", "trade_ai · native_acquisition", "#245c43", "#6FCF97");

    g += node(680, 40, 240, 64, "Hermes 编排", "意图 → TaskGraph", "#1f4560", "#7EB6D8");
    g += node(680, 130, 240, 64, "Experience Engine", "win/loss / 异议 / 履约", "#245c43", "#6FCF97");
    g += node(680, 220, 240, 64, "内容发布链", "DeerFlow → n8n", "#245c43", "#6FCF97");

    g += node(980, 40, 240, 64, "WhatsApp 通道", "入站总线 ✅ 已接通", "#245c43", "#6FCF97");
    g += node(980, 130, 240, 64, "证据链", "Analyzer ✅ 自动分析", "#245c43", "#6FCF97");
    g += node(980, 220, 240, 64, "官网 / 外部平台", "发布分发回流", "#245e54", "#4A9B8C");

    g += arrow(300, 72, 360, 72, "#6FCF97", false, "原生");
    g += arrow(300, 162, 360, 162, "#6FCF97", false, "原生");
    g += arrow(300, 252, 360, 252, "#6FCF97", false, "原生");
    g += arrow(490, 40, 490, 130, "#6FCF97", false, "拓客→CRM");
    g += arrow(620, 72, 680, 72, "#7EB6D8", false, "编排");
    g += arrow(620, 162, 680, 162, "#6FCF97", false, "经验反哺");
    g += arrow(620, 252, 680, 252, "#6FCF97", false, "内容");
    g += arrow(920, 72, 980, 72, "#6FCF97", false, "入站总线");
    g += arrow(920, 162, 980, 162, "#6FCF97", false, "自动分析");
    g += arrow(920, 252, 980, 252, "#6FCF97", false, "n8n 分发");
    g += arrow(800, 194, 490, 194, "#6FCF97", false, "策略反哺");

    return wrapSvg(g, 1260, 320);
  }

  function renderDiagram(key) {
    const conf = DIAGRAMS[key] || DIAGRAMS.full;
    const host = document.getElementById("diagram-host");
    if (!host) return;
    host.innerHTML = `
      <div class="panel">
        <div class="panel-title">${esc(conf.title)}</div>
        <div class="panel-desc">${esc(conf.desc)}</div>
        <div class="diagram-shell" id="diagram-svg-host">${conf.svg}</div>
        <div class="legend" aria-label="图例">
          <div class="legend-item"><span class="legend-dot ok"></span>已修复 / 已接通</div>
          <div class="legend-item"><span class="legend-dot warn"></span>部分修复 / 待优化</div>
          <div class="legend-item"><span class="legend-dot gap"></span>仍缺口</div>
          <div class="legend-item"><span class="legend-dot normal"></span>正常链路</div>
          <div class="legend-item"><span class="legend-dot storage"></span>存储 / 中间件</div>
        </div>
      </div>`;
  }

  function showTab(tabId, btn) {
    document.querySelectorAll(".tab-content").forEach((el) => {
      el.classList.remove("active");
    });
    document.querySelectorAll(".tab").forEach((el) => {
      el.classList.remove("active");
      el.setAttribute("aria-selected", "false");
    });
    const panel = document.getElementById(tabId);
    if (panel) panel.classList.add("active");
    if (btn) {
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
    }

    if (tabId === "full-diagram") renderDiagram(currentDiagram || "full");
    if (tabId === "trade-flow") renderDiagram("trade");
    if (tabId === "orchestration") renderDiagram("orchestration");
    if (tabId === "data-flow") renderDiagram("dataflow");
  }

  let currentDiagram = "full";

  function setDiagramMode(mode, btn) {
    currentDiagram = mode;
    document.querySelectorAll("[data-diagram-mode]").forEach((el) => {
      el.classList.toggle("active", el === btn);
      el.setAttribute("aria-pressed", el === btn ? "true" : "false");
    });
    renderDiagram(mode);
  }

  function applyProblemFilter(filter) {
    const fn = problemFilterMap[filter] || problemFilterMap.all;
    let visible = 0;
    document.querySelectorAll(".problem-card").forEach((card) => {
      const show = fn(card);
      card.style.display = show ? "" : "none";
      if (show) visible += 1;
    });
    const counter = document.getElementById("problem-count");
    if (counter) counter.textContent = String(visible);
    document.querySelectorAll("[data-filter]").forEach((el) => {
      el.classList.toggle("active", el.dataset.filter === filter);
      el.setAttribute("aria-pressed", el.dataset.filter === filter ? "true" : "false");
    });
  }

  function currentVisibleSvg() {
    // Prefer the SVG currently mounted in any diagram host
    const hosts = [
      document.querySelector("#diagram-svg-host svg"),
      document.querySelector("#trade-flow-diagram svg"),
      document.querySelector("#orchestration-diagram svg"),
      document.querySelector("#data-flow-diagram svg")
    ];
    return hosts.find(Boolean) || null;
  }

  function exportSvg() {
    const svg = currentVisibleSvg();
    if (!svg) {
      alert("当前没有可导出的架构图，请先切换到包含图示的页签。");
      return;
    }
    const clone = svg.cloneNode(true);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    const source = new XMLSerializer().serializeToString(clone);
    const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    downloadBlob(blob, "AEOS-architecture.svg");
  }

  function exportPng() {
    const svg = currentVisibleSvg();
    if (!svg) {
      alert("当前没有可导出的架构图，请先切换到包含图示的页签。");
      return;
    }
    const vb = (svg.getAttribute("viewBox") || "0 0 1280 720").split(/\s+/).map(Number);
    const width = vb[2] || 1280;
    const height = vb[3] || 720;
    const clone = svg.cloneNode(true);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.setAttribute("width", String(width));
    clone.setAttribute("height", String(height));
    const source = new XMLSerializer().serializeToString(clone);
    const svgUrl = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
    const img = new Image();
    img.onload = function () {
      const canvas = document.createElement("canvas");
      const scale = 2;
      canvas.width = width * scale;
      canvas.height = height * scale;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#10192A";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(function (blob) {
        if (!blob) {
          alert("PNG 导出失败，可改用 SVG 导出或打印视图。");
          return;
        }
        downloadBlob(blob, "AEOS-architecture.png");
      }, "image/png");
    };
    img.onerror = function () {
      alert("PNG 渲染失败，已回退建议使用 SVG 导出。");
    };
    img.src = svgUrl;
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  function bind() {
    document.querySelectorAll(".tab").forEach((btn) => {
      btn.addEventListener("click", function () {
        showTab(btn.dataset.tab, btn);
      });
    });

    document.querySelectorAll("[data-diagram-mode]").forEach((btn) => {
      btn.addEventListener("click", function () {
        setDiagramMode(btn.dataset.diagramMode, btn);
      });
    });

    document.querySelectorAll("[data-filter]").forEach((btn) => {
      btn.addEventListener("click", function () {
        applyProblemFilter(btn.dataset.filter);
      });
    });

    const exportSvgBtn = document.getElementById("export-svg");
    const exportPngBtn = document.getElementById("export-png");
    const printBtn = document.getElementById("print-view");
    if (exportSvgBtn) exportSvgBtn.addEventListener("click", exportSvg);
    if (exportPngBtn) exportPngBtn.addEventListener("click", exportPng);
    if (printBtn) printBtn.addEventListener("click", () => window.print());
  }

  function initTradeAndOthers() {
    const tradeHost = document.getElementById("trade-flow-diagram");
    const orchHost = document.getElementById("orchestration-diagram");
    const dataHost = document.getElementById("data-flow-diagram");
    if (tradeHost) tradeHost.innerHTML = DIAGRAMS.trade.svg;
    if (orchHost) orchHost.innerHTML = DIAGRAMS.orchestration.svg;
    if (dataHost) dataHost.innerHTML = DIAGRAMS.dataflow.svg;
  }

  document.addEventListener("DOMContentLoaded", function () {
    bind();
    renderDiagram("full");
    initTradeAndOthers();
    applyProblemFilter("all");
  });

  // Expose for debugging / tests
  window.AEOS_PAGE = {
    showTab,
    setDiagramMode,
    applyProblemFilter,
    exportSvg,
    exportPng,
    DIAGRAMS
  };
})();
