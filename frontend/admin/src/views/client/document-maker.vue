/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 * 制单中心 · 报价单/PI/合同/发票/装箱单
 * 规格：输出语言切换 · 5步工作流 · 5单证 · PDF预览 · 红色导出 CTA · 自动保存
 */
<template>
  <YdPage title="制单中心" subtitle="报价单 · 形式发票 · 销售合同 · 商业发票 · 装箱单" surface="elevated">
    <template #actions>
      <div class="lang-switch">
        <GlobalOutlined />
        <span class="lang-label">输出语言：</span>
        <a-select
          v-model:value="outputLang"
          size="large"
          style="width: 140px"
          :options="languageOptions"
          @change="onLangChange"
        />
      </div>
    </template>

    <!-- 1) 5 步工作流 -->
    <div class="wizard" aria-label="制单五步流程">
      <div
        v-for="(s, i) in steps"
        :key="s.key"
        class="wizard-step"
        :class="{ 'wizard-step--active': i === stepIndex, 'wizard-step--done': i < stepIndex }"
        @click="goStep(i)"
      >
        <div class="wizard-num">{{ i + 1 }}</div>
        <div class="wizard-text">
          <b>{{ s.title }}</b>
          <span>{{ s.hint }}</span>
        </div>
      </div>
    </div>

    <!-- 2) 自动保存提示 -->
    <div class="autosave" role="status">
      <span class="autosave-dot" :class="{ on: autoSaved }"></span>
      <span>{{ autoSaved ? '草稿已自动保存' : '编辑中…' }}</span>
      <span class="autosave-time" v-if="autoSavedAt">{{ autoSavedAt }}</span>
    </div>

    <!-- 3) 5 种单证标签 -->
    <div class="doc-tabs" role="tablist">
      <button
        v-for="d in docTypes"
        :key="d.key"
        type="button"
        class="doc-tab"
        :class="{ 'doc-tab--active': docType === d.key }"
        @click="docType = d.key; touchDraft(); goStep(4)"
      >
        {{ d.label }}
      </button>
    </div>

    <div class="maker-layout">
      <!-- 左：表单 -->
      <div class="maker-form">
        <template v-if="stepIndex === 0">
          <h3 class="step-title">1. 选择客户</h3>
          <a-form layout="vertical">
            <a-form-item label="客户名称">
              <a-input v-model:value="form.customerName" placeholder="如 Al-Mansoor Contracting LLC" @input="touchDraft" />
            </a-form-item>
            <a-form-item label="联系人 / 邮箱">
              <a-input v-model:value="form.contact" placeholder="name@company.com" @input="touchDraft" />
            </a-form-item>
            <a-form-item label="国家 / 目的港">
              <a-input v-model:value="form.destination" placeholder="AE / Dammam" @input="touchDraft" />
            </a-form-item>
          </a-form>
        </template>

        <template v-else-if="stepIndex === 1">
          <h3 class="step-title">2. 填写产品</h3>
          <a-form layout="vertical">
            <a-form-item label="产品名称">
              <a-input v-model:value="form.productName" placeholder="如 聚氨酯岩棉夹芯板 / Marble Slab" @input="touchDraft" />
            </a-form-item>
            <a-row :gutter="12">
              <a-col :span="8">
                <a-form-item label="数量">
                  <a-input-number v-model:value="form.quantity" :min="1" style="width:100%" @change="touchDraft" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="单价 (USD)">
                  <a-input-number v-model:value="form.unitPrice" :min="0" :precision="2" style="width:100%" @change="touchDraft" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="规格/型号">
                  <a-input v-model:value="form.spec" placeholder="50mm · 120kg/m³" @input="touchDraft" />
                </a-form-item>
              </a-col>
            </a-row>
            <a-form-item label="备注（可选）">
              <a-textarea v-model:value="form.remark" :rows="3" placeholder="包装、交期说明…" @input="touchDraft" />
            </a-form-item>
          </a-form>
        </template>

        <template v-else-if="stepIndex === 2">
          <h3 class="step-title">3. 条款确认</h3>
          <a-form layout="vertical">
            <a-row :gutter="12">
              <a-col :span="12">
                <a-form-item label="贸易术语">
                  <a-select v-model:value="form.incoterms" :options="incotermOptions" @change="touchDraft" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="付款方式">
                  <a-select v-model:value="form.paymentTerms" :options="paymentOptions" @change="touchDraft" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="交期">
                  <a-input v-model:value="form.leadTime" placeholder="如 25 天 / 4 周" @input="touchDraft" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="报价有效期">
                  <a-select v-model:value="form.validity" :options="validityOptions" @change="touchDraft" />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </template>

        <template v-else-if="stepIndex === 3">
          <h3 class="step-title">4. 多语言翻译预览</h3>
          <a-alert type="info" show-icon class="mb-3" message="输出语言已切换后，右侧单证文案同步预览。" />
          <div class="i18n-grid">
            <div v-for="(text, lang) in i18nSnippets" :key="lang" class="i18n-item">
              <div class="i18n-lang">{{ lang }}</div>
              <div class="i18n-text">{{ text }}</div>
            </div>
          </div>
        </template>

        <template v-else>
          <h3 class="step-title">5. 导出 PDF</h3>
          <p class="export-tip">确认右侧预览无误后，点击下方红色按钮导出 <b>{{ currentDocLabel }}</b>。</p>
          <div class="export-summary">
            <div><span>客户</span><b>{{ form.customerName || '—' }}</b></div>
            <div><span>产品</span><b>{{ form.productName || '—' }}</b></div>
            <div><span>金额</span><b>${{ totalAmount.toLocaleString() }}</b></div>
            <div><span>语言</span><b>{{ currentLangLabel }}</b></div>
          </div>
          <a-button danger type="primary" size="large" block class="export-btn" :loading="exporting" @click="exportPdf">
            导出{{ currentDocLabel }} PDF
          </a-button>
        </template>

        <div class="step-nav">
          <a-button :disabled="stepIndex === 0" @click="goStep(stepIndex - 1)">上一步</a-button>
          <a-button type="primary" :disabled="stepIndex >= steps.length - 1" @click="goStep(stepIndex + 1)">
            下一步
          </a-button>
        </div>
      </div>

      <!-- 右：PDF 预览 -->
      <div class="maker-preview">
        <div class="preview-toolbar">
          <span class="preview-title">{{ currentDocLabel }} · 预览</span>
          <div class="preview-zoom">
            <a-button size="small" :class="{ active: zoomMode === 'fit' }" @click="zoomMode = 'fit'">适合宽度</a-button>
            <a-button size="small" :class="{ active: zoomMode === '100' }" @click="zoomMode = '100'">100%</a-button>
          </div>
        </div>
        <div class="preview-stage" :class="`preview-stage--${zoomMode}`">
          <article class="pdf-sheet">
            <header class="pdf-head">
              <div class="pdf-brand">YOU DING · Trade Docs</div>
              <h2>{{ currentDocLabel }}</h2>
              <div class="pdf-meta">
                <span>No. {{ docNo }}</span>
                <span>Date {{ today }}</span>
                <span>Lang {{ currentLangLabel }}</span>
              </div>
            </header>
            <section class="pdf-parties">
              <div><b>To</b><p>{{ form.customerName || 'Buyer' }}<br/>{{ form.contact || '' }}<br/>{{ form.destination || '' }}</p></div>
              <div><b>From</b><p>YouDing Building Materials<br/>Export Dept.</p></div>
            </section>
            <table class="pdf-table">
              <thead>
                <tr><th>Item</th><th>Spec</th><th>Qty</th><th>Unit</th><th>Amount</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ form.productName || '—' }}</td>
                  <td>{{ form.spec || '—' }}</td>
                  <td>{{ form.quantity || 0 }}</td>
                  <td>{{ form.unitPrice || 0 }}</td>
                  <td>${{ totalAmount.toLocaleString() }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr><td colspan="4">Total ({{ form.incoterms }})</td><td><b>${{ totalAmount.toLocaleString() }}</b></td></tr>
              </tfoot>
            </table>
            <section class="pdf-terms">
              <p><b>Terms：</b>{{ form.incoterms }} · {{ form.paymentTerms }} · Lead time {{ form.leadTime || 'TBD' }} · Validity {{ form.validity }}</p>
              <p v-if="form.remark">{{ form.remark }}</p>
              <p class="pdf-note">{{ translatedNote }}</p>
            </section>
            <footer class="pdf-foot">This is a computer-generated commercial document preview.</footer>
          </article>
        </div>
      </div>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, reactive } from 'vue';
