import { Modal } from 'ant-design-vue';
import type { ModalFuncProps } from 'ant-design-vue';

/** Modal.confirm 安全封装：异步 onOk 须 return Promise，禁止 async onOk */
export function ydConfirm(options: ModalFuncProps) {
  const { onOk, ...rest } = options;
  return Modal.confirm({
    ...rest,
    onOk() {
      if (!onOk) return undefined;
      try {
        const ret = onOk();
        if (ret && typeof (ret as Promise<unknown>).then === 'function') {
          return ret as Promise<void>;
        }
      } catch (e) {
        return Promise.reject(e);
      }
      return undefined;
    },
  });
}
