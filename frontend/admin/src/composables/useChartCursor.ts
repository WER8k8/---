/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 *
 * 图表磁吸游标（Magnetic Cursor）
 * ─────────────────────────────────────────────────────────────
 * 用途：折线图横向滑动时，指示线**吸附最近数据点**，并把吸附到的值抛出去，
 *      与指标卡 / 码表（useCountUp）联动，形成"游标滑动 → 数值丝滑翻滚"。
 *
 * ⚠️ 接入前必读（实测发现）：
 *   1. 本项目 8 个图表文件用 `vue-echarts` 的 `use([...])` 按需注册，
 *      **没有一个注册 `AxisPointerComponent`**。
 *        · 仅用 tooltip 驱动的指示线（随 tooltip 显隐）→ `TooltipComponent` 够用
 *        · 若要**常驻**指示线（`xAxis.axisPointer.show = true`）→ 必须补注册：
 *          `import { AxisPointerComponent } from 'echarts/components'` 并加入 `use([...])`
 *   2. 配色一律读设计令牌（`--uj-brand` 等），**不要硬编码十六进制** ——
 *      项目主色按壳切换（platform/client/agent），硬编码会破坏 agent 壳。
 *   3. 动效接 `prefers-reduced-motion`：降低动态效果时关闭吸附动画与呼吸光晕。
 */
import { ref, onBeforeUnmount, type Ref } from 'vue';

export interface SnapCursorConfig {
  /** 游标线颜色，默认读令牌 `--uj-brand` */
  lineColor?: string;
  /** 游标线宽，默认 1 */
  lineWidth?: number;
  /** 数据点强调时的圆点大小（配 series.symbolSize 使用） */
  symbolSize?: number;
  /** 是否启用"呼吸光晕"强调，默认 true；降低动态效果时自动关闭 */
  breath?: boolean;
}