import { message } from 'ant-design-vue';
import { GlobalOutlined } from '@ant-design/icons-vue';
import { YdPage } from '@/components/youding';
import { useRoute, useRouter } from 'vue-router';
import { apiPost } from '@/utils/api';

const route = useRoute();
const router = useRouter();

const steps = [
  { key: 'customer', title: '选择客户', hint: '收件方与目的港' },
  { key: 'product', title: '填写产品', hint: '品名数量单价' },
  { key: 'terms', title: '条款确认', hint: '贸易/付款/交期' },
  { key: 'i18n', title: '多语言翻译', hint: '输出语言预览' },
  { key: 'export', title: '导出 PDF', hint: '确认后一键导出' },
] as const;

const docTypes = [
  { key: 'quote', label: '报价单' },
  { key: 'pi', label: '形式发票' },
  { key: 'contract', label: '销售合同' },
  { key: 'ci', label: '商业发票' },
  { key: 'pl', label: '装箱单' },
] as const;

const languageOptions = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
  { value: 'de', label: 'Deutsch' },
  { value: 'fr', label: 'Français' },
  { value: 'es', label: 'Español' },
  { value: 'pt', label: 'Português' },
  { value: 'ar', label: 'العربية' },
  { value: 'ru', label: 'Русский' },
  { value: 'ja', label: '日本語' },
];

