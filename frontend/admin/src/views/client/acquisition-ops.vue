<template>
  <YdPage title="获客作战台" subtitle="谁在跟 · 货 · 物流 · 联系 · 交代 · 付款" surface="elevated">
    <template #actions>
      <a-space>
        <a-button type="primary" @click="showPreview = true">智能拆解预览</a-button>
        <a-button @click="reloadTips">刷新提醒</a-button>
      </a-space>
    </template>

    <div class="acq-ops space-y-4">
      <!-- 进线 / 选客户 -->
      <a-card size="small" title="1. 找到客户 / 进线">
        <div class="grid gap-3 md:grid-cols-4">
          <a-input v-model:value="form.inquiry_id" placeholder="询盘编号（如 INQ-001）" allow-clear />
          <a-input v-model:value="form.country" placeholder="国家二字码（如 SA / IN）" allow-clear />
          <a-select v-model:value="form.grade" placeholder="客户好坏（可选）" allow-clear style="width: 100%">
            <a-select-option :value="90">A · 深跟</a-select-option>
            <a-select-option :value="70">B · 标准跟</a-select-option>
            <a-select-option :value="50">C · 低成本</a-select-option>
            <a-select-option :value="20">D · 谨慎</a-select-option>
          </a-select>
          <a-input v-model:value="form.owner_user_id" placeholder="谁来跟（业务员）" allow-clear />
        </div>
        <div class="mt-3 grid gap-3 md:grid-cols-2">
          <a-textarea
            v-model:value="form.message"
            :rows="2"
            placeholder="客户说了什么？（原样贴进来即可）"
          />
          <div class="flex flex-col gap-2">
            <a-button type="primary" :loading="loading" @click="onIngestReply">
              客户回复 → 建卡并记跟进
            </a-button>
            <a-button :loading="loading" @click="onLoadCard">打开跟单卡</a-button>
            <a-button :loading="translateLoading" @click="onTranslate">翻译成中文</a-button>
          </div>
        </div>
        <a-alert v-if="wallet" class="mt-3" :type="wallet.hard_block_enabled ? 'error' : 'info'" show-icon
          :message="wallet.message || '计费状态'" />
        <a-alert
          v-if="translateResult"
          class="mt-3"
          :type="translateResult.degraded ? 'warning' : 'success'"
          show-icon
          :message="`译文（${translateResult.provider}${translateResult.degraded ? ' · 降级' : ''}）`"
          :description="translateResult.translated"
        />
        <a-alert
          v-if="intentAnalysis"
          class="mt-3"
          :type="intentAnalysis.intent === 'reject_competitor' ? 'error' : 'info'"
          show-icon
          :message="`意图判断：${INTENT_LABELS[intentAnalysis.intent] || intentAnalysis.intent}（${intentAnalysis.confidence}）`"
          :description="`${intentAnalysis.reason} ｜ 建议阶段：${intentAnalysis.stage_suggestion} ｜ 下一步：${intentAnalysis.next_action}${intentAnalysis.talk_track ? ' ｜ 话术：' + intentAnalysis.talk_track : ''}`"
        />
        <a-alert v-if="alert" class="mt-3" :type="alertType" show-icon :message="alert" />
      </a-card>

      <a-card v-if="channels && channels.channels.length" size="small" title="获客渠道（红标=演示/未开通）">
        <div class="flex flex-wrap gap-2">
          <a-tag v-for="ch in channels.channels" :key="ch.id" :color="ch.is_mock ? 'error' : 'success'">
            {{ ch.name }}{{ ch.is_mock ? ' · 演示' : ' · 可用' }}
          </a-tag>
        </div>
        <div class="text-xs text-gray-500 mt-1">{{ channels.hint }}</div>
      </a-card>

      <!-- 今日待办 SLA -->
      <a-card size="small" title="今日待办（先逾期，后将到期）">
        <div class="flex items-center gap-2 mb-2">
          <a-tag v-if="followups" color="processing">共 {{ followups.total }}</a-tag>
          <a-tag v-if="followups && followups.overdue_count" color="error">逾期 {{ followups.overdue_count }}</a-tag>
          <a-button size="small" :loading="followupLoading" @click="loadFollowups">刷新待办</a-button>
        </div>
        <div v-if="!followups || !followups.items.length" class="text-gray-400 text-sm py-2">
          暂无待办。有客户回复或记录跟进后会出现在这里。
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="item in followups.items.slice(0, 8)"
            :key="item.inquiry_id"
            class="acq-follow"
            @click="openInquiry(item.inquiry_id)"
          >
            <div class="acq-follow-top">
              <b>{{ item.buyer_display || item.inquiry_id }}</b>
              <a-tag :color="item.sla.overdue ? 'error' : item.sla.sla === 'due' ? 'warning' : 'default'">
                {{ item.sla.overdue ? '逾期' : item.sla.sla === 'due' ? '将到期' : '待安排' }}
              </a-tag>
              <a-tag v-if="item.buyer_grade">{{ item.buyer_grade }}级</a-tag>
            </div>
            <div class="text-sm text-gray-600">{{ item.next_action || item.last_summary || '—' }}</div>
            <div class="text-xs text-gray-400">{{ item.sla.display }}</div>
          </div>
        </div>
      </a-card>

      <!-- Playbook 提醒 -->
      <a-card v-if="tips.length" size="small" title="2. 系统提醒（怎么聊）">
        <a-alert type="info" show-icon message="进线作战提示">
          <template #description>
            <ul class="acq-tips">
              <li v-for="(t, i) in tips" :key="i">{{ t }}</li>
            </ul>
          </template>
        </a-alert>
      </a-card>

      <!-- 跟单卡六组 -->
      <a-card size="small" title="3. 跟单作战卡（一眼看懂）">
        <div v-if="!card" class="text-center text-gray-400 py-8">
          还没有卡片。请在上方填询盘编号，点「客户回复 → 建卡」或「打开跟单卡」。
        </div>
        <template v-else>
          <!-- P1-4 评分大字常驻 -->
          <div class="acq-score-bar">
            <div class="acq-score-letter" :class="`g-${(scoreDisplay.grade || '-').toLowerCase()}`">
              {{ scoreDisplay.grade || '-' }}
            </div>
            <div class="acq-score-meta">
              <div class="acq-score-reason">{{ scoreDisplay.reason }}</div>
              <div class="acq-score-action">{{ scoreDisplay.action }}</div>
              <div v-if="card.buyer_display" class="text-gray-700 text-sm mt-1">{{ card.buyer_display }}</div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <a-tag color="processing">{{ card.stage || '-' }}</a-tag>
              <a-tag v-if="card.buyer_grade" :color="gradeColor">{{ card.buyer_grade }}级</a-tag>
            </div>
          </div>

          <!-- P1-2 履约节点 + 提醒 -->
          <div v-if="fulfillment && fulfillment.nodes && fulfillment.nodes.length" class="mt-3">
            <div class="font-semibold mb-1">报价 / PI / 收款节点</div>
            <div class="acq-nodes">
              <div
                v-for="n in fulfillment.nodes"
                :key="n.key"
                class="acq-node"
                :class="`st-${n.status}`"
              >
                <div class="acq-node-label">{{ n.label }}</div>
                <div class="acq-node-status">{{ n.status_label }}</div>
                <div v-if="n.ref" class="acq-node-ref">{{ n.ref }}</div>
              </div>
            </div>
            <div v-if="fulfillment.reminders && fulfillment.reminders.length" class="mt-2 space-y-1">
              <a-alert
                v-for="(r, i) in fulfillment.reminders.slice(0, 4)"
                :key="i"
                :type="r.status === 'overdue' ? 'error' : 'warning'"
                show-icon
                :message="r.display"
              />
            </div>
            <div class="mt-2 grid gap-2 md:grid-cols-4">
              <a-select v-model:value="fulForm.key" size="small" style="width: 100%">
                <a-select-option value="quote">报价</a-select-option>
                <a-select-option value="pi">形式发票PI</a-select-option>
                <a-select-option value="deposit">定金</a-select-option>
                <a-select-option value="balance">尾款</a-select-option>
              </a-select>
              <a-select v-model:value="fulForm.status" size="small" style="width: 100%">
                <a-select-option value="pending">未开始</a-select-option>
                <a-select-option value="active">进行中</a-select-option>
                <a-select-option value="done">已完成</a-select-option>
                <a-select-option value="overdue">已逾期</a-select-option>
                <a-select-option value="skipped">已跳过</a-select-option>
              </a-select>
              <a-input v-model:value="fulForm.ref" size="small" placeholder="PI号等（可空）" />
              <a-button size="small" type="primary" :loading="loading" @click="onFulfillment">保存节点</a-button>
            </div>
          </div>

          <div class="acq-grid mt-3">
            <div v-for="(val, key) in summary" :key="key" class="acq-cell">
              <div class="acq-label">{{ key }}</div>
              <div class="acq-value">{{ val || '—' }}</div>
            </div>
          </div>

          <!-- P1-6 千人千面背调闸 -->
          <div v-if="researchGate" class="mt-3">
            <a-alert
              :type="researchGate.personalized_allowed ? 'success' : 'warning'"
              show-icon
              :message="`开发信个性化：${researchGate.personalized_allowed ? '允许' : '禁止（先背调）'} · ${researchGate.research_level_label}`"
              :description="researchGate.reason"
            />
            <div class="mt-2 flex flex-wrap gap-2 items-center">
              <a-select v-model:value="researchForm.level" size="small" style="width: 180px">
                <a-select-option value="none">未背调</a-select-option>
                <a-select-option value="basic">基础信息</a-select-option>
                <a-select-option value="osint">OSINT背调</a-select-option>
                <a-select-option value="full">完整背调</a-select-option>
              </a-select>
              <a-button size="small" :loading="loading" @click="onResearch">登记背调深度</a-button>
              <span class="text-xs text-gray-500">{{ researchGate.next_step }}</span>
            </div>
          </div>

          <a-alert
            v-if="card.playbook_tips && card.playbook_tips.length"
            class="mt-3"
            type="warning"
            show-icon
            message="注意"
          >
            <template #description>
              <ul class="acq-tips">
                <li v-for="(t, i) in card.playbook_tips" :key="i">{{ t }}</li>
              </ul>
            </template>
          </a-alert>

          <div class="mt-4 grid gap-3 md:grid-cols-2">
            <div>
              <div class="font-semibold mb-1">记一笔跟进</div>
              <a-textarea v-model:value="touch.summary" :rows="2" placeholder="例如：已读未回 / 已发报价 / 要求 CIF 吉达" />
              <a-input v-model:value="touch.next_action" class="mt-2" placeholder="下一步做什么" />
              <a-button class="mt-2" type="primary" :loading="loading" @click="onTouch">保存跟进</a-button>
            </div>
            <div>
              <div class="font-semibold mb-1">交代 / 备注</div>
              <a-textarea v-model:value="note.body" :rows="2" placeholder="客户要求、承诺事项…" />
              <a-button class="mt-2" :loading="loading" @click="onNote">添加备注</a-button>
              <div class="mt-3 font-semibold mb-1">流失原因（聊跑了）</div>
              <a-select
                v-model:value="loss.reasons"
                mode="multiple"
                placeholder="可多选"
                style="width: 100%"
                :options="lossOptions"
              />
              <a-input v-model:value="loss.note" class="mt-2" placeholder="补充说明（可空）" />
              <a-button class="mt-2" danger :loading="loading" @click="onLoss">登记流失</a-button>
              <div class="mt-3 font-semibold mb-1">成交（赢单）</div>
              <a-input v-model:value="win.amount" size="small" placeholder="成交金额" />
              <a-input v-model:value="win.note" size="small" class="mt-1" placeholder="赢的原因/备注" />
              <a-button class="mt-2" type="primary" :loading="loading" @click="onWin">登记成交</a-button>
            </div>
          </div>

          <!-- P1-5 样品流程 -->
          <div class="mt-4">
            <div class="font-semibold mb-1">样品寄样（防黑洞）</div>
            <div v-if="sampleView" class="text-sm text-gray-700 mb-2">
              当前：<b>{{ sampleView.label }}</b>
              <span v-if="sampleView.fee_status"> · 费用{{ sampleView.fee_status }}</span>
              <span v-if="sampleView.tracking_no"> · 单号 {{ sampleView.tracking_no }}</span>
              <div class="text-xs text-gray-500 mt-1">{{ sampleView.next_action }}</div>
              <a-alert
                v-if="sampleView.fee_hole_risk"
                class="mt-2"
                type="error"
                show-icon
                message="样品已寄但费用未结，请催收或改为免费并备注"
              />
            </div>
            <div class="grid gap-2 md:grid-cols-4">
              <a-select v-model:value="sampleForm.status" size="small" style="width: 100%">
                <a-select-option value="requested">客户要样品</a-select-option>
                <a-select-option value="confirmed">规格/费用确认</a-select-option>
                <a-select-option value="preparing">备样中</a-select-option>
                <a-select-option value="shipped">已寄出</a-select-option>
                <a-select-option value="delivered">已签收</a-select-option>
                <a-select-option value="fee_collected">样品费已收</a-select-option>
                <a-select-option value="waived">免费寄样</a-select-option>
                <a-select-option value="rejected">已取消</a-select-option>
              </a-select>
              <a-input v-model:value="sampleForm.product" size="small" placeholder="样品品名" />
              <a-input v-model:value="sampleForm.tracking_no" size="small" placeholder="快递单号" />
              <a-button size="small" type="primary" :loading="loading" @click="onSample">保存样品</a-button>
            </div>
            <div class="grid gap-2 md:grid-cols-3 mt-2">
              <a-input v-model:value="sampleForm.fee_amount" size="small" placeholder="样品费金额" />
              <a-select v-model:value="sampleForm.fee_status" size="small" style="width: 100%">
                <a-select-option value="unbilled">未开费</a-select-option>
                <a-select-option value="billed">已告知费用</a-select-option>
                <a-select-option value="paid">费用已收</a-select-option>
                <a-select-option value="waived">免费</a-select-option>
              </a-select>
              <a-input v-model:value="sampleForm.note" size="small" placeholder="备注（运费谁出等）" />
            </div>
          </div>

          <div v-if="card.notes && card.notes.length" class="mt-4">
            <div class="font-semibold mb-1">交代记录</div>
            <div v-for="(n, i) in card.notes" :key="i" class="acq-note">
              <b>{{ n.author }}</b> · {{ n.at }}：{{ n.body }}
            </div>
          </div>

          <div class="mt-4">
            <div class="font-semibold mb-1">收款 / 物流 / 货（可编辑）</div>
            <div class="grid gap-2 md:grid-cols-3">
              <div>
                <div class="text-xs text-gray-500 mb-1">收款</div>
                <a-input v-model:value="pay.pi_no" placeholder="PI 号" size="small" />
                <a-input v-model:value="pay.deposit_amount" placeholder="定金金额" size="small" class="mt-1" />
                <a-input v-model:value="pay.deposit_paid_at" placeholder="定金到账日" size="small" class="mt-1" />
                <a-input v-model:value="pay.balance_status" placeholder="尾款 pending/paid/overdue" size="small" class="mt-1" />
                <a-button size="small" type="primary" class="mt-1" :loading="loading" @click="onPay">保存收款</a-button>
              </div>
              <div>
                <div class="text-xs text-gray-500 mb-1">物流</div>
                <a-input v-model:value="logi.carrier" placeholder="船公司/货代" size="small" />
                <a-input v-model:value="logi.bl_no" placeholder="提单号" size="small" class="mt-1" />
                <a-input v-model:value="logi.etd" placeholder="ETD" size="small" class="mt-1" />
                <a-input v-model:value="logi.eta" placeholder="ETA" size="small" class="mt-1" />
                <a-button size="small" type="primary" class="mt-1" :loading="loading" @click="onLogi">保存物流</a-button>
              </div>
              <div>
                <div class="text-xs text-gray-500 mb-1">发什么货</div>
                <a-input v-model:value="goods.name" placeholder="品名" size="small" />
                <a-input v-model:value="goods.spec" placeholder="规格" size="small" class="mt-1" />
                <a-input v-model:value="goods.qty" placeholder="数量" size="small" class="mt-1" />
                <a-input v-model:value="goods.unit" placeholder="单位" size="small" class="mt-1" />
                <a-button size="small" type="primary" class="mt-1" :loading="loading" @click="onGoods">保存货物</a-button>
              </div>
            </div>
          </div>
        </template>
      </a-card>

      <!-- P1-3 流失原因报表 -->
      <a-card size="small" title="4. 流失原因报表（为什么聊跑了）">
        <div class="flex items-center gap-2 mb-2">
          <a-tag v-if="lossReport" color="error">流失 {{ lossReport.total_lost }} 单</a-tag>
          <a-button size="small" :loading="lossLoading" @click="loadLossReport">刷新报表</a-button>
          <a-button size="small" @click="showDict = true">编排词典</a-button>
        </div>
        <div v-if="!lossReport || !lossReport.distribution.length" class="text-gray-400 text-sm py-2">
          {{ lossReport?.plain_summary || '暂无流失记录。登记流失后这里会出分布。' }}
        </div>
        <template v-else>
          <div class="text-sm text-gray-700 mb-2">{{ lossReport.plain_summary }}</div>
          <div v-for="d in lossReport.distribution" :key="d.reason" class="acq-loss-row">
            <div class="acq-loss-reason">
              <b>{{ d.reason }}</b>
              <span class="text-gray-500">· {{ d.count }} 次（{{ d.percent }}%）</span>
            </div>
            <div class="acq-loss-bar">
              <div class="acq-loss-fill" :style="{ width: `${Math.min(100, d.percent)}%` }" />
            </div>
            <div class="text-xs text-gray-500">{{ d.hint }}</div>
          </div>
        </template>
      </a-card>

      <!-- P1-7/P1-8 内容归因 + IP 槽位 -->
      <a-card size="small" title="5. 内容归因 / IP槽位（只读）">
        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <div class="font-semibold mb-1">内容带来多少询盘</div>
            <div class="text-sm text-gray-700 mb-2">{{ attrReport?.plain_summary || '暂无数据' }}</div>
            <div v-if="attrReport && attrReport.items.length">
              <div v-for="it in attrReport.items.slice(0, 5)" :key="it.content_id" class="text-xs text-gray-600 mb-1">
                {{ it.content_title || it.content_id }} · 询盘 {{ it.inquiry_count }}
              </div>
            </div>
            <div class="mt-2 flex gap-2">
              <a-input v-model:value="attrForm.content_id" size="small" placeholder="内容ID" />
              <a-input v-model:value="attrForm.inquiry_id" size="small" placeholder="询盘号" />
              <a-button size="small" @click="onLinkContent">挂来源</a-button>
            </div>
          </div>
          <div>
            <div class="font-semibold mb-1">IP / 指纹槽位</div>
            <div class="text-sm text-gray-700 mb-2">{{ ipSlots?.plain_summary || '暂无数据' }}</div>
            <div v-if="ipSlots">
              <div v-for="s in ipSlots.slots" :key="s.slot_id" class="text-xs text-gray-600 mb-1">
                {{ s.label }} · <a-tag :color="s.status === 'unknown' ? 'default' : 'success'" class="ml-1">{{ s.status_label }}</a-tag>
              </div>
              <div class="text-xs text-gray-400 mt-1">{{ ipSlots.hint }}</div>
            </div>
          </div>
        </div>
      </a-card>

      <!-- P2 Win/Loss + Onboarding -->
      <a-card size="small" title="6. 成交/流失 · 开通五步">
        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <div class="font-semibold mb-1">成交 vs 流失</div>
            <div class="text-sm text-gray-700 mb-2">{{ winLoss?.plain_summary || '暂无数据' }}</div>
            <div class="flex gap-2 flex-wrap text-xs text-gray-600">
              <a-tag v-if="winLoss" color="success">成交 {{ winLoss.won_count }}</a-tag>
              <a-tag v-if="winLoss" color="error">流失 {{ winLoss.lost_count }}</a-tag>
            </div>
            <a-button size="small" class="mt-2" :loading="p2Loading" @click="loadP2">刷新</a-button>
          </div>
          <div>
            <div class="font-semibold mb-1">开通引导 {{ onboarding?.done_count || 0 }}/{{ onboarding?.total || 5 }}</div>
            <div class="text-sm text-gray-700 mb-2">{{ onboarding?.plain_summary || '暂无' }}</div>
            <div v-if="onboarding">
              <div v-for="s in onboarding.steps" :key="s.id" class="text-xs mb-1">
                <a-tag :color="s.done ? 'success' : 'default'">{{ s.status_label }}</a-tag>
                {{ s.title }} — {{ s.plain }}
              </div>
            </div>
          </div>
        </div>
      </a-card>

      <!-- P2-1/3 经验真源 + 权重建议 -->
      <a-card size="small" title="7. 经验真源 · 航道权重建议（人审）">
        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <div class="font-semibold mb-1">经验真源</div>
            <div class="text-sm text-gray-700">{{ expSource?.plain_summary || '—' }}</div>
            <div class="text-xs text-gray-500 mt-1">
              主源：{{ expSource?.primary_source || 'evolution_pg' }}
              <a-tag v-if="expSource?.json_fallback_used" color="warning" class="ml-1">JSON兜底</a-tag>
            </div>
          </div>
          <div>
            <div class="font-semibold mb-1">航道权重建议 {{ weightView?.plain_summary || '' }}</div>
            <div v-if="weightView && weightView.suggestions">
              <div v-for="s in weightView.suggestions.slice(0, 6)" :key="s.intent" class="text-xs mb-1">
                {{ s.label }}：{{ s.base_weight }} → <b>{{ s.suggested_weight }}</b>
                <a-tag v-if="s.status === 'insufficient'" class="ml-1">样本不足</a-tag>
                <a-tag v-else-if="s.delta !== 0" :color="s.delta > 0 ? 'success' : 'warning'" class="ml-1">
                  {{ s.delta > 0 ? '建议上调' : '建议下调' }}
                </a-tag>
                <div class="text-gray-400" v-if="s.reasons && s.reasons[0]">{{ s.reasons[0] }}</div>
              </div>
            </div>
            <div class="text-xs text-gray-400 mt-1">只出建议，不自动改调度。</div>
          </div>
        </div>
      </a-card>

      <!-- P2-6/7/8/10 账单 · 撞单 · 手机待办 · 旺财补救 -->
      <a-card size="small" title="8. 账单说明 · 撞单 · 手机待办 · 建站卡壳补救">
        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <div class="font-semibold mb-1">账单（大白话）</div>
            <div class="text-sm text-gray-700 mb-1">{{ billing?.plain_summary || '—' }}</div>
            <div v-if="billing && billing.items.length" class="acq-bill-list">
              <div v-for="(b, i) in billing.items.slice(0, 6)" :key="i" class="text-xs text-gray-600">
                {{ b.plain }}
              </div>
            </div>
            <div class="font-semibold mt-3 mb-1">撞单规则</div>
            <div class="text-xs text-gray-600">{{ collision?.rule || '无主可认领；有主须确认交接并留痕。' }}</div>
            <div class="text-xs text-gray-500">{{ collision?.plain_summary || '' }}</div>
          </div>
          <div>
            <div class="font-semibold mb-1">手机今日待办</div>
            <div class="text-sm text-gray-700">{{ mobileBrief?.brief || '—' }}</div>
            <div v-if="mobileBrief && mobileBrief.top.length" class="text-xs text-gray-600 mt-1">
              <div v-for="m in mobileBrief.top" :key="m.inquiry_id" class="acq-mobile-item">
                <b>{{ m.display }}</b> · {{ m.next }} · {{ m.sla }}
              </div>
            </div>
            <div class="font-semibold mt-3 mb-1">建站卡壳 → 补救</div>
            <div class="text-sm text-gray-700">{{ rescue?.plain_summary || '—' }}</div>
            <div v-if="rescue?.blocked && rescue.next_steps?.length" class="text-xs text-gray-600 mt-1">
              <div v-for="(s, i) in rescue.next_steps" :key="i">· {{ s }}</div>
              <div class="text-gray-400 mt-1" v-if="rescue.repeated">已抑制重复派发</div>
              <div v-else-if="rescue.allow_dispatch" class="mt-1">
                建议意图：<b>{{ rescue.suggested_intent }}</b>（可回上方智能拆解派发）
              </div>
            </div>
            <div class="font-semibold mt-3 mb-1">NPS / 挽回</div>
            <div class="text-sm text-gray-700">{{ npsView?.plain_summary || '—' }}</div>
            <div v-if="npsView?.rescue_actions?.length" class="text-xs text-gray-600 mt-1">
              <div v-for="(a, i) in npsView.rescue_actions" :key="i">· {{ a }}</div>
            </div>
          </div>
        </div>
      </a-card>

      <!-- P3 合规闸门 -->
      <a-card size="small" title="9. 报价有效期 · 交期门禁 · 退订 · 付款风险">
        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <div class="font-semibold mb-1">报价有效期</div>
            <div class="text-sm text-gray-700">{{ cardQuote?.plain || '打开跟单卡后显示' }}</div>
            <div class="flex gap-2 mt-2">
              <a-input v-model:value="p3Form.quote_at" size="small" placeholder="报价日 YYYY-MM-DD" />
              <a-input v-model:value="p3Form.valid_days" size="small" placeholder="有效天数" style="width:90px" />
              <a-button size="small" @click="onQuoteValidity">登记报价</a-button>
            </div>
            <div class="font-semibold mt-3 mb-1">交期门禁</div>
            <div class="text-sm text-gray-700">{{ cardLead?.plain || '无证据不得保证交期' }}</div>
            <div class="flex flex-wrap gap-2 mt-2">
              <a-input v-model:value="p3Form.leadtime_days" size="small" placeholder="承诺天数" style="width:90px" />
              <a-checkbox v-model:checked="p3Form.has_inv">有现货</a-checkbox>
              <a-checkbox v-model:checked="p3Form.has_cap">有产能</a-checkbox>
              <a-button size="small" @click="onLeadtime">检查交期</a-button>
            </div>
          </div>
          <div>
            <div class="font-semibold mb-1">退订 / 抑制</div>
            <div class="text-sm text-gray-700">{{ suppression?.plain_summary || '—' }}</div>
            <div class="flex gap-2 mt-2">
              <a-input v-model:value="p3Form.sup_email" size="small" placeholder="邮箱" />
              <a-button size="small" danger @click="onSuppress">加入抑制</a-button>
            </div>
            <div class="font-semibold mt-3 mb-1">付款风险（自动 PI 闸）</div>
            <div class="text-sm text-gray-700">{{ payRisk?.plain || '—' }}</div>
            <div class="text-xs text-gray-500" v-if="payRisk">
              等级 {{ payRisk.level }} · 自动PI {{ payRisk.auto_pi_allowed ? '允许' : '禁止' }}
              <div v-if="payRisk.reasons?.length">· {{ payRisk.reasons[0] }}</div>
            </div>
            <div class="flex gap-2 mt-2">
              <a-input v-model:value="p3Form.risk_country" size="small" placeholder="国家" style="width:80px" />
              <a-button size="small" @click="onPayRisk(true)">检查自动PI</a-button>
            </div>
          </div>
        </div>
      </a-card>

      <!-- P3-4/8 知识队列 + 制裁重扫 -->
      <a-card size="small" title="10. 必读知识 · 名单重扫">
        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <div class="font-semibold mb-1">合规/知识待读</div>
            <div class="text-sm text-gray-700 mb-2">{{ know?.plain_summary || '—' }}</div>
            <div v-if="know?.next_item" class="text-xs text-gray-600 mb-2">
              下一题：<b>{{ know.next_item.title }}</b>
              <div class="text-gray-500">{{ know.next_item.plain }}</div>
            </div>
            <div v-if="know?.items?.length" class="acq-know-list">
              <div v-for="k in know.items" :key="k.id" class="acq-know-item">
                <a-tag :color="k.done ? 'success' : 'default'">{{ k.done ? '已读' : '待读' }}</a-tag>
                <span class="text-xs">{{ k.title }}</span>
                <a-button v-if="!k.done" size="small" type="link" @click="onKnowDone(k.id)">标记已读</a-button>
              </div>
            </div>
          </div>
          <div>
            <div class="font-semibold mb-1">名单重扫（制裁/风险）</div>
            <div class="text-sm text-gray-700">{{ riskRescan?.plain_summary || '—' }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ riskRescan?.source_plain }}</div>
            <div v-if="riskRescan?.items?.length" class="mt-2">
              <div v-for="r in riskRescan.items.slice(0, 5)" :key="r.inquiry_id" class="acq-know-item">
                <a-tag :color="r.due ? 'warning' : 'success'">{{ r.status_label }}</a-tag>
                <span class="text-xs">{{ r.plain }}</span>
                <a-button v-if="r.due && form.inquiry_id === r.inquiry_id" size="small" type="link" @click="onMarkRisk">已重扫</a-button>
              </div>
            </div>
            <a-button size="small" class="mt-2" :loading="p2Loading" @click="loadP2">刷新</a-button>
          </div>
        </div>
      </a-card>
    </div>

    <!-- 智能拆解预览 -->
    <a-modal v-model:open="showPreview" title="智能调度预览（先看懂再干活）" width="720px" :footer="null">
      <div class="space-y-3">
        <a-alert type="info" show-icon message="输入想干什么，系统会拆成步骤。外发动作需人工确认，不会偷偷发。" />
        <a-select v-model:value="preview.intent" style="width: 100%">
          <a-select-option value="find_leads">找客户 + 写开发信</a-select-option>
          <a-select-option value="fulfillment">履约：询盘→PI→物流</a-select-option>
          <a-select-option value="whatsapp">社媒 / WhatsApp 拓客</a-select-option>
          <a-select-option value="generate_site">建站 + 内容分发</a-select-option>
          <a-select-option value="deep_research">市场调研</a-select-option>
        </a-select>
        <a-input v-model:value="preview.keyword" placeholder="关键词（如 rockwool / 石膏板）" />
        <a-input v-model:value="preview.country" placeholder="国家（如 SA / IN）" />
        <a-button type="primary" :loading="loading" block @click="onPreview">拆解给我看</a-button>
        <a-button
          v-if="previewResult"
          type="primary"
          :loading="dispatchLoading"
          danger
          block
          @click="onDispatch"
        >
          确认派发（写入任务图并调度）
        </a-button>
        <a-alert v-if="dispatchResult" class="mt-2" :type="dispatchResult.dispatched ? 'success' : 'info'" show-icon
          :message="dispatchResult.dispatched ? '已派发' : '已拆解（未派发）'"
          :description="`${dispatchResult.persistence_note || ''} plan=${dispatchResult.plan_id} source=${dispatchResult.graph_source}`" />
        <div v-if="previewResult">
          <div class="mb-2 text-sm text-gray-600">
            来源：{{ previewResult.source }} ｜ 策略：{{ previewResult.strategy }}
          </div>
          <a-table
            :data-source="previewResult.nodes"
            :columns="nodeCols"
            row-key="id"
            size="small"
            :pagination="false"
          />
          <a-alert
            v-if="previewResult.approval_required?.length"
            class="mt-2"
            type="warning"
            show-icon
            :message="`需要人工确认：${previewResult.approval_required.join('、')}`"
          />
        </div>
      </div>
    </a-modal>

    <!-- P1-9 编排词典 -->
    <a-modal v-model:open="showDict" title="编排词典 v1（已验证航道）" width="760px" :footer="null">
      <div class="space-y-3">
        <a-alert type="info" show-icon :message="dictSummary || '已验证航道词典'" />
        <div v-for="r in dictRoutes" :key="r.id" class="acq-dict-item">
          <div class="font-semibold">{{ r.name }} <span class="text-gray-400 text-xs">{{ r.intent }}</span></div>
          <div class="text-sm text-gray-700">{{ r.order_label }}</div>
          <div class="text-xs text-gray-500">{{ r.plain }}</div>
          <div class="text-xs text-gray-400 mt-1">
            节点：{{ r.nodes.join(' → ') }}
            <span v-if="r.human_review?.length"> ｜ 人审：{{ r.human_review.join('、') }}</span>
          </div>
        </div>
      </div>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
