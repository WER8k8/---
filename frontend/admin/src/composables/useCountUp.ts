/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, watch, onBeforeUnmount, type Ref } from 'vue';

export interface UseCountUpOptions {
  /** 首次载入动画时长 ms，默认 900 */
  duration?: number;
  /**
   * **值更新时**的补间时长 ms，默认 260。
   * 比 `duration` 短，因为更新（如图表游标联动）需要跟手，900ms 会明显滞后。
   */
  changeDuration?: number;
  /** 小数位，默认 0 */
  decimals?: number | (() => number);
  /** 是否启用 */
  enabled?: boolean | (() => boolean);
}

function resolveOption<T>(v: T | (() => T) | undefined, fallback: T): T {
  if (typeof v === 'function') return (v as () => T)();
  return v ?? fallback;
}

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

/**
 * 统计数字滚动（纯 requestAnimationFrame，无第三方库）
 *
 * 两种补间语义（这是「码表丝滑」的关键）：
 *   · **首次**：从 0 爬升到目标值 —— 保留载入时的滚动效果
 *   · **后续更新**：从**当前显示值**补间到新值 —— 不跳回 0 重跑
 *
 * ⚠️ 历史缺陷（本版修复）：旧实现为 `val = to * ease(t)`，
 *    恒从 0 插值。导致图表游标联动时数字**反复跳回 0 再爬升**，
 *    与「机械码表丝滑翻滚」的诉求正好相反。
 */
export function useCountUp(
  target: () => number | null | undefined,
  options: UseCountUpOptions = {},
): Ref<string> {
  const display = ref('0');
  const duration = options.duration ?? 900;

  let raf = 0;
  /** 上一次显示到的数值，作为下次补间的起点 */
  let currentValue = 0;
  /** 是否已启动过首次载入动画 */
  let started = false;

  function format(val: number, decimals: number): string {
    return decimals > 0 ? val.toFixed(decimals) : String(Math.round(val));
  }

  function run(to: number) {
    const enabled = resolveOption(options.enabled, true);
    const decimals = resolveOption(options.decimals, 0);
    if (!Number.isFinite(to)) return;

    // ⚠️ 语义修正（此前是 `if (!enabled) return;`）：
    //    `enabled: false` 应当表示「**不做动画**」，而不是「**不更新数字**」。
    //    旧写法会让读数永远冻结在旧值（首次则冻结在 0），降级场景下直接丢数据。
    //    正确行为：直接落值，只是没有补间。
    if (!enabled) {
      cancelAnimationFrame(raf);
      currentValue = to;
      started = true;
      display.value = format(to, decimals);
      return;
    }

    // 首次从 0 起；后续从当前值起（避免跳回 0）
    const from = started ? currentValue : 0;
    const dur = started ? resolveOption(options.changeDuration, 260) : duration;

    cancelAnimationFrame(raf);

    // 值没变就不必跑动画，直接落到目标（防止无意义的 60fps 空转）
    if (from === to) {
      currentValue = to;
      display.value = format(to, decimals);
      started = true;
      return;
    }

    // 先置 started，这样动画途中若目标再次变化，
    // 会从"当前插值中的值"接着补间，而不是回退到 0
    started = true;

    const startAt = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - startAt) / dur);
      const val = from + (to - from) * easeOutCubic(t);
      currentValue = val;
      display.value = format(val, decimals);
      if (t < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        currentValue = to;
      }
    };
    raf = requestAnimationFrame(tick);
  }

  watch(
    target,
    (v) => {
      if (v == null || !Number.isFinite(v)) return;
      run(v);
    },
    { immediate: true },
  );

  // 组件卸载时取消未完成的帧，避免 rAF 泄漏
  onBeforeUnmount(() => cancelAnimationFrame(raf));

  return display;
}

/** 从 "98.2%" / "12,506" 等字符串解析数值与后缀 */
export function parseMetricValue(raw: string | number | undefined | null): {
  num: number | null;
  suffix: string;
  decimals: number;
} {
  if (raw === undefined || raw === null || raw === '') {
    return { num: null, suffix: '', decimals: 0 };
  }
  if (typeof raw === 'number' && Number.isFinite(raw)) {
    return { num: raw, suffix: '', decimals: 0 };
  }
  const s = String(raw).trim();
  const match = s.match(/^([\d,]+(?:\.\d+)?)(.*)$/);
  if (!match) return { num: null, suffix: s, decimals: 0 };
  const numStr = match[1].replace(/,/g, '');
  const num = Number(numStr);
  const decimals = numStr.includes('.') ? (numStr.split('.')[1]?.length ?? 0) : 0;
  return {
    num: Number.isFinite(num) ? num : null,
    suffix: match[2] ?? '',
    decimals,
  };
}