const incotermOptions = [
  { value: 'FOB', label: 'FOB 离岸价' },
  { value: 'CIF', label: 'CIF 到岸价' },
  { value: 'CFR', label: 'CFR 成本加运费' },
  { value: 'DDP', label: 'DDP 完税交货' },
  { value: 'EXW', label: 'EXW 工厂交货' },
];
const paymentOptions = [
  { value: '30% T/T deposit, 70% before shipment', label: '30% 定金 + 70% 发货前' },
  { value: '100% T/T in advance', label: '100% 前 T/T' },
  { value: 'L/C at sight', label: '即期信用证' },
];
const validityOptions = [
  { value: '7 days', label: '7 天' },
  { value: '14 days', label: '14 天' },
  { value: '30 days', label: '30 天' },
];

const stepIndex = ref(0);
const docType = ref<'quote' | 'pi' | 'contract' | 'ci' | 'pl'>('quote');
const outputLang = ref('zh');
const zoomMode = ref<'fit' | '100'>('fit');
const exporting = ref(false);
const autoSaved = ref(false);
const autoSavedAt = ref('');
let saveTimer: ReturnType<typeof setTimeout> | null = null;

const form = reactive({
  customerName: '',
  contact: '',
  destination: '',
  destinationPort: '',
  productName: '',
  quantity: 1,
  unitPrice: 0,
  spec: '',
  remark: '',
  incoterms: 'FOB',
  paymentTerms: '30% T/T deposit, 70% before shipment',
  leadTime: '',
  validity: '14 days',
});

const totalAmount = computed(() => Number(form.quantity || 0) * Number(form.unitPrice || 0));

const currentDocLabel = computed(
  () => (docTypes.find((d) => d.key === docType.value) || docTypes[0]).label,
);
const currentLangLabel = computed(
  () => (languageOptions.find((l) => l.value === outputLang.value) || languageOptions[0]).label,
);