/** 读 CSS 变量并回退，保证与设计令牌单一真源一致 */
function cssVar(name: string, fallback: string): string {
  if (typeof window === 'undefined' || !document?.documentElement) return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

/** 是否处于"降低动态效果"偏好 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export interface SnapCursorFragments {
  tooltip: Record<string, unknown>;
  xAxis: Record<string, unknown>;
  seriesEmphasis: Record<string, unknown>;
}

/**
 * 生成「磁吸游标」的 echarts 配置片段（纯函数，无副作用）。
 *
 * 用法：把返回值浅合并进既有 option，不要整体替换：
 * ```ts
 * const snap = buildSnapCursor();
 * const option = computed(() => ({
 *   ...baseOption.value,
 *   tooltip: { ...baseOption.value.tooltip, ...snap.tooltip },
 *   xAxis: { ...baseOption.value.xAxis, ...snap.xAxis },
 *   series: baseOption.value.series.map((s) => ({
 *     ...s, emphasis: { ...s.emphasis, ...snap.seriesEmphasis },
 *   })),
 * }));
 * ```
 */
export function buildSnapCursor(cfg: SnapCursorConfig = {}): SnapCursorFragments {
  const color = cfg.lineColor ?? cssVar('--uj-brand', '#4a9b8c');
  const reduce = prefersReducedMotion();
  const breath = cfg.breath !== false && !reduce;

  return {
    tooltip: {
      // 必须是 axis 触发，否则不会出现横向游标
      trigger: 'axis',
      axisPointer: {
        type: 'line',
        /** ★ 磁吸关键：吸附到最近数据点，而不是跟着鼠标像素自由移动 */
        snap: true,
        // 降低动态效果时不做指示线动画
        animation: !reduce,
        lineStyle: {
          color,
          width: cfg.lineWidth ?? 1,
          type: 'dashed',
        },
        // 顶部数值交给码表承担，避免与 tooltip 形成双份读数
        label: { show: false },
      },
    },
    xAxis: {
      axisPointer: { snap: true },
    },
    seriesEmphasis: {
      focus: 'series',
      // 呼吸放大：降低动态效果时关闭
      scale: !reduce,
      itemStyle: {
        borderColor: color,
        borderWidth: 2,
        shadowBlur: breath ? 10 : 0,
        shadowColor: color,
      },
    },
  };
}

export interface CursorInfo {
  /** 轴上的值（如月份 'Jan'）；具体类型取决于 xAxis.type */
  value: unknown;
  /** 数据索引；拿不到时为 -1 */
  dataIndex: number;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
type AnyOption = Record<string, any>;

/** 只在 base 是普通对象时浅合并；数组/原始值直接取 extra（避免把坐标轴数组拍成对象） */
function mergeShape(base: unknown, extra: AnyOption): AnyOption {
  if (base && typeof base === 'object' && !Array.isArray(base)) {
    return { ...(base as AnyOption), ...extra };
  }
  if (base === undefined) return extra;
  return base as AnyOption;
}

/**
 * 一次性把「磁吸游标」应用到整份 echarts option 上。
 *
 * 相比手工展开 `buildSnapCursor()` 的片段，这个包装器：
 *   · 保留既有 `tooltip.formatter`（不会被覆盖）
 *   · **保留既有的 `axisPointer.type`**（例如横向条形图用的 `'shadow'` 不会被改成 `'line'`）
 *   · 对 `series` 数组逐条补 `emphasis`，不影响其它 series 配置
 *   · `xAxis` 是数组时原样保留（只对单对象形态注入 snap）
 *
 * ⚠️ 适用范围：**只用于有连续/分类直角轴的折线图**。
 *    饼图（无直角轴）不适用；柱状图本身已按分类吸附，无需处理。
 *
 * ⚠️ 无需额外注册组件：`TooltipComponent` 在 echarts 内部已 `use(installAxisPointer)`
 *    （见 `echarts/lib/component/tooltip/install.js`），
 *    `updateAxisPointer` action 也已注册。**不需要**再引 `AxisPointerComponent`。
 */
export function applySnapCursor<T extends AnyOption>(
  option: T,
  cfg: SnapCursorConfig = {},
): T {
  const frag = buildSnapCursor(cfg);

  // 保留既有 axisPointer 类型（如 shadow），其余吸附参数照常注入
  const existingType = (option?.tooltip as AnyOption | undefined)?.axisPointer?.type;
  const axisPointer = existingType
    ? { ...(frag.tooltip.axisPointer as AnyOption), type: existingType }
    : frag.tooltip.axisPointer;

  const series = Array.isArray(option.series)
    ? option.series.map((s: AnyOption) => ({
        ...s,
        emphasis: { ...((s?.emphasis as AnyOption) ?? {}), ...frag.seriesEmphasis },
      }))
    : option.series;

  return {
    ...option,
    tooltip: mergeShape(option.tooltip, {
      trigger: 'axis',
      axisPointer: axisPointer as AnyOption,
    }),
    xAxis: mergeShape(option.xAxis, frag.xAxis),
    ...(series === undefined ? {} : { series }),
  } as T;
}
/* eslint-enable @typescript-eslint/no-explicit-any */

/**
 * ECharts 实例的最小结构。刻意不引 echarts 类型，保持本助手零耦合、可独立复用。
 *
 * `on` 声明为**必需**：`resolveChart()` 只会在 `on` 确为函数时才返回对象，
 * 所以这是被保证的不变式。若把它写成可选，调用处每处都要再收窄一次
 * （`chart.on(...)` 会报 TS2722），属于把保证丢给调用方。
 */
export interface ChartLike {
  on: (event: string, handler: (payload: unknown) => void) => void;
  off?: (event: string, handler: (payload: unknown) => void) => void;
}

/**
 * 从任意来源中取出底层 ECharts 实例。支持两种入参：
 *   1. **已经是 ECharts 实例**（自身带 on/off）→ 原样返回
 *   2. **vue-echarts 的组件实例** → 读它 `expose` 出来的 `chart` getter
 *
 * ⚠️ 第 2 条是实测确认的，不是猜的：
 *    `vue-echarts@8` 的 `dist/index.js` 末尾：
 *      `expose(Object.assign({ setOption, get root() {...}, get chart() {...} }, publicApi))`
 *    所以 `<v-chart ref="r">` 上 **`r.chart`** 就是底层实例，`r` 本身**不是**。
 *    直接 `bind(r)` 会因为 `r.on` 不存在而静默失败——这是最容易踩的坑。
 */
export function resolveChart(source: unknown): ChartLike | null {
  if (!source || typeof source !== 'object') return null;
  const self = source as ChartLike;
  if (typeof self.on === 'function') return self;
  const inner = (source as { chart?: unknown }).chart;
  if (inner && typeof (inner as ChartLike).on === 'function') return inner as ChartLike;
  return null;
}

/**
 * 订阅"游标吸附到哪个数据点"，输出 index 与解析后的值。
 *
 * @param resolve 用 (info) => T 把你的数据源映射成要展示的值（如某条 series 的 y 值）。
 *                由调用方提供，因为"取哪条 series 的哪个值"是业务问题，
 *                不能由本助手猜。
 */
export function useChartCursor<T = number>(
  resolve?: (info: CursorInfo) => T | null,
) {
  const activeIndex: Ref<number> = ref(-1);
  const activeValue: Ref<T | null> = ref<T | null>(null) as Ref<T | null>;
  /** 实例是否已成功绑定；页面可据此决定是否显示联动读数 */
  const chartReady: Ref<boolean> = ref(false);

  let chart: ChartLike | null = null;

  function onAxisPointer(payload: unknown) {
    const e = payload as {
      dataIndex?: number;
      axesInfo?: Array<{ value?: unknown }>;
    } | null;
    const axisValue = e?.axesInfo?.[0]?.value;
    const idx =
      typeof e?.dataIndex === 'number'
        ? e.dataIndex
        : typeof axisValue === 'number'
          ? axisValue
          : -1;

    activeIndex.value = idx >= 0 ? idx : -1;
    if (resolve && idx >= 0) {
      activeValue.value = resolve({ value: axisValue, dataIndex: idx });
    }
  }

  function clear() {
    activeIndex.value = -1;
    activeValue.value = null;
  }

  /**
   * 绑定到 `<v-chart ref="chartRef">` 的 `chartRef.value`（组件实例），
   * 或直接绑定 ECharts 实例。返回是否绑定成功。
   *
   * 重复调用会先解绑，避免同一实例上叠加两份 handler。
   */
  function bind(instance: unknown): boolean {
    const inst = resolveChart(instance);
    if (!inst) return false;
    if (chart) unbind();
    chart = inst;
    chart.on('updateAxisPointer', onAxisPointer);
    // 鼠标移出图表区域时复位，避免数值停在最后一个点
    chart.on('globalout', clear);
    chartReady.value = true;
    return true;
  }

  function unbind(): void {
    // 先断开引用，再解绑事件：避免 off 过程中重入导致重复解绑
    const inst = chart;
    chart = null;
    chartReady.value = false;
    // 显式收窄：`if (!chart?.off) return;` 这种写法 TS 不会把 chart.off 收窄成函数
    if (!inst || typeof inst.off !== 'function') return;
    inst.off('updateAxisPointer', onAxisPointer);
    inst.off('globalout', clear);
  }

  /**
   * 有界重试绑定。**这一步在实际页面上是必需的，不是保险起见**：
   *
   *   · 图表通常被 `v-if` 包在骨架屏 / 空态之后（本项目的看板页都是这个结构），
   *     父组件 `onMounted` 时模板 ref 仍然是 `null`；
   *   · `vue-echarts` 的实例初始化还会走 `initDeferred` + `nextTick`，
   *     比 ref 赋值再晚一帧，此刻 `ref.chart` 仍是 `undefined`。
   *
   * 因此按帧重试，**最多 maxFrames 帧后就放弃并返回 false**，不会无限自旋。
   *
   * @param get 取实例来源的 getter（传 `() => chartRef.value`，不要传值，
   *            否则 ref 后置变化时拿不到新值）
   */
  function bindWhenReady(get: () => unknown, maxFrames = 30): Promise<boolean> {
    return new Promise((resolve) => {
      let frames = 0;
      const attempt = () => {
        if (bind(get())) {
          resolve(true);
          return;
        }
        if (++frames >= maxFrames) {
          resolve(false);
          return;
        }
        if (typeof requestAnimationFrame === 'function') requestAnimationFrame(attempt);
        else setTimeout(attempt, 16);
      };
      attempt();
    });
  }

  onBeforeUnmount(unbind);

  return { activeIndex, activeValue, chartReady, bind, bindWhenReady, unbind, clear };
}
