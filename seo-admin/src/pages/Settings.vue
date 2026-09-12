<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统全局设置</h2>
      <p>配置品牌信息、外链规则、AI生成参数和发布风控规则</p>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="基础信息" name="basic">
        <el-card>
          <el-form :model="basicForm" label-width="120px" style="max-width: 600px">
            <el-form-item label="品牌名称">
              <el-input v-model="basicForm.brand_name" placeholder="请输入品牌名称" />
            </el-form-item>
            <el-form-item label="官网域名">
              <el-input
                v-model="basicForm.official_website"
                placeholder="https://www.example.com"
              />
            </el-form-item>
            <el-form-item label="联系电话">
              <el-input v-model="basicForm.contact_phone" placeholder="400-XXX-XXXX" />
            </el-form-item>
            <el-form-item label="公司简介">
              <el-input v-model="basicForm.company_intro" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveConfig('basic')">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="外链规则" name="link">
        <el-card>
          <el-form :model="linkForm" label-width="120px" style="max-width: 600px">
            <el-form-item label="插入位置">
              <el-select v-model="linkForm.link_insert_position" style="width: 100%">
                <el-option label="文末" value="end" />
                <el-option label="文中" value="middle" />
                <el-option label="文首" value="start" />
              </el-select>
            </el-form-item>
            <el-form-item label="外链格式">
              <el-input v-model="linkForm.link_format" placeholder="?source={region}" />
              <div class="form-tip">可用变量：{region} 县域名</div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveConfig('link')">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="AI生成配置" name="ai">
        <el-card>
          <el-form :model="aiForm" label-width="120px" style="max-width: 600px">
            <el-form-item label="AI模型">
              <el-select v-model="aiForm.ai_model" style="width: 100%">
                <el-option label="GPT-4" value="gpt-4" />
                <el-option label="GPT-3.5" value="gpt-3.5" />
                <el-option label="Claude" value="claude" />
              </el-select>
            </el-form-item>
            <el-form-item label="文章字数">
              <el-input-number v-model="aiForm.article_length" :min="500" :max="2000" :step="100" />
            </el-form-item>
            <el-form-item label="伪原创强度">
              <el-select v-model="aiForm.rewrite_strength" style="width: 100%">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveConfig('ai')">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="发布风控" name="risk">
        <el-card>
          <el-form :model="riskForm" label-width="140px" style="max-width: 600px">
            <el-form-item label="单平台日上限">
              <el-input-number v-model="riskForm.daily_limit_per_platform" :min="10" :max="200" />
            </el-form-item>
            <el-form-item label="发布间隔最小(分钟)">
              <el-input-number v-model="riskForm.publish_interval_min" :min="1" :max="60" />
            </el-form-item>
            <el-form-item label="发布间隔最大(分钟)">
              <el-input-number v-model="riskForm.publish_interval_max" :min="5" :max="120" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveConfig('risk')">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="微信推送" name="wechat">
        <el-card>
          <el-form :model="wechatForm" label-width="120px" style="max-width: 600px">
            <el-form-item label="推送开关">
              <el-switch v-model="wechatForm.push_enabled" />
              <div class="form-tip">开启后将自动推送每日数据报告</div>
            </el-form-item>
            <el-form-item label="微信AppID">
              <el-input v-model="wechatForm.app_id" placeholder="请输入微信公众号AppID" />
            </el-form-item>
            <el-form-item label="微信AppSecret">
              <el-input
                v-model="wechatForm.app_secret"
                type="password"
                placeholder="请输入微信公众号AppSecret"
                show-password
              />
            </el-form-item>
            <el-form-item label="推送时间">
              <el-time-picker
                v-model="wechatForm.push_time"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="选择推送时间"
              />
              <div class="form-tip">每日在此时间推送数据报告</div>
            </el-form-item>
            <el-form-item label="目标OpenIDs">
              <el-input
                v-model="wechatForm.target_openids"
                type="textarea"
                :rows="3"
                placeholder="请输入要推送的微信用户OpenID，多个用逗号分隔"
              />
            </el-form-item>
            <el-form-item label="推送类型">
              <el-checkbox-group v-model="wechatForm.push_types">
                <el-checkbox label="daily">每日数据报告</el-checkbox>
                <el-checkbox label="alert">异常告警通知</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveWechatConfig">保存配置</el-button>
              <el-button @click="sendManualDaily">手动推送今日报告</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="push-logs-card" style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>推送历史记录</span>
            </div>
          </template>

          <el-table v-loading="logsLoading" :data="pushLogs">
            <el-table-column prop="push_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="row.push_type === 'daily' ? '' : 'danger'" size="small">
                  {{ row.push_type === 'daily' ? '每日报告' : '异常告警' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="target_openid" label="接收者" width="200" />
            <el-table-column prop="send_status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.send_status === 1 ? 'success' : 'danger'" size="small">
                  {{ row.send_status === 1 ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="sent_at" label="发送时间" width="180" />
          </el-table>

          <el-pagination
            v-model:current-page="logsPage"
            v-model:page-size="logsPageSize"
            :total="logsTotal"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 16px; justify-content: flex-end"
            @size-change="fetchPushLogs"
            @current-change="fetchPushLogs"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import api from '@/api';

const activeTab = ref('basic');

const basicForm = reactive({
  brand_name: '',
  official_website: '',
  contact_phone: '',
  company_intro: '',
});
const linkForm = reactive({ link_insert_position: 'end', link_format: '?source={region}' });
const aiForm = reactive({ ai_model: 'gpt-4', article_length: 800, rewrite_strength: 'medium' });
const riskForm = reactive({
  daily_limit_per_platform: 50,
  publish_interval_min: 5,
  publish_interval_max: 30,
});
const wechatForm = reactive({
  app_id: '',
  app_secret: '',
  target_openids: '',
  push_enabled: false,
  push_time: '09:00',
  push_types: ['daily', 'alert'],
});

const pushLogs = ref([]);
const logsLoading = ref(false);
const logsPage = ref(1);
const logsPageSize = ref(20);
const logsTotal = ref(0);

const fetchConfigs = async () => {
  try {
    const res = await api.get('/api/v1/configs');
    const data = res.data;
    if (data.basic) Object.assign(basicForm, data.basic);
    if (data.link) Object.assign(linkForm, data.link);
    if (data.ai) Object.assign(aiForm, data.ai);
    if (data.risk) Object.assign(riskForm, data.risk);
  } catch (e) {
    console.error('获取配置失败:', e);
  }
};

const fetchWechatConfig = async () => {
  try {
    const res = await api.get('/api/v1/wechat/config');
    if (res.code === 200 && res.data) {
      Object.assign(wechatForm, {
        app_id: res.data.app_id || '',
        app_secret: res.data.app_secret || '',
        target_openids: res.data.target_openids || '',
        push_enabled: !!res.data.push_enabled,
        push_time: res.data.push_time || '09:00',
        push_types: res.data.push_types ? res.data.push_types.split(',') : ['daily', 'alert'],
      });
    }
  } catch (e) {
    console.error('获取微信配置失败:', e);
  }
};

const saveConfig = async group => {
  try {
    const formMap = { basic: basicForm, link: linkForm, ai: aiForm, risk: riskForm };
    await api.put('/api/v1/configs', formMap[group]);
    ElMessage.success('配置保存成功');
  } catch (e) {
    ElMessage.error('配置保存失败');
  }
};

const saveWechatConfig = async () => {
  try {
    const configData = {
      ...wechatForm,
      push_types: wechatForm.push_types.join(','),
    };
    await api.put('/api/v1/wechat/config', configData);
    ElMessage.success('微信配置保存成功');
  } catch (e) {
    ElMessage.error('保存失败');
  }
};

const sendManualDaily = async () => {
  try {
    await api.post('/api/v1/wechat/manual/send');
    ElMessage.success('推送任务已发起');
    await fetchPushLogs();
  } catch (e) {
    ElMessage.error('推送失败');
  }
};

const fetchPushLogs = async () => {
  try {
    logsLoading.value = true;
    const res = await api.get('/api/v1/wechat/logs', {
      params: {
        page: logsPage.value,
        page_size: logsPageSize.value,
      },
    });
    if (res.code === 200) {
      pushLogs.value = res.data.list || [];
      logsTotal.value = res.data.total || 0;
    }
  } catch (e) {
    console.error('获取推送日志失败:', e);
  } finally {
    logsLoading.value = false;
  }
};

onMounted(() => {
  fetchConfigs();
  fetchWechatConfig();
  fetchPushLogs();
});
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
