import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { apiGet, apiPost } from '@/utils/api'

export const FEATURE_LABELS: Record<string, string> = {
  seo: 'SEO 优化',
  analytics: '数据分析',
  globalization: '多语言',
  international: '国际询盘',
  content: '内容管理',
  ai: 'AI 写作',
  video: '视频工厂',
  white_label: '品牌定制',
  api: 'API 接口',
}

export function featureList(plan: { features?: string | string[] }): string[] {
  try {
    const raw =
      typeof plan.features === 'string' ? JSON.parse(plan.features) : plan.features
    return (raw as string[]).map((k: string) => FEATURE_LABELS[k] || k)
  } catch {
    return []
  }
}

export function displayPlanPrice(
  plan: { price_monthly: number; price_yearly: number },
  billingCycle: 'monthly' | 'yearly',
): string {
  const amount = billingCycle === 'yearly' ? plan.price_yearly : plan.price_monthly
  return (amount / 100).toFixed(2)
}

export function usePlanPayment() {
  const plans = ref<any[]>([])
  const plansLoading = ref(false)
  const selectedPlanId = ref('')
  const billingCycle = ref<'monthly' | 'yearly'>('monthly')
  const selectedTenantId = ref('')

  const qrVisible = ref(false)
  const paying = ref(false)
  const currentCodeUrl = ref('')
  const currentMock = ref(false)
  const currentOrderId = ref('')
  const currentOrderNo = ref('')
  const currentSubject = ref('')
  const currentAmount = ref(0)
  const mockPaying = ref(false)

  async function resolveTenantId(): Promise<string> {
    if (selectedTenantId.value) return selectedTenantId.value
    try {
      const dash = await apiGet<{ tenant_id?: string; tenant?: { id?: string } }>(
        '/client/dashboard',
      )
      const tid = dash?.tenant_id || dash?.tenant?.id
      if (tid) {
        selectedTenantId.value = String(tid)
        return selectedTenantId.value
      }
    } catch {
      /* ignore */
    }
    try {
      const cur = await apiGet<{ tenant?: { id?: string } }>('/tenants/current')
      const tid = cur?.tenant?.id
      if (tid) {
        selectedTenantId.value = String(tid)
        return selectedTenantId.value
      }
    } catch {
      /* ignore */
    }
    return ''
  }

  async function loadPlans() {
    plansLoading.value = true
    try {
      const data = await apiGet<any[]>('/payment/plans')
      plans.value = data || []
      if (plans.value.length > 0 && !selectedPlanId.value) {
        selectedPlanId.value = plans.value[0].id
      }
    } catch (e: unknown) {
      if (import.meta.env.DEV) console.error(e)
      message.error('加载套餐失败')
    } finally {
      plansLoading.value = false
    }
  }

  async function handlePay(plan: {
    id: string
    name: string
    price_monthly: number
    price_yearly: number
  }) {
    const tid = await resolveTenantId()
    if (!tid) {
      message.warning('无法识别当前租户，请重新登录')
      return
    }

    paying.value = true
    qrVisible.value = true
    currentCodeUrl.value = ''
    currentMock.value = false
    currentOrderId.value = ''
    currentOrderNo.value = ''
    currentSubject.value = `${plan.name} - ${billingCycle.value === 'monthly' ? '月付' : '年付'}`
    currentAmount.value =
      billingCycle.value === 'yearly' ? plan.price_yearly : plan.price_monthly

    try {
      const data = await apiPost<{
        code_url?: string
        mock?: boolean
        id?: string
        order_no?: string
        amount?: number
        subject?: string
      }>('/payment/create-native', {
        tenant_id: tid,
        plan_id: plan.id,
        billing_cycle: billingCycle.value,
      })
      currentCodeUrl.value = data.code_url || ''
      currentMock.value = data.mock || false
      currentOrderId.value = data.id || ''
      currentOrderNo.value = data.order_no || ''
      currentAmount.value = data.amount ?? currentAmount.value
      currentSubject.value = data.subject || currentSubject.value
    } catch (e: unknown) {
      const err = e as { message?: string }
      message.error(err.message || '创建支付订单失败')
      qrVisible.value = false
    } finally {
      paying.value = false
    }
  }

  async function mockPayOrder(onSuccess?: () => void) {
    // 安全检查：仅允许在开发环境使用模拟支付
    if (!import.meta.env.DEV) {
      message.error('模拟支付仅在开发环境可用');
      return;
    }
    if (!currentOrderId.value) return;
    mockPaying.value = true;
    try {
      const data = await apiPost<{ order_no?: string }>('/payment/mock-pay', {
        order_id: currentOrderId.value,
      });
      message.success(`订单 ${data.order_no || ''} 支付成功`);
      qrVisible.value = false;
      onSuccess?.();
    } catch (e: unknown) {
      const err = e as { message?: string };
      message.error(err.message || '模拟支付失败');
    } finally {
      mockPaying.value = false;
    }
  }

  return {
    plans,
    plansLoading,
    selectedPlanId,
    billingCycle,
    selectedTenantId,
    qrVisible,
    paying,
    currentCodeUrl,
    currentMock,
    currentOrderId,
    currentOrderNo,
    currentSubject,
    currentAmount,
    mockPaying,
    resolveTenantId,
    loadPlans,
    handlePay,
    mockPayOrder,
  }
}