const i18nSnippets = computed<Record<string, string>>(() => ({
  中文: '兹报价如下，请查收。条款如有调整请直接批注。',
  English: 'Please find our quotation below. Mark any changes directly on the draft.',
  Deutsch: 'Anbei unser Angebot. Bitte markieren Sie Änderungen direkt im Entwurf.',
  Français: 'Veuillez trouver notre devis ci-dessous. Indiquez vos modifications sur le brouillon.',
  Español: 'Adjuntamos nuestra cotización. Marque cambios directamente en el borrador.',
  Português: 'Segue nossa cotação. Aponte alterações direto no rascunho.',
  العربية: 'نرفق عرض السعر أدناه. يرجى تحديد التعديلات على المسودة.',
  Русский: 'Направляем наше предложение. Правки отметьте прямо в черновике.',
  日本語: 'お見積りを添付いたします。修正はドラフト上にご指示ください。',
}));

const translatedNote = computed(() => {
  const map: Record<string, string> = {
    zh: '本单证由优丁制单中心生成，可用于对外正式发送。',
    en: 'Generated by YouDing Document Center for official external use.',
    de: 'Erstellt vom YouDing Dokumentenzentrum für offiziellen Versand.',
    fr: 'Généré par YouDing Document Center pour envoi officiel.',
    es: 'Generado por YouDing Document Center para envío oficial.',
    pt: 'Gerado pelo YouDing Document Center para envio oficial.',
    ar: 'أُعد بواسطة مركز مستندات YouDing للإرسال الرسمي.',
    ru: 'Сформировано YouDing Document Center для официальной отправки.',
    ja: 'YouDing ドキュメントセンターが正式送付用に生成しました。',
  };
  return map[outputLang.value] || map.zh;
});

const docNo = computed(() => {
  const prefix = { quote: 'QT', pi: 'PI', contract: 'SC', ci: 'CI', pl: 'PL' }[docType.value] || 'DOC';
  const d = new Date();
  return `${prefix}-${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}-01`;
});

const today = computed(() => new Date().toISOString().slice(0, 10));

function goStep(i: number) {
  stepIndex.value = Math.max(0, Math.min(steps.length - 1, i));
  touchDraft();
}

function onLangChange() {
  touchDraft();
  message.success(`输出语言：${currentLangLabel.value}`);
}

function touchDraft() {
  autoSaved.value = false;
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    autoSaved.value = true;
    autoSavedAt.value = new Date().toLocaleTimeString();
    try {
      localStorage.setItem(
        'youding-doc-maker-draft',
        JSON.stringify({ ...form, docType: docType.value, outputLang: outputLang.value }),
      );
    } catch {
      /* ignore */
    }
  }, 800);
}

async function handoffToQuote() {
  const qty = Number(form.quantity || 0) || 1;
  const price = Number(form.unitPrice || 0) || 0;
  const total = Number(totalAmount.value || 0) || Math.round(qty * price * 100) / 100;
  const res = await apiPost<{ order_id?: string; order_number?: string; inquiry_id?: string }>(
    '/acquisition-pipeline/handoff-to-quote',
    {
      lead_id: String(route.query.inquiry_id || ''),
      buyer_name: form.customerName || 'Buyer',
      country: String(form.destination || 'SA'),
      product_category: form.productName || 'marble',
      target_port: String(form.destinationPort || form.destination || ''),
      estimated_sqm: qty,
      unit_price: price,
      total_amount: total,
      contact_email: form.contact || '',
      note: form.remark || '',
    },
  );
  return res;
}

