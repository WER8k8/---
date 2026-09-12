/** visitor-context 网络请求 — 超时、重试、可取消（生产切换不失败） */

export type VisitorContextFetchResult<T> = {
  ok: boolean;
  data?: T;
  status?: number;
};

const TIMEOUT_MS = import.meta.dev ? 12000 : 8000;
const MAX_RETRIES = import.meta.dev ? 1 : 2;

let sharedController: AbortController | null = null;

export function cancelVisitorContextFetch(): void {
  sharedController?.abort();
  sharedController = null;
}

export async function fetchVisitorContextPayload<T>(
  url: string,
  headers: Record<string, string>,
  options?: { cancelPrevious?: boolean; isolated?: boolean },
): Promise<VisitorContextFetchResult<T>> {
  if (!options?.isolated && options?.cancelPrevious !== false) {
    cancelVisitorContextFetch();
  }
  const controller = new AbortController();
  if (!options?.isolated) {
    sharedController = controller;
  }

  let lastStatus: number | undefined;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt += 1) {
    if (controller.signal.aborted) {
      return { ok: false, status: lastStatus };
    }
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const res = await fetch(url, { headers, signal: controller.signal });
      lastStatus = res.status;
      const body = await res.json();
      if (res.ok && body?.data) {
        if (!options?.isolated && sharedController === controller) {
          sharedController = null;
        }
        return { ok: true, data: body.data as T, status: res.status };
      }
      if (res.status >= 500 && attempt < MAX_RETRIES) {
        await new Promise((resolve) => setTimeout(resolve, 250 * (attempt + 1)));
        continue;
      }
      break;
    } catch {
      if (attempt < MAX_RETRIES) {
        await new Promise((resolve) => setTimeout(resolve, 250 * (attempt + 1)));
        continue;
      }
    } finally {
      clearTimeout(timeout);
    }
  }

  if (!options?.isolated && sharedController === controller) {
    sharedController = null;
  }
  return { ok: false, status: lastStatus };
}
