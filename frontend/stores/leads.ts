interface LeadDraft {
  name: string
  phone: string
  region: string
  message: string
  distance_km?: number | null
  quantity_m3?: number | null
}

export const useLeadsStore = defineStore('leads', () => {
  // ===== 询盘草稿（本地持久化） =====
  const draft = ref<LeadDraft>({
    name: '',
    phone: '',
    region: '',
    message: '',
    distance_km: null,
    quantity_m3: null
  })

  function saveDraft(data: Partial<LeadDraft>) {
    Object.assign(draft.value, data)
  }

  function clearDraft() {
    draft.value = {
      name: '',
      phone: '',
      region: '',
      message: '',
      distance_km: null,
      quantity_m3: null
    }
  }

  // ===== 最近提交记录 =====
  const lastSubmittedId = ref<number | null>(null)
  const lastSubmittedPrice = ref<string>('')

  function recordSubmission(id: number, price: string) {
    lastSubmittedId.value = id
    lastSubmittedPrice.value = price
  }

  return {
    draft,
    saveDraft,
    clearDraft,
    lastSubmittedId,
    lastSubmittedPrice,
    recordSubmission
  }
})