/**
 * 获客作战台 —— 唯一目标：智能获客，傻子都行。
 * 硬锁：仅挂在 /client/* 租户壳；不新建登录页；主色走全局令牌。
 */
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import YdPage from '@/components/youding/YdPage.vue'
import {
  addOpsCardNote,
  dispatchAcquisition,
  getLossReport,
  getOpsCard,
  getOrchestrationDictionary,
  getContentAttribution,
  getExperienceSource,
  getBillingExplain,
  getCollisionReport,
  getMobileFollowupBrief,
  getNpsRescue,
  getWangcaiRescue,
  getIpSlots,
  getOnboarding,
  getSuppressionList,
  getPaymentRisk,
  getKnowledgeQueue,
  getRiskRescan,
  markKnowledge,
  markRiskScan,
  updateQuoteValidity,
  updateLeadtime,
  addSuppression,
  getTemplateWeights,
  getWalletStatus,
  getWinLoss,
  claimOpsInquiry,
  ingestReply,
  linkContentInquiry,
  recordOpsCardWin,
  listPlaybooks,
  listAcquisitionChannels,
  listFollowups,
  materializeOpsCard,
  previewIntent,
  recordOpsCardLoss,
  touchOpsCard,
  translateAcquisition,
  updateOpsCardFulfillment,
  updateOpsCardGoods,
  updateOpsCardLogistics,
  updateOpsCardPayment,
  updateOpsCardResearch,
  updateOpsCardSample,
  type IntentPreviewResponse,
  type LossReportResponse,
  type OpsCardPayload,
  type OpsCardResponse,
  type OpsCardSummary,
  type OrchestrationDictionaryResponse,
  type ResearchGateView,
  type SampleView,
  type ScoreDisplay,
} from '@/api/acquisition'
import { apiGet } from '@/utils/api'

