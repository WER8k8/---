/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="外贸核价与出口报价" subtitle="BOQ 22 参数建材工业核价 · 集装箱配载 · 形式发票联动" surface="elevated">
    <a-tabs v-model:activeKey="activeTab" type="card" class="mb-4">
      <!-- Tab 1: BOQ 22参数工业级核价 -->
      <a-tab-pane key="boq" tab="BOQ 22参数工业核价（建材大厂标准）">
        <a-alert
          type="info"
          show-icon
          class="mb-4"
          message="工业级外贸核价引擎"
          description="基于 30 年建材大厂实操逻辑：材料基价 × 厚度系数 + 表面工艺附加费 + 磨边附加费 + Incoterms一切险/海运费 + 20GP/40HQ集装箱物理重柜配载（限重27吨）。"
        />

        <a-card title="BOQ 22 参数配置" class="mb-4" size="small">
          <a-form layout="vertical">
            <!-- 第 1 组：材质与规格核心参数 -->
            <a-divider orientation="left">1. 材质与物理规格 (Material & Dimension)</a-divider>
            <a-row :gutter="16">
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="材料类型 (Material Type)" required>
                  <a-select v-model:value="boqForm.material_type">
                    <a-select-option value="marble">大理石 (Marble)</a-select-option>
                    <a-select-option value="granite">花岗岩 (Granite)</a-select-option>
                    <a-select-option value="ceramic">陶瓷/瓷砖 (Ceramic/Tile)</a-select-option>
                    <a-select-option value="wood">木材/地板 (Wood/Flooring)</a-select-option>
                    <a-select-option value="metal">金属/型材 (Metal/Extrusions)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="质量等级 (Material Grade)">
                  <a-select v-model:value="boqForm.material_grade">
                    <a-select-option value="premium">A 级特优 (+15%)</a-select-option>
                    <a-select-option value="first_choice">优等品 First Choice (+10%)</a-select-option>
                    <a-select-option value="standard">合格标准品 Standard (基准)</a-select-option>
                    <a-select-option value="commercial">工程商用级 Commercial (-10%)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="采购总数量 (Quantity sqm)" required>
                  <a-input-number v-model:value="boqForm.quantity_sqm" :min="1" class="w-full" placeholder="例如 1500" />
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="板材厚度 (Thickness mm)">
                  <a-select v-model:value="boqForm.thickness_mm">
                    <a-select-option :value="15">15 mm (轻型 -17.5%)</a-select-option>
                    <a-select-option :value="18">18 mm (出口标准 -7%)</a-select-option>
                    <a-select-option :value="20">20 mm (工业基准 0%)</a-select-option>
                    <a-select-option :value="25">25 mm (+17.5%)</a-select-option>
                    <a-select-option :value="30">30 mm (重载加厚 +35%)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>

            <!-- 第 2 组：工艺与表面加工 -->
            <a-divider orientation="left">2. 表面工艺与磨边 (Finish & Edge Profile)</a-divider>
            <a-row :gutter="16">
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="表面处理 (Surface Finish)">
                  <a-select v-model:value="boqForm.surface_finish">
                    <a-select-option value="polished">光面/抛光 Polished (基准)</a-select-option>
                    <a-select-option value="honed">哑光 Honed (+2 USD/㎡)</a-select-option>
                    <a-select-option value="flamed">火烧面 Flamed (+4 USD/㎡)</a-select-option>
                    <a-select-option value="bush_hammered">荔枝面 Bush Hammered (+6 USD/㎡)</a-select-option>
                    <a-select-option value="sandblasted">喷砂面 Sandblasted (+5 USD/㎡)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="磨边工艺 (Edge Profile)">
                  <a-select v-model:value="boqForm.edge_profile">
                    <a-select-option value="eased">直边倒角 Eased (标准)</a-select-option>
                    <a-select-option value="beveled">斜边 Beveled (+2 USD/㎡)</a-select-option>
                    <a-select-option value="half_bullnose">半圆边 Half Bullnose (+3.5 USD/㎡)</a-select-option>
                    <a-select-option value="full_bullnose">全圆边 Full Bullnose (+5 USD/㎡)</a-select-option>
                    <a-select-option value="ogee">法国边 Ogee (+7 USD/㎡)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="颜色系列 (Color / Texture)">
                  <a-input v-model:value="boqForm.color" placeholder="如 Bianco Carrara / Pure Grey" />
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="品牌或标段 (Brand / Project)">
                  <a-input v-model:value="boqForm.brand" placeholder="如 YouDing Commercial" />
                </a-form-item>
              </a-col>
            </a-row>

            <!-- 第 3 组：物流与贸易条款 -->
            <a-divider orientation="left">3. 国际物流与贸易条款 (Logistics & Incoterms)</a-divider>
            <a-row :gutter="16">
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="国际贸易条款 (Incoterms)" required>
                  <a-select v-model:value="boqForm.incoterms">
                    <a-select-option value="FOB">FOB 离岸港交货</a-select-option>
                    <a-select-option value="CIF">CIF 到岸交货（含一切险）</a-select-option>
                    <a-select-option value="CFR">CFR 成本加运费</a-select-option>
                    <a-select-option value="DDP">DDP 完税后交货</a-select-option>
                    <a-select-option value="EXW">EXW 工厂交货</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="起运港 (Loading Port)">
                  <a-input v-model:value="boqForm.loading_port" placeholder="例如 Shenzhen / Xiamen" />
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="目的港 (Destination Port)">
                  <a-input v-model:value="boqForm.destination_port" placeholder="例如 Dammam / Rotterdam" />
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="交货周期 (Lead Time Days)">
                  <a-input-number v-model:value="boqForm.lead_time_days" :min="7" class="w-full" />
                </a-form-item>
              </a-col>
            </a-row>

            <!-- 第 4 组：包装、认证与质保 -->
            <a-divider orientation="left">4. 包装、认证与合规 (Packaging & Compliance)</a-divider>
            <a-row :gutter="16">
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="包装方式 (Packaging Type)">
                  <a-select v-model:value="boqForm.packaging_type">
                    <a-select-option value="fumigated_wooden_crates">熏蒸实木箱 (Fumigated Crates)</a-select-option>
                    <a-select-option value="wooden_bundles">木扎架 (Wooden Bundles)</a-select-option>
                    <a-select-option value="carton_pallet">纸箱打托 (Cartons on Pallet)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="国际认证 (Certification)">
                  <a-select v-model:value="boqForm.certification" allow-clear>
                    <a-select-option value="ce">欧盟 CE 认证 (+350 USD)</a-select-option>
                    <a-select-option value="iso9001">ISO 9001 体系</a-select-option>
                    <a-select-option value="sgs">SGS 第三方出厂检验证</a-select-option>
                    <a-select-option value="greenguard">绿色卫士 Greenguard</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="质保年限 (Warranty Years)">
                  <a-input-number v-model:value="boqForm.warranty_years" :min="1" class="w-full" />
                </a-form-item>
              </a-col>
              <a-col :xs="24" :sm="12" :md="6">
                <a-form-item label="付款方式约定 (Payment Terms)">
                  <a-input v-model:value="boqForm.payment_terms" placeholder="30% T/T Deposit, 70% against B/L" />
                </a-form-item>
              </a-col>
            </a-row>

            <!-- 附加开关 -->
            <a-row :gutter="16">
              <a-col :span="24">
                <a-space size="large">
                  <a-checkbox v-model:checked="boqForm.customization">特殊非标定制 (+15%)</a-checkbox>
                  <a-checkbox v-model:checked="boqForm.logo_printing">外箱/背面打标 (+500 USD)</a-checkbox>
                  <a-checkbox v-model:checked="boqForm.inspection_required">出厂商检验货 (+200 USD)</a-checkbox>
                  <a-checkbox v-model:checked="boqForm.insurance_required">购买海运一切险 (+2%)</a-checkbox>
                </a-space>
              </a-col>
            </a-row>

            <div class="mt-4">
              <a-button type="primary" size="large" :loading="boqLoading" @click="runBoqCalculation">
                执行 BOQ 22 参数工业核价
              </a-button>
            </div>
          </a-form>
        </a-card>

        <!-- BOQ 结果展示区 -->
        <a-card v-if="boqResult" title="BOQ 工业核价与装载力报告" class="mb-4">
          <a-row :gutter="16" class="mb-4">
            <a-col :xs="24" :sm="8">
              <a-statistic title="调整后单价 (Adjusted Unit Price)" :value="boqResult.adjusted_unit_price" prefix="$" suffix="/ ㎡" />
            </a-col>
            <a-col :xs="24" :sm="8">
              <a-statistic title="订单总货值 (Total FOB/CIF)" :value="boqResult.total" prefix="$" :precision="2" value-style="color: #4a9b8c" />
            </a-col>
            <a-col :xs="24" :sm="8">
              <a-statistic title="预估 20GP 重柜数" :value="boqResult.breakdown?.estimated_20gp_containers || 1" suffix="个集装箱" />
            </a-col>
          </a-row>

          <a-alert
            type="warning"
            show-icon
            class="mb-3"
            :message="'外贸实操风控提醒'"
            :description="boqResult.trade_advisory"
          />

          <a-descriptions bordered size="small" :column="3">
            <a-descriptions-item label="基础单价">${{ boqResult.base_price }} / ㎡</a-descriptions-item>
            <a-descriptions-item label="采购面积">{{ boqResult.quantity }} ㎡</a-descriptions-item>
            <a-descriptions-item label="出厂纯货值">${{ boqResult.subtotal }}</a-descriptions-item>
            <a-descriptions-item label="货物总体积">{{ boqResult.breakdown?.volume_cbm }} CBM (立方米)</a-descriptions-item>
            <a-descriptions-item label="货物总毛重">{{ boqResult.breakdown?.gross_weight_tons }} 吨 (Tons)</a-descriptions-item>
            <a-descriptions-item label="集装箱限重">20GP限重 27 吨 (防超重甩柜)</a-descriptions-item>
          </a-descriptions>

          <div class="mt-4 flex gap-2">
            <a-button type="primary" @click="copyBoqBreakdown">复制核价清单与外贸备忘</a-button>
            <a-button @click="router.push('/client/queues/fulfillment')">前往履约队列出具形式发票 (PI) →</a-button>
          </div>
        </a-card>
      </a-tab-pane>

      <!-- Tab 2: 简易出口报价 -->
      <a-tab-pane key="simple" tab="快速出口报价（简易模式）">
        <a-card title="简易报价参数" class="mb-4">
          <a-form layout="vertical">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="MOQ">
                  <a-input v-model:value="simpleForm.moq" placeholder="例如 100" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="单价 (USD)">
                  <a-input-number v-model:value="simpleForm.unitPrice" :min="0" class="w-full" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="贸易条款">
                  <a-input v-model:value="simpleForm.deliveryTerms" />
                </a-form-item>
              </a-col>
            </a-row>
            <a-form-item label="备注（中文）">
              <a-textarea v-model:value="simpleForm.notesZh" :rows="2" />
            </a-form-item>
            <a-button type="primary" :loading="simpleLoading" @click="generateSimpleQuote">生成简易报价</a-button>
          </a-form>
        </a-card>

        <a-card v-if="simpleQuote" title="结果">
          <p v-if="!simpleQuote.ready" class="text-red-600">{{ simpleQuote.error }}</p>
          <template v-else>
            <pre class="quote-box">{{ simpleQuote.one_pager_zh }}</pre>
            <p class="text-xs text-gray-500 mt-2">{{ simpleQuote.honest_note }}</p>
            <a-space class="mt-3" wrap>
              <a-button @click="copyText(simpleQuote.one_pager_zh || '')">复制中文一页</a-button>
              <a-button v-if="simpleQuote.pi?.markdown" @click="copyText(simpleQuote.pi.markdown)">复制 PI 英文</a-button>
            </a-space>
          </template>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </YdPage>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import { YdPage } from '@/components/youding';
