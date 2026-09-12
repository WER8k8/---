import { ref } from 'vue'

type StrategyItem = Record<string, unknown>

/** 跨轮次保留 UBrain 策略选项，供用户回复 A/B/C 展开 */
export function useUbrainChatContext() {
  const lastStrategies = ref<StrategyItem[]>([])

  function applyReply(data: { tool_result?: { strategies?: StrategyItem[] } }) {
    const strategies = data.tool_result?.strategies
    if (Array.isArray(strategies) && strategies.length > 0) {
      lastStrategies.value = strategies
    }
  }

  type Turn = { role: string; text: string }

  function buildBody(message: string, recentMessages?: Turn[]) {
    const body: {
      message: string
      context?: { last_strategies?: StrategyItem[]; recent_turns?: Turn[] }
    } = { message }
    const context: NonNullable<(typeof body)['context']> = {}
    if (lastStrategies.value.length > 0) {
      context.last_strategies = lastStrategies.value
    }
    if (recentMessages?.length) {
      context.recent_turns = recentMessages
        .slice(-8)
        .map((m) => ({
          role: m.role,
          text: (m.text || '').slice(0, 400),
        }))
    }
    if (Object.keys(context).length > 0) {
      body.context = context
    }
    return body
  }

  return { lastStrategies, applyReply, buildBody }
}