const loading = ref(false)
const alert = ref('')
const alertType = ref<'success' | 'error' | 'info' | 'warning'>('info')
const card = ref<OpsCardPayload | null>(null)
const summary = ref<Partial<OpsCardSummary>>({})
const tips = ref<string[]>([])
const tenantId = ref('demo')

/** 回复意图展示标签（与 backend intent_classifier 枚举对齐） */
const INTENT_LABELS: Record<string, string> = {
  price_haggling: '压价议价',
  request_quote: '索取报价',
  request_sample: '索要样品',
  payment_discuss: '付款谈判',
  cert_insist: '认证要求',
  quantity_port: '数量/港口',
  reject_competitor: '已选同行/流失风险',
  generic_interest: '泛意向',
  unknown: '未识别',
}
const intentAnalysis = ref<{
  intent: string
  stage_suggestion: string
  confidence: number
  reason: string
  next_action: string
  talk_track: string
} | null>(null)

const followupLoading = ref(false)
const channels = ref<Awaited<ReturnType<typeof listAcquisitionChannels>> | null>(null)

async function loadChannels() {
  try { channels.value = await listAcquisitionChannels() } catch { channels.value = null }
}
const followups = ref<Awaited<ReturnType<typeof listFollowups>> | null>(null)

const pay = reactive({
  pi_no: '',
  deposit_amount: '',
  deposit_paid_at: '',
  balance_status: 'pending',
})
const logi = reactive({ carrier: '', bl_no: '', etd: '', eta: '' })
const goods = reactive({ name: '', spec: '', qty: '', unit: 'pcs' })