import { apiPost } from '@/utils/api';
import { postExportQuote, type ExportQuote } from '@/api/cross-border';

const router = useRouter();
const activeTab = ref('boq');

// ── BOQ 22参数表单 ──
const boqLoading = ref(false);
const boqResult = ref<Record<string, any> | null>(null);

const boqForm = reactive({
  material_type: 'marble',
  material_grade: 'premium',
  quantity_sqm: 1500,
  thickness_mm: 20,
  surface_finish: 'polished',
  edge_profile: 'eased',
  color: 'Bianco Carrara White',
  brand: 'YouDing BuildTech',
  origin_country: 'China',
  certification: 'ce',
  packaging_type: 'fumigated_wooden_crates',
  loading_port: 'Shenzhen, China',
  destination_port: 'Dammam, Saudi Arabia',
  incoterms: 'FOB',
  payment_terms: '30% T/T Deposit, 70% against B/L copy',
  lead_time_days: 30,
  warranty_years: 5,
  moq_pieces: 100,
  customization: false,
  logo_printing: false,
  inspection_required: false,
  insurance_required: false,
});

async function runBoqCalculation() {
  boqLoading.value = true;
  try {
    const res = await apiPost<Record<string, any>>('/quotes/calculate-boq', {
      material_type: boqForm.material_type,
      quantity_sqm: boqForm.quantity_sqm,
      incoterms: boqForm.incoterms,
      thickness_mm: boqForm.thickness_mm,
      customization: boqForm.customization,
      logo_printing: boqForm.logo_printing,
      inspection_required: boqForm.inspection_required,
      insurance_required: boqForm.insurance_required,
      params: { ...boqForm },
    });
    const data = (res as any)?.data || res;
    boqResult.value = data;
    message.success('BOQ 22 参数工业核价计算完成');
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '核价计算失败');
  } finally {
    boqLoading.value = false;
  }
}

