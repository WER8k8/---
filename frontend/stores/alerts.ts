import { useApi } from "~/composables/useApi";
import type { Alert, AlertRule, AlertStatistics } from "~/types/alert";

export const useAlertsStore = defineStore("alerts", () => {
  const api = useApi();

  const alerts = ref<Alert[]>([]);
  const rules = ref<AlertRule[]>([]);
  const statistics = ref<AlertStatistics | null>(null);
  const loading = ref(false);
  const currentAlert = ref<Alert | null>(null);
  const currentRule = ref<AlertRule | null>(null);

  const activeAlerts = computed(() =>
    alerts.value.filter(a => a.status === "active")
  );

  const criticalAlerts = computed(() =>
    alerts.value.filter(a => a.severity === "critical")
  );

  async function fetchAlerts(params: Record<string, unknown> = {}) {
    loading.value = true;
    try {
      const response = await api.get<{ items: Alert[] }>("/alerts", params);
      alerts.value = response.items || [];
      return response;
    } finally {
      loading.value = false;
    }
  }

  async function fetchRules() {
    loading.value = true;
    try {
      rules.value = await api.get<AlertRule[]>("/alerts/rules");
    } finally {
      loading.value = false;
    }
  }

  async function fetchStatistics() {
    try {
      statistics.value = await api.get<AlertStatistics>("/alerts/statistics");
    } catch (error) {
      console.error("Failed to fetch statistics:", error);
    }
  }

  async function createRule(ruleData: Partial<AlertRule>) {
    const rule = await api.post<AlertRule>("/alerts/rules", ruleData);
    rules.value.unshift(rule);
    return rule;
  }

  async function createAlert(alertData: Partial<Alert>) {
    const alert = await api.post<Alert>("/alerts", alertData);
    alerts.value.unshift(alert);
    return alert;
  }

  async function acknowledgeAlert(alertId: number, data: Record<string, unknown> = {}) {
    const alert = await api.post<Alert>(`/alerts/${alertId}/acknowledge`, data);
    const index = alerts.value.findIndex(a => a.id === alertId);
    if (index !== -1) {
      alerts.value[index] = alert;
    }
    if (currentAlert.value?.id === alertId) {
      currentAlert.value = alert;
    }
    return alert;
  }

  async function resolveAlert(alertId: number, data: Record<string, unknown> = {}) {
    const alert = await api.post<Alert>(`/alerts/${alertId}/resolve`, data);
    const index = alerts.value.findIndex(a => a.id === alertId);
    if (index !== -1) {
      alerts.value[index] = alert;
    }
    if (currentAlert.value?.id === alertId) {
      currentAlert.value = alert;
    }
    return alert;
  }

  async function getAlert(alertId: number) {
    const alert = await api.get<Alert>(`/alerts/${alertId}`);
    currentAlert.value = alert;
    return alert;
  }

  async function getRule(ruleId: number) {
    const rule = await api.get<AlertRule>(`/alerts/rules/${ruleId}`);
    currentRule.value = rule;
    return rule;
  }

  async function getAlertHistories(alertId: number) {
    return await api.get<unknown[]>(`/alerts/${alertId}/histories`);
  }

  async function triggerRule(ruleId: number, context: Record<string, unknown> = {}) {
    return await api.post<unknown>(`/alerts/rules/${ruleId}/trigger`, context);
  }

  async function checkAllRules(context: Record<string, unknown> = {}) {
    const newAlerts = await api.post<Alert[]>("/alerts/check-all", context);
    alerts.value = [...newAlerts, ...alerts.value];
    return newAlerts;
  }

  function setCurrentAlert(alert: Alert | null) {
    currentAlert.value = alert;
  }

  function setCurrentRule(rule: AlertRule | null) {
    currentRule.value = rule;
  }
  
  return {
    alerts,
    rules,
    statistics,
    loading,
    currentAlert,
    currentRule,
    activeAlerts,
    criticalAlerts,
    fetchAlerts,
    fetchRules,
    fetchStatistics,
    createRule,
    createAlert,
    acknowledgeAlert,
    resolveAlert,
    getAlert,
    getRule,
    getAlertHistories,
    triggerRule,
    checkAllRules,
    setCurrentAlert,
    setCurrentRule,
  };
});