// P1 批量状态
const scoreDisplay = ref<ScoreDisplay>({ grade: '-', reason: '尚未评分', score: null, action: '先观察或补信息', large: false })
const fulfillment = ref<OpsCardResponse['fulfillment']>(null)
const sampleView = ref<SampleView | null>(null)
const researchGate = ref<ResearchGateView | null>(null)
const fulForm = reactive({ key: 'quote', status: 'pending', ref: '' })
const sampleForm = reactive({
  status: 'requested',
  product: '',
  tracking_no: '',
  fee_amount: '',
  fee_status: 'unbilled',
  note: '',
})
const researchForm = reactive({ level: 'none' })
const lossReport = ref<LossReportResponse | null>(null)
const lossLoading = ref(false)
const showDict = ref(false)
const dictRoutes = ref<OrchestrationDictionaryResponse['routes']>([])
const dictSummary = ref('')
const attrReport = ref<Awaited<ReturnType<typeof getContentAttribution>> | null>(null)
const ipSlots = ref<Awaited<ReturnType<typeof getIpSlots>> | null>(null)
const attrForm = reactive({ content_id: '', inquiry_id: '' })

async function loadGrowthOps() {
  try {
    const tenant = await resolveTenantId()
    attrReport.value = await getContentAttribution(tenant)
  } catch { attrReport.value = null }
  try {
    const tenant = await resolveTenantId()
    ipSlots.value = await getIpSlots(tenant)
  } catch { ipSlots.value = null }
}