function copyBoqBreakdown() {
  if (!boqResult.value) return;
  const b = boqResult.value;
  const text = `【YouDing BOQ 工业核价单】
材料: ${boqForm.material_type} (${b.breakdown?.grade})
厚度: ${b.breakdown?.thickness_mm}mm | 表面: ${b.breakdown?.surface_finish} | 磨边: ${b.breakdown?.edge_profile}
采购面积: ${b.quantity} ㎡
出厂单价: $${b.adjusted_unit_price} / ㎡
总货值: $${b.total} ${b.currency} (${b.incoterms})
物流物理预估: ${b.breakdown?.gross_weight_tons} 吨 | ${b.breakdown?.volume_cbm} CBM
集装箱配载: 建议订舱 ${b.breakdown?.estimated_20gp_containers} 个 20GP 重柜 (限重27吨/柜)
风控备忘: ${b.trade_advisory}`;
  copyText(text);
}

// ── 简易报价表单 ──
const simpleLoading = ref(false);
const simpleQuote = ref<ExportQuote | null>(null);
const simpleForm = reactive({
  moq: '',
  unitPrice: undefined as number | undefined,
  deliveryTerms: 'FOB Tianjin',
  notesZh: '',
});

async function generateSimpleQuote() {
  simpleLoading.value = true;
  try {
    const res = await postExportQuote({
      moq: simpleForm.moq || undefined,
      unit_price: simpleForm.unitPrice,
      delivery_terms: simpleForm.deliveryTerms,
      notes_zh: simpleForm.notesZh,
    });
    simpleQuote.value = res as ExportQuote;
    if (!simpleQuote.value?.ready) {
      message.warning(simpleQuote.value?.error || '请先完善产品库');
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '生成失败');
  } finally {
    simpleLoading.value = false;
  }
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(() => message.success('已复制到剪贴板'));
}
</script>

<style scoped>
.quote-box {
  white-space: pre-wrap;
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
}
.w-full {
  width: 100%;
}
</style>