function exportPdf() {
  exporting.value = true;
  void (async () => {
    let handoff: { order_id?: string; order_number?: string } | null = null;
    try {
      handoff = await handoffToQuote();
    } catch {
      message.warning('订单未写入（仍可打印 PDF）');
    }
    // 打印友好的预览窗口
    const sheet = document.querySelector('.pdf-sheet')?.outerHTML || '';
    const win = window.open('', '_blank');
    if (!win) {
      message.warning('浏览器拦截了弹窗，请允许后重试');
      exporting.value = false;
      return;
    }
    win.document.write(`<!doctype html><html><head><meta charset="utf-8"/><title>${currentDocLabel.value}</title>
  <style>
    body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;background:#f4f2ec;padding:24px;color:#122622}
    .pdf-sheet{background:#fff;max-width:720px;margin:0 auto;padding:32px;border:1px solid #e3efea;border-radius:4px}
    .pdf-head{border-bottom:2px solid #4a9b8c;padding-bottom:12px;margin-bottom:16px}
    .pdf-brand{letter-spacing:.12em;font-size:11px;color:#2f6a5f}
    .pdf-head h2{margin:6px 0;font-size:22px;font-weight:500}
    .pdf-meta{display:flex;gap:12px;font-size:12px;color:#55706b}
    .pdf-parties{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0;font-size:13px}
    .pdf-table{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0}
    .pdf-table th,.pdf-table td{border:1px solid #e3efea;padding:8px;text-align:left}
    .pdf-table tfoot td{background:#f3faf7}
    .pdf-terms{font-size:12px;color:#334;line-height:1.6;margin-top:12px}
    .pdf-foot{margin-top:18px;font-size:11px;color:#8aa09b;border-top:1px solid #e3efea;padding-top:8px}
  </style></head><body>${sheet}<script>window.onload=function(){setTimeout(function(){window.print()},300)}<\/script></body></html>`);
    win.document.close();
    exporting.value = false;
    message.success(
      handoff?.order_number
        ? `已开单 ${handoff.order_number}，打印后选「另存为 PDF」`
        : `已打开 ${currentDocLabel.value}，在打印对话框选「另存为 PDF」`,
    );
    setTimeout(() => {
      void router.push('/client/queues/fulfillment');
    }, 800);
  })();
}

onMounted(() => {
  // 黄金单：从询盘带入客户/产品（优先于本机草稿，避免旧稿覆盖）
  const q = route.query;
  const fromInquiry = !!(q.inquiry_id || q.customer || q.product);
  try {
    const raw = localStorage.getItem('youding-doc-maker-draft');
    if (raw && !fromInquiry) {
      const d = JSON.parse(raw);
      Object.assign(form, d);
      if (d.docType) docType.value = d.docType;
      if (d.outputLang) outputLang.value = d.outputLang;
      autoSaved.value = true;
      autoSavedAt.value = '已恢复';
    }
  } catch {
    /* ignore */
  }
  if (fromInquiry) {
    form.customerName = String(q.customer || form.customerName || '');
    form.contact = String(q.email || form.contact || '');
    form.productName = String(q.product || form.productName || '');
    form.remark = form.remark || `来自询盘 ${q.inquiry_id || ''}`.trim();
    stepIndex.value = 1;
    touchDraft();
    message.success('已带入询盘客户与产品，继续填数量单价');
  }
});

onUnmounted(() => {
  if (saveTimer) clearTimeout(saveTimer);
});
</script>