async function onLinkContent() {
  if (!attrForm.content_id || !attrForm.inquiry_id) {
    message.warning('请填内容ID和询盘号')
    return
  }
  try {
    const tenant = await resolveTenantId()
    await linkContentInquiry({
      content_id: attrForm.content_id,
      inquiry_id: attrForm.inquiry_id,
      tenant_id: tenant,
    })
    setAlert('已把询盘挂到该内容来源。', 'success')
    void loadGrowthOps()
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  }
}

function applyCard(resp: OpsCardResponse | null) {
  if (!resp) return
  card.value = resp.card || null
  summary.value = resp.summary || {}
  if ((resp as any).quote_validity) cardQuote.value = (resp as any).quote_validity
  if ((resp as any).leadtime_gate) cardLead.value = (resp as any).leadtime_gate
  if ((resp as any).payment_risk) payRisk.value = (resp as any).payment_risk
  if (resp.score_display) {
    scoreDisplay.value = resp.score_display
  } else if (resp.card) {
    scoreDisplay.value = {
      grade: resp.card.buyer_grade || '-',
      reason: resp.card.buyer_grade_reason || '尚未评分',
      score: (resp.card.buyer_score as number) || null,
      action: '先观察或补信息',
      large: !!resp.card.buyer_grade,
    }
  }
  fulfillment.value = resp.fulfillment || null
  sampleView.value = resp.sample || null
  researchGate.value = resp.research_gate || null
  if (resp.sample) {
    sampleForm.status = resp.sample.status && resp.sample.status !== 'none' ? resp.sample.status : 'requested'
    sampleForm.product = resp.sample.product || sampleForm.product
    sampleForm.tracking_no = resp.sample.tracking_no || sampleForm.tracking_no
    sampleForm.fee_amount = String(resp.sample.fee_amount || sampleForm.fee_amount || '')
    sampleForm.fee_status = resp.sample.fee_status || sampleForm.fee_status
    sampleForm.note = resp.sample.note || sampleForm.note
  }
  if (resp.research_gate) {
    researchForm.level = resp.research_gate.research_level || 'none'
  }
  if (resp.card) {
    const payAny = resp.card.payment as Record<string, unknown> | undefined
    if (payAny) {
      pay.pi_no = String(payAny.pi_no || pay.pi_no || '')
      pay.deposit_amount = String(payAny.deposit_amount || pay.deposit_amount || '')
      pay.deposit_paid_at = String(payAny.deposit_paid_at || pay.deposit_paid_at || '')
      pay.balance_status = String(payAny.balance_status || pay.balance_status || 'pending')
    }
  }
}

