/* 付费转化向控制台演示 · 零外链 */
(function () {
  "use strict";

  const views = {
    ops: {
      title: "今日作战台",
      sub: "待办置顶 · 数字其次 · 趋势再次 · 明细可下钻",
      listTitle: "优先处理",
      listSub: "与收入/风险直接相关",
      moneyTitle: "经营摘要",
      moneySub: "付费决策相关",
      kpi: [
        { label: "今日询盘", value: "42", delta: "较昨日 +18%" },
        { label: "待人审 PI", value: "6", delta: "其中 2 笔超 24h", neg: true },
        { label: "本周成交", value: "9", delta: "转化窗口内" },
        { label: "健康分", value: "92", delta: "编排/权限正常" },
      ],
      tasks: [
        { text: "高优先级询盘：中东基建 RFQ · 需今日核价", tag: "收入", cls: "ok" },
        { text: "Hermes GP-A：PI 节点 wait_human", tag: "人审闸", cls: "warn" },
        { text: "SEO 矩阵：3 篇待发布至多平台", tag: "增长", cls: "info" },
        { text: "证据链：1 条 policy blocked 待复核", tag: "风险", cls: "risk" },
      ],
      money: [
        { k: "本月经常性收入", v: "示意 ¥86,400" },
        { k: "待确认订单额", v: "¥128,000" },
        { k: "AI Token 用量", v: "62% 档位" },
        { k: "需关注流失风险租户", v: "3 家" },
      ],
    },
    money: {
      title: "经营与计费",
      sub: "套餐 · 订单 · 分润 · Token —— 老板最关心的数字",
      listTitle: "计费与回款动态",
      listSub: "影响现金流",
      moneyTitle: "收入结构",
      moneySub: "可持续订阅信号",
      kpi: [
        { label: "MRR 月经常性", value: "¥8.6万", delta: "示意" },
        { label: "订单待收", value: "¥12.8万", delta: "含定金核销中" },
        { label: "代理分润", value: "¥1.2万", delta: "本月累计" },
        { label: "续费预警", value: "3", delta: "7 日内到期", neg: true },
      ],
      tasks: [
        { text: "增长版租户续费窗口开启", tag: "续费", cls: "ok" },
        { text: "支付码与接口巡检通过", tag: "支付", cls: "info" },
        { text: "市级代理佣金待确认", tag: "分润", cls: "warn" },
        { text: "IP 池成本周环比 +4%", tag: "成本", cls: "warn" },
      ],
      money: [
        { k: "SaaS 订阅", v: "62%" },
        { k: "AI Token / 增值", v: "21%" },
        { k: "专业服务/实施", v: "17%" },
        { k: "目标续费率", v: "≥ 85%" },
      ],
    },
    ai: {
      title: "编排与 AI",
      sub: "Hermes 原生直驱 · 资产可复用 · 执行诚实",
      listTitle: "编排执行态势",
      listSub: "可调度才叫系统",
      moneyTitle: "产能与成本",
      moneySub: "AI 是否值钱看这里",
      kpi: [
        { label: "运行中任务图", value: "12", delta: "L1 模板驱动" },
        { label: "Wait Human", value: "5", delta: "设计内审批" },
        { label: "资产库", value: "350+", delta: "技能/角色/SOP" },
        { label: "自检门禁", value: "19/19", delta: "编排链路" },
      ],
      tasks: [
        { text: "社媒拓客图：prospect.scrape 执行中", tag: "拓客", cls: "info" },
        { text: "履约图：document.generate_trade_docs", tag: "单证", cls: "ok" },
        { text: "内容发布链：content_publish_dispatch", tag: "分发", cls: "ok" },
        { text: "无 WA Key 外联诚实 failed（防假成功）", tag: "求真", cls: "warn" },
      ],
      money: [
        { k: "人工跟单占时（目标下降）", v: "↓ 结构性下降" },
        { k: "模板复用率", v: "高" },
        { k: "假成功风险", v: "已压制成 failed/degraded" },
        { k: "扩展边际成本", v: "主要为 Token/通道" },
      ],
    },
    trade: {
      title: "外贸 7 步闭环",
      sub: "询盘到物流一条链，本项目 CRM 原生直驱",
      listTitle: "履约节点",
      listSub: "PI / 定金 / 单证 / 物流",
      moneyTitle: "履约收入信号",
      moneySub: "成交可追踪",
      kpi: [
        { label: "进行中订单", value: "23", delta: "跨 8 个市场" },
        { label: "待发运", value: "4", delta: "单证已齐套" },
        { label: "待定金核销", value: "2", delta: "状态机跟踪" },
        { label: "平均履约周期", value: "↓", delta: "编排后压缩" },
      ],
      tasks: [
        { text: "7 步：询盘 → BOQ 核价 → PI", tag: "主链", cls: "ok" },
        { text: "定金到账 → DEPOSIT_RECEIVED", tag: "状态", cls: "info" },
        { text: "CI/PL/报关草单成套输出", tag: "单证", cls: "ok" },
        { text: "尾款与物流回执回写", tag: "闭环", cls: "info" },
      ],
      money: [
        { k: "本月出海管道", v: "USD/EUR/AED" },
        { k: "国内集采管道", v: "CNY 双轨并行" },
        { k: "单证自动化", v: "PI/CI/PL 原生" },
        { k: "失败透明度", v: "账户未配置 → degraded" },
      ],
    },
    risk: {
      title: "风控与证据",
      sub: "付费企业级的关键：可控、可审、可止损",
      listTitle: "风险与合规动态",
      listSub: "出事前能看见",
      moneyTitle: "风险成本",
      moneySub: "避免隐性损失",
      kpi: [
        { label: "人审闸触发", value: "5", delta: "外发/财务类" },
        { label: "证据异常", value: "3", delta: "已进入分析流" },
        { label: "权限越界拦截", value: "0", delta: "当前窗口" },
        { label: "诚实降级", value: "正常", delta: "不编造银行号" },
      ],
      tasks: [
        { text: "Browser 证据：blocked/超时待复核", tag: "证据", cls: "warn" },
        { text: "WhatsApp 外发等待审批", tag: "外联", cls: "warn" },
        { text: "财务单证 PI 人审队列", tag: "资金", cls: "risk" },
        { text: "操作审计时间轴可追溯", tag: "审计", cls: "ok" },
      ],
      money: [
        { k: "坏账/错发单证风险", v: "闸门前置" },
        { k: "品牌外联封号风险", v: "暖机+人审" },
        { k: "数据权限泄漏", v: "壳层隔离" },
        { k: "为风控付费的理由", v: "避免一次事故回本" },
      ],
    },
  };

  function renderView(key) {
    const v = views[key] || views.ops;
    const title = document.getElementById("view-title");
    const sub = document.getElementById("view-sub");
    const listTitle = document.getElementById("list-title");
    const moneyTitle = document.getElementById("money-title");
    const kpiGrid = document.getElementById("kpi-grid");
    const taskList = document.getElementById("task-list");
    const moneyRows = document.getElementById("money-rows");
    if (title) title.textContent = v.title;
    if (sub) sub.textContent = v.sub;
    if (listTitle) listTitle.innerHTML = `${v.listTitle} <span>${v.listSub}</span>`;
    if (moneyTitle) moneyTitle.innerHTML = `${v.moneyTitle} <span>${v.moneySub}</span>`;
    if (kpiGrid) {
      kpiGrid.innerHTML = v.kpi
        .map(
          (k) =>
            `<div class="kpi"><label>${k.label}</label><b>${k.value}</b><small class="${k.neg ? "neg" : ""}">${k.delta}</small></div>`
        )
        .join("");
    }
    if (taskList) {
      taskList.innerHTML = v.tasks
        .map((t) => `<div class="task"><span>${t.text}</span><span class="tag ${t.cls}">${t.tag}</span></div>`)
        .join("");
    }
    if (moneyRows) {
      moneyRows.innerHTML = v.money
        .map((m) => `<div class="money-row"><span>${m.k}</span><b>${m.v}</b></div>`)
        .join("");
    }
  }

  function bindNav() {
    const nav = document.getElementById("shell-nav");
    if (!nav) return;
    nav.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => {
        nav.querySelectorAll(".nav-item").forEach((el) => el.classList.remove("active"));
        btn.classList.add("active");
        renderView(btn.dataset.view || "ops");
      });
    });
  }

  function bindCta() {
    const scrollPlans = () => {
      const el = document.getElementById("plans");
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    ["btn-cta", "btn-cta-2", "btn-scroll-plans"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener("click", scrollPlans);
    });
    document.querySelectorAll("[data-plan]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const name = btn.dataset.plan || "方案";
        btn.textContent = `已选择 ${name}`;
        btn.disabled = true;
        const note = document.createElement("div");
        note.className = "motion-note";
        note.style.marginTop = "10px";
        note.textContent = `已记录意向：${name}。演示页不发起真实支付；接入商务表单或 CRM 后即可闭环。`;
        const plans = document.getElementById("plans");
        if (plans) plans.appendChild(note);
      });
    });
  }

  function init() {
    renderView("ops");
    bindNav();
    bindCta();
  }

  document.addEventListener("DOMContentLoaded", init);

  window.YOUDING_MOTION_DEMO = { renderView, views };
})();