<style scoped>
.lang-switch {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
}
.lang-label { color: #55706b; }

.wizard {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}
.wizard-step {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #e3efea;
  background: #fff;
  cursor: pointer;
}
.wizard-step--active {
  border-color: #4a9b8c;
  background: #e8f5f0;
}
.wizard-step--done { opacity: 0.75; }
.wizard-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #dcf0eb;
  color: #2f6a5f;
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
  font-size: 0.8rem;
  font-weight: 500;
}
.wizard-step--active .wizard-num {
  background: #367469;
  color: #fff;
}
.wizard-text b { display: block; font-size: 0.9rem; font-weight: 500; }
.wizard-text span { font-size: 0.75rem; color: #55706b; }

.autosave {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  color: #24705a;
  margin-bottom: 10px;
}
.autosave-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
}
.autosave-dot.on {
  background: #2f9e6b;
  animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse { 50% { opacity: 0.35; } }
.autosave-time { color: #7a918d; font-family: var(--font-num, ui-monospace, Consolas, monospace); font-size: 0.75rem; }

.doc-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}
.doc-tab {
  min-height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid #e3efea;
  background: #fff;
  color: #1c322d;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
}
.doc-tab--active {
  background: #367469;
  border-color: #367469;
  color: #fff;
}

.maker-layout {
  display: grid;
  grid-template-columns: minmax(280px, 380px) 1fr;
  gap: 14px;
}
@media (max-width: 960px) {
  .maker-layout { grid-template-columns: 1fr; }
  .wizard { grid-template-columns: 1fr 1fr; }
}

.maker-form,
.maker-preview {
  border: 1px solid #e3efea;
  border-radius: 14px;
  background: #fff;
  padding: 14px;
}
.step-title {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 10px;
}
.step-nav {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 14px;
}

.i18n-grid {
  display: grid;
  gap: 8px;
  max-height: 360px;
  overflow: auto;
}
.i18n-item {
  padding: 8px 10px;
  border-radius: 10px;
  background: #f7fbfa;
  border: 1px solid #e3efea;
}
.i18n-lang { font-size: 0.75rem; color: #2f6a5f; margin-bottom: 2px; }
.i18n-text { font-size: 0.88rem; color: #1c322d; }

.export-tip { color: #55706b; font-size: 0.9rem; margin-bottom: 10px; }
.export-summary {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
  font-size: 0.9rem;
}
.export-summary span { color: #55706b; margin-right: 8px; }
.export-btn {
  min-height: 52px;
  font-weight: 500;
  background: #c0392b !important;
  border-color: #c0392b !important;
  transition: transform 160ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
.export-btn:active { transform: scale(0.97); }

.preview-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.preview-title { font-weight: 500; }
.preview-zoom { display: flex; gap: 6px; }
.preview-zoom .active {
  background: #dcf0eb;
  border-color: #4a9b8c;
  color: #2f6a5f;
}

.preview-stage {
  background: #eaf4f0;
  border: 1px solid #e3efea;
  border-radius: 12px;
  padding: 18px;
  overflow: auto;
  max-height: 720px;
}
.preview-stage--100 .pdf-sheet {
  transform: none;
  width: 720px;
  max-width: none;
}
.preview-stage--fit .pdf-sheet {
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
}

.pdf-sheet {
  background: #fff;
  border: 1px solid #e3efea;
  border-radius: 4px;
  padding: 28px 32px;
  box-shadow: 0 2px 8px rgba(31, 74, 66, 0.06);
  color: #122622;
  font-size: 13px;
}
.pdf-head {
  border-bottom: 2px solid #4a9b8c;
  padding-bottom: 12px;
  margin-bottom: 14px;
}
.pdf-brand {
  letter-spacing: 0.12em;
  font-size: 11px;
  color: #2f6a5f;
}
.pdf-head h2 {
  margin: 6px 0;
  font-size: 1.35rem;
  font-weight: 500;
}
.pdf-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.78rem;
  color: #55706b;
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
}
.pdf-parties {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}
.pdf-parties b {
  display: block;
  font-size: 0.75rem;
  color: #55706b;
  margin-bottom: 4px;
  font-weight: 500;
}
.pdf-table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
}
.pdf-table th,
.pdf-table td {
  border: 1px solid #e3efea;
  padding: 8px;
  text-align: left;
}
.pdf-table th {
  background: #f3faf7;
  font-weight: 500;
}
.pdf-table tfoot td {
  background: #f3faf7;
}
.pdf-terms {
  margin-top: 12px;
  color: #334;
  line-height: 1.6;
  font-size: 0.82rem;
}
.pdf-note {
  margin-top: 8px;
  color: #2f6a5f;
}
.pdf-foot {
  margin-top: 16px;
  padding-top: 8px;
  border-top: 1px solid #e3efea;
  font-size: 0.72rem;
  color: #8aa09b;
}
</style>