async function onFulfillment() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  loading.value = true
  try {
    const resp = await updateOpsCardFulfillment(form.inquiry_id, {
      key: fulForm.key,
      status: fulForm.status,
      ref: fulForm.ref,
    })
    applyCard(resp)
    setAlert('节点状态已保存。', 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally { loading.value = false }
}

async function onSample() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  loading.value = true
  try {
    const resp = await updateOpsCardSample(form.inquiry_id, {
      status: sampleForm.status,
      product: sampleForm.product,
      tracking_no: sampleForm.tracking_no,
      fee_amount: Number(sampleForm.fee_amount) || 0,
      fee_status: sampleForm.fee_status,
      note: sampleForm.note,
    })
    applyCard(resp)
    setAlert('样品状态已保存。', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    setAlert(`样品保存失败：${msg}`, 'error')
  } finally { loading.value = false }
}

async function onResearch() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  loading.value = true
  try {
    const resp = await updateOpsCardResearch(form.inquiry_id, {
      research_level: researchForm.level,
      note: '',
    })
    applyCard(resp)
    setAlert('背调深度已登记。无背调禁止个性化开发信。', researchForm.level === 'none' ? 'warning' : 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally { loading.value = false }
}

async function loadLossReport() {
  lossLoading.value = true
  try {
    const tenant = await resolveTenantId()
    lossReport.value = await getLossReport(tenant)
  } catch {
    lossReport.value = null
  } finally {
    lossLoading.value = false
  }
}

async function loadDictionary() {
  try {
    const d = await getOrchestrationDictionary()
    dictRoutes.value = d.routes || []
    dictSummary.value = d.plain_summary || ''
  } catch {
    dictRoutes.value = []
    dictSummary.value = ''
  }
}

async function onPay() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  loading.value = true
  try {
    const resp = await updateOpsCardPayment(form.inquiry_id, {
      pi_no: pay.pi_no,
      deposit_amount: Number(pay.deposit_amount) || 0,
      deposit_paid_at: pay.deposit_paid_at,
      balance_status: pay.balance_status || 'pending',
    })
    applyCard(resp)
    setAlert('收款信息已保存。', 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally { loading.value = false }
}

async function onLogi() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  loading.value = true
  try {
    const resp = await updateOpsCardLogistics(form.inquiry_id, {
      carrier: logi.carrier,
      bl_no: logi.bl_no,
      etd: logi.etd,
      eta: logi.eta,
      milestone: logi.bl_no ? '已登记提单' : '',
    })
    applyCard(resp)
    setAlert('物流信息已保存。', 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally { loading.value = false }
}

async function onGoods() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  loading.value = true
  try {
    const resp = await updateOpsCardGoods(form.inquiry_id, {
      sku_lines: [{
        name: goods.name,
        spec: goods.spec,
        qty: Number(goods.qty) || 0,
        unit: goods.unit || 'pcs',
      }],
    })
    applyCard(resp)
    setAlert('货物信息已保存。', 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally { loading.value = false }
}

async function loadFollowups() {
  followupLoading.value = true
  try {
    const tenant = await resolveTenantId()
    followups.value = await listFollowups(tenant)
  } catch {
    followups.value = null
  } finally {
    followupLoading.value = false
  }
}

function openInquiry(id: string) {
  form.inquiry_id = id
  void onLoadCard()
}

async function resolveTenantId(): Promise<string> {
  if (tenantId.value && tenantId.value !== 'demo') return tenantId.value
  try {
    const dash = await apiGet<{ tenant_id?: string; tenant?: { id?: string } }>('/client/dashboard')
    const tid = dash?.tenant_id || dash?.tenant?.id
    if (tid) {
      tenantId.value = String(tid)
      return tenantId.value
    }
  } catch {
    /* 后端未起时保留 demo，演示仍可用；生产登录后应能取到真租户 */
  }
  return tenantId.value || 'demo'
}

const form = reactive({
  inquiry_id: '',
  country: '',
  grade: undefined as number | undefined,
  owner_user_id: '',
  message: '',
})

const touch = reactive({ summary: '', next_action: '' })
const note = reactive({ body: '' })
const loss = reactive({ reasons: [] as string[], note: '' })
const win = reactive({ amount: '', note: '' })
const winLoss = ref<Awaited<ReturnType<typeof getWinLoss>> | null>(null)
const onboarding = ref<Awaited<ReturnType<typeof getOnboarding>> | null>(null)
const p2Loading = ref(false)
const expSource = ref<Awaited<ReturnType<typeof getExperienceSource>> | null>(null)
const weightView = ref<Awaited<ReturnType<typeof getTemplateWeights>> | null>(null)
const billing = ref<Awaited<ReturnType<typeof getBillingExplain>> | null>(null)
const collision = ref<Awaited<ReturnType<typeof getCollisionReport>> | null>(null)
const mobileBrief = ref<Awaited<ReturnType<typeof getMobileFollowupBrief>> | null>(null)
const rescue = ref<Awaited<ReturnType<typeof getWangcaiRescue>> | null>(null)
const npsView = ref<Awaited<ReturnType<typeof getNpsRescue>> | null>(null)
const suppression = ref<Awaited<ReturnType<typeof getSuppressionList>> | null>(null)
const payRisk = ref<Awaited<ReturnType<typeof getPaymentRisk>> | null>(null)
const cardQuote = ref<Record<string, any> | null>(null)
const cardLead = ref<Record<string, any> | null>(null)
const know = ref<Awaited<ReturnType<typeof getKnowledgeQueue>> | null>(null)
const riskRescan = ref<Awaited<ReturnType<typeof getRiskRescan>> | null>(null)
const p3Form = reactive({
  quote_at: '',
  valid_days: '14',
  leadtime_days: '',
  has_inv: false,
  has_cap: false,
  sup_email: '',
  risk_country: 'IN',
})

async function onQuoteValidity() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  try {
    const resp = await updateQuoteValidity(form.inquiry_id, {
      quote_at: p3Form.quote_at,
      valid_days: Number(p3Form.valid_days) || 14,
    })
    applyCard(resp)
    cardQuote.value = (resp as any).quote_validity || null
    setAlert(cardQuote.value?.plain || '报价有效期已登记', 'info')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  }
}

async function onLeadtime() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  try {
    const resp = await updateLeadtime(form.inquiry_id, {
      promised_days: p3Form.leadtime_days ? Number(p3Form.leadtime_days) : undefined,
      has_inventory_evidence: p3Form.has_inv,
      has_capacity_evidence: p3Form.has_cap,
    })
    applyCard(resp)
    cardLead.value = (resp as any).leadtime_gate || null
    setAlert(cardLead.value?.plain || '交期检查完成', cardLead.value?.allowed ? 'success' : 'warning')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  }
}

async function onSuppress() {
  if (!p3Form.sup_email) { message.warning('请填邮箱'); return }
  try {
    const r = await addSuppression({ email: p3Form.sup_email, tenant_id: tenantId.value, reason: 'unsubscribe' })
    setAlert(r.message || '已加入抑制', 'warning')
    const tenant = await resolveTenantId()
    suppression.value = await getSuppressionList(tenant)
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  }
}

async function onPayRisk(auto = true) {
  try {
    payRisk.value = await getPaymentRisk({
      country: p3Form.risk_country,
      buyer_type: 'new',
      inquiry_id: form.inquiry_id,
      auto_pi: auto,
      deposit_ratio: 0,
    })
    setAlert(payRisk.value?.plain || '风险检查完成', payRisk.value?.auto_pi_allowed ? 'success' : 'warning')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  }
}

async function onKnowDone(id: string) {
  try {
    const r = await markKnowledge({ item_id: id, action: 'done', tenant_id: tenantId.value })
    setAlert(r.message || '已标记', 'success')
    const tenant = await resolveTenantId()
    know.value = await getKnowledgeQueue(tenant)
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  }
}

async function onMarkRisk() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  try {
    const r = await markRiskScan({
      inquiry_id: form.inquiry_id,
      result: 'unknown',
      source: 'manual',
      note: '人工复核（未接外部名单源）',
    })
    setAlert(r.message || '已登记重扫', 'success')
    const tenant = await resolveTenantId()
    riskRescan.value = await getRiskRescan(tenant)
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  }
}

async function loadP2() {
  p2Loading.value = true
  try {
    const tenant = await resolveTenantId()
    winLoss.value = await getWinLoss(tenant)
    onboarding.value = await getOnboarding(tenant, !!dispatchResult.value?.dispatched)
    expSource.value = await getExperienceSource(tenant)
    weightView.value = await getTemplateWeights(tenant)
    billing.value = await getBillingExplain(tenant)
    collision.value = await getCollisionReport(tenant)
    mobileBrief.value = await getMobileFollowupBrief(tenant)
    rescue.value = await getWangcaiRescue(tenant)
    npsView.value = await getNpsRescue(tenant)
    suppression.value = await getSuppressionList(tenant)
    know.value = await getKnowledgeQueue(tenant)
    riskRescan.value = await getRiskRescan(tenant)
  } catch {
    winLoss.value = null
  } finally {
    p2Loading.value = false
  }
}

async function onWin() {
  if (!form.inquiry_id) { message.warning('请先填写询盘编号'); return }
  loading.value = true
  try {
    const resp = await recordOpsCardWin(form.inquiry_id, {
      amount: Number(win.amount) || 0,
      currency: 'USD',
      note: win.note,
      reasons: win.note ? [win.note] : [],
    })
    applyCard(resp)
    if (resp.win_loss) winLoss.value = resp.win_loss
    setAlert('成交已登记，会写入经验环。', 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally { loading.value = false }
}

const lossOptions = [
  { label: '价格高', value: '价格高' },
  { label: '认证不够', value: '认证不够' },
  { label: '交期不合适', value: '交期不合适' },
  { label: '付款方式冲突', value: '付款方式冲突' },
  { label: '已选同行', value: '已选同行' },
  { label: '无回复/原因未知', value: '无回复' },
  { label: 'MOQ/规格不合', value: 'MOQ不合' },
  { label: '其他', value: '其他' },
]

const showPreview = ref(false)
const preview = reactive({ intent: 'find_leads', keyword: '', country: '' })
const previewResult = ref<IntentPreviewResponse | null>(null)
const dispatchLoading = ref(false)
const dispatchResult = ref<{
  plan_id: string
  graph_source: string
  node_count: number
  dispatched: boolean
  persistence_note: string
  dispatch_error: string
  card?: OpsCardPayload | null
} | null>(null)
const nodeCols = [
  { title: '步骤', dataIndex: 'id', width: 60 },
  { title: '谁来做', dataIndex: 'executor', width: 120 },
  { title: '做什么', dataIndex: 'capability' },
  {
    title: '人工确认',
    dataIndex: 'approval_required',
    width: 90,
  },
]

const gradeColor = computed(() => {
  const g = card.value?.buyer_grade
  if (g === 'A') return 'success'
  if (g === 'B') return 'processing'
  if (g === 'C') return 'warning'
  if (g === 'D') return 'error'
  return 'default'
})

function setAlert(text: string, type: typeof alertType.value = 'info') {
  alert.value = text
  alertType.value = type
}

async function reloadTips() {
  if (!form.country) {
    tips.value = []
    return
  }
  try {
    const r = await listPlaybooks(form.country, 'new')
    const all: string[] = []
    for (const p of r.playbooks || []) {
      all.push(...(p.tips || []), ...(p.warnings || []))
    }
    tips.value = Array.from(new Set(all)).slice(0, 8)
  } catch {
    tips.value = []
  }
}

async function onIngestReply() {
  if (!form.inquiry_id) {
    message.warning('请先填写询盘编号')
    return
  }
  loading.value = true
  try {
    const tenant = await resolveTenantId()
    const resp = await ingestReply({
      tenant_id: tenant,
      inquiry_id: form.inquiry_id,
      channel: 'inbound',
      message: form.message || '（无正文）',
      country: form.country,
      grade: form.grade,
      owner_user_id: form.owner_user_id,
    })
    applyCard(resp)
    intentAnalysis.value = resp.intent_analysis || null
    if (resp.playbook_tips && resp.playbook_tips.length) {
      tips.value = resp.playbook_tips.slice(0, 8)
    } else {
      await reloadTips()
    }
    if (resp.alerts && resp.alerts.length) {
      setAlert(resp.alerts.join('；'), 'warning')
    } else if (resp.intent_analysis) {
      const lab = INTENT_LABELS[resp.intent_analysis.intent] || resp.intent_analysis.intent
      setAlert(
        `已建卡。意图：${lab}。下一步：${resp.intent_analysis.next_action}`,
        resp.intent_analysis.intent === 'reject_competitor' ? 'warning' : 'success',
      )
    } else {
      setAlert('已建卡并记录跟进。请看下方六格信息。', 'success')
    }
    void loadFollowups()
    void loadLossReport()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    setAlert(`保存失败：${msg}。请确认后端已启动，或稍后重试。`, 'error')
  } finally {
    loading.value = false
  }
}

async function onLoadCard() {
  if (!form.inquiry_id) {
    message.warning('请先填写询盘编号')
    return
  }
  loading.value = true
  try {
    const resp = await getOpsCard(form.inquiry_id)
    applyCard(resp)
    setAlert('已打开跟单卡。', 'success')
  } catch {
    // 没有卡则尝试生成
    try {
      const resp = await materializeOpsCard({
        tenant_id: await resolveTenantId(),
        inquiry_id: form.inquiry_id,
        owner_user_id: form.owner_user_id,
        grade: form.grade || 0,
      })
      applyCard(resp)
      setAlert('该询盘尚无卡片，已为你新建一张。', 'info')
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setAlert(`打不开：${msg}`, 'error')
    }
  } finally {
    loading.value = false
  }
}

async function onTouch() {
  if (!form.inquiry_id || !touch.summary) {
    message.warning('请填写跟进内容')
    return
  }
  loading.value = true
  try {
    const resp = await touchOpsCard(form.inquiry_id, {
      channel: 'manual',
      summary: touch.summary,
      next_action: touch.next_action,
    })
    applyCard(resp)
    touch.summary = ''
    setAlert('跟进已保存。', 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally {
    loading.value = false
  }
}

async function onNote() {
  if (!form.inquiry_id || !note.body) {
    message.warning('请填写备注')
    return
  }
  loading.value = true
  try {
    const resp = await addOpsCardNote(form.inquiry_id, { author: '我', body: note.body })
    applyCard(resp)
    note.body = ''
    setAlert('备注已添加。', 'success')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally {
    loading.value = false
  }
}

async function onLoss() {
  if (!form.inquiry_id || !loss.reasons.length) {
    message.warning('请选择流失原因')
    return
  }
  loading.value = true
  try {
    const resp = await recordOpsCardLoss(form.inquiry_id, { reasons: loss.reasons, note: loss.note })
    applyCard(resp)
    setAlert('流失已登记，系统会记下来供以后改玩法。', 'warning')
  } catch (e: unknown) {
    setAlert(e instanceof Error ? e.message : String(e), 'error')
  } finally {
    loading.value = false
  }
}

async function onPreview() {
  loading.value = true
  try {
    previewResult.value = await previewIntent({
      intent: preview.intent,
      tenant_id: await resolveTenantId(),
      payload: {
        keyword: preview.keyword,
        country: preview.country,
        message: preview.keyword,
        product_name: preview.keyword,
        topic: preview.keyword,
      },
    })
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '拆解失败')
    previewResult.value = null
  } finally {
    loading.value = false
  }
}

async function onDispatch() {
  dispatchLoading.value = true
  try {
    const tenant = await resolveTenantId()
    dispatchResult.value = await dispatchAcquisition({
      intent: preview.intent,
      tenant_id: tenant,
      payload: {
        keyword: preview.keyword,
        country: preview.country,
        message: preview.keyword,
        product_name: preview.keyword,
        topic: preview.keyword,
      },
      inquiry_id: form.inquiry_id || '',
      auto_dispatch: true,
    })
    if (form.inquiry_id) {
      try {
        const fresh = await getOpsCard(form.inquiry_id)
        applyCard(fresh)
      } catch {
        /* ignore */
      }
    }
    setAlert(
      dispatchResult.value.dispatched
        ? `已派发：${dispatchResult.value.node_count} 个步骤`
        : `已拆解未派发：${dispatchResult.value.persistence_note || dispatchResult.value.dispatch_error}`,
      dispatchResult.value.dispatched ? 'success' : 'info',
    )
  } catch (e: unknown) {
    dispatchResult.value = null
    message.error(e instanceof Error ? e.message : '派发失败')
  } finally {
    dispatchLoading.value = false
  }
}

onMounted(async () => {
  // 预置演示数据，降低空态焦虑（傻子都行）
  if (!form.inquiry_id) form.inquiry_id = 'INQ-DEMO-001'
  if (!form.country) form.country = 'SA'
  try {
    const tid = await resolveTenantId()
    wallet.value = await getWalletStatus(tid)
  } catch {
    wallet.value = {
      tenant_id: 'demo',
      token_balance: null,
      plan: null,
      hard_block_enabled: false,
      status: 'unknown',
      message: '后端未启动或计费未接入',
    } as Awaited<ReturnType<typeof getWalletStatus>>
  }
  await loadFollowups()
  void loadChannels()
  void loadLossReport()
  void loadDictionary()
  void loadGrowthOps()
  void loadP2()
})

const wallet = ref<{
  token_balance: number | null
  plan: string | null
  hard_block_enabled: boolean
  status: string
  message: string
} | null>(null)

async function onTranslate() {
  if (!form.message) {
    message.warning('请先粘贴客户原文')
    return
  }
  translateLoading.value = true
  try {
    translateResult.value = await translateAcquisition(form.message, 'auto', 'zh')
  } catch (e: unknown) {
    translateResult.value = null
    message.error(e instanceof Error ? e.message : '翻译失败')
  } finally {
    translateLoading.value = false
  }
}

const translateLoading = ref(false)
const translateResult = ref<{
  original: string
  translated: string
  provider: string
  degraded: boolean
  message: string
} | null>(null)
</script>

<style scoped>
.acq-ops {
  max-width: 1100px;
  margin: 0 auto;
}
.acq-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.acq-cell {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px 14px;
  background: #fafafa;
  min-height: 84px;
}
.acq-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}
.acq-value {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  word-break: break-all;
  line-height: 1.4;
}
.acq-tips {
  margin: 0;
  padding-left: 1.1em;
  font-size: 13px;
  line-height: 1.6;
}
.acq-note {
  font-size: 13px;
  padding: 6px 0;
  border-bottom: 1px dashed #e5e7eb;
}
.acq-follow {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px 10px;
  cursor: pointer;
  background: #fff;
}
.acq-follow:hover {
  border-color: #4a9b8c;
}
.acq-follow-top {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 4px;
}
.acq-score-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fafafa;
  margin-bottom: 8px;
}
.acq-score-letter {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 800;
  color: #fff;
  background: #9ca3af;
  flex-shrink: 0;
}
.acq-score-letter.g-a { background: #10b981; }
.acq-score-letter.g-b { background: #4a9b8c; }
.acq-score-letter.g-c { background: #f59e0b; }
.acq-score-letter.g-d { background: #ef4444; }
.acq-score-meta { flex: 1; min-width: 180px; }
.acq-score-reason { font-weight: 600; color: #111827; }
.acq-score-action { font-size: 12px; color: #6b7280; margin-top: 2px; }
.acq-nodes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
}
.acq-node {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px;
  background: #fff;
  text-align: center;
}
.acq-node.st-done { border-color: #10b981; background: #ecfdf5; }
.acq-node.st-active { border-color: #4a9b8c; background: #f0faf7; }
.acq-node.st-overdue { border-color: #ef4444; background: #fef2f2; }
.acq-node-label { font-size: 13px; font-weight: 600; color: #111827; }
.acq-node-status { font-size: 12px; color: #6b7280; margin-top: 2px; }
.acq-node-ref { font-size: 11px; color: #4a9b8c; margin-top: 2px; word-break: break-all; }
.acq-loss-row { margin-bottom: 10px; }
.acq-loss-reason { font-size: 13px; margin-bottom: 4px; }
.acq-loss-bar {
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 2px;
}
.acq-loss-fill {
  height: 100%;
  background: #ef4444;
  border-radius: 4px;
}
.acq-dict-item {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 12px;
  background: #fafafa;
}
.acq-bill-list { max-height: 120px; overflow: auto; }
.acq-mobile-item { padding: 4px 0; border-bottom: 1px dashed #e5e7eb; }

/* P2-8 移动端跟单：六格/待办在手机上单列可点 */
@media (max-width: 640px) {
  .acq-ops { max-width: 100%; padding: 0 4px; }
  .acq-grid { grid-template-columns: 1fr 1fr; }
  .acq-score-bar { gap: 8px; padding: 10px; }
  .acq-score-letter { width: 48px; height: 48px; font-size: 26px; }
  .acq-nodes { grid-template-columns: 1fr 1fr; }
  .acq-cell { min-height: 72px; padding: 10px; }
  .acq-value { font-size: 14px; }
  .acq-mobile-item {
    padding: 8px 0;
    border-bottom: 1px dashed #e5e7eb;
    font-size: 13px;
  }
  .acq-bill-list { max-height: 140px; overflow: auto; }
  .acq-know-list { max-height: 160px; overflow: auto; }
  .acq-know-item {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
    padding: 4px 0;
    font-size: 12px;
  }
}
  .acq-nodes { grid-template-columns: 1fr 1fr; }
  .acq-follow { padding: 10px; }
}
</style>
