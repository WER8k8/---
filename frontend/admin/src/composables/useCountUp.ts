import { ref, watch, onMounted, type Ref } from 'vue';

export interface UseCountUpOptions {
  /** 动画时长 ms，默认 900 */
  duration?: number;
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
 * 统计数字载入滚动（纯 requestAnimationFrame，无第三方库）
 */
export function useCountUp(
  target: () => number | null | undefined,
  options: UseCountUpOptions = {},
): Ref<string> {
  const display = ref('0');
  const duration = options.duration ?? 900;

  let raf = 0;

  function run(to: number) {
    const enabled = resolveOption(options.enabled, true);
    const decimals = resolveOption(options.decimals, 0);
    if (!enabled || !Number.isFinite(to)) return;
    cancelAnimationFrame(raf);
    const startAt = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - startAt) / duration);
      const val = to * easeOutCubic(t);
      display.value =
        decimals > 0 ? val.toFixed(decimals) : String(Math.round(val));
      if (t < 1) raf = requestAnimationFrame(tick);
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
