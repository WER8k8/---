/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="层级管理" subtitle="L1 超管 → L2 省代 → L3 市代 → L4 租户" surface="elevated">
  <div class="hierarchy-root">
    <a-alert
      v-if="hierarchyError"
      type="warning"
      show-icon
      class="mb-4"
      :message="hierarchyError"
      closable
      @close="hierarchyError = ''"
    />
    <section class="page-header">
      <div class="page-header-main">
        <p class="page-kicker">{{ greeting }}，{{ displayName }}</p>
        <h1 class="page-title">
          <CrownOutlined class="page-title-icon" />
          层级管理
        </h1>
        <p class="page-desc">
          超管(L1) → 省级代理(L2) → 市级代理(L3) → 官网租户(L4)。查看各层级数据统计，分配权限，管理下级组织。
        </p>
        <div class="page-actions">
          <a-button type="primary" @click="router.push('/dashboard')">数据概览</a-button>
          <a-button @click="router.push('/admin/system/permissions')">权限管理</a-button>
        </div>
      </div>
      <div class="page-stats">
        <div v-for="s in heroStats" :key="s.label" class="page-stat">
          <span class="page-stat-value">{{ s.value }}</span>
          <span class="page-stat-label">{{ s.label }}</span>
        </div>
      </div>
    </section>

    <div class="hierarchy-tree-section panel-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">组织架构树</h2>
          <p class="section-desc">四级层级结构，点击节点查看详情</p>
        </div>
        <a-button type="primary" @click="showAddModal = true">
          <template #icon><PlusOutlined /></template>
          添加节点
        </a-button>
      </div>

      <div class="hierarchy-tree-visual">
        <div class="level-column" v-for="(level, levelIdx) in hierarchyLevels" :key="level.code">
          <div class="level-header-card">
            <div class="level-icon" :style="{ backgroundColor: level.color }">
              <component :is="level.icon" />
            </div>
            <div class="level-info">
              <h3>{{ level.name }}</h3>
              <p>{{ level.code }}</p>
            </div>
          </div>

          <div class="level-nodes">
            <div
              v-for="node in getLevelNodes(level.code)"
              :key="node.id"
              class="node-card"
              :class="{ selected: selectedNode?.id === node.id }"
              @click="selectNode(node)"
            >
              <div class="node-header">
                <div class="node-name">{{ node.name }}</div>
                <div class="node-actions">
                  <template v-if="!node.isTenant">
                    <a-button type="text" size="small" @click.stop="editNode(node)">
                      <EditOutlined />
                    </a-button>
                    <a-button type="text" size="small" danger @click.stop="deleteNode(node)">
                      <DeleteOutlined />
                    </a-button>
                  </template>
                  <a-button v-else type="link" size="small" @click.stop="goTenant(node)">
                    租户
                  </a-button>
                </div>
              </div>
              <div class="node-stats">
                <div class="node-stat">
                  <span class="stat-label">{{ node.isTenant ? '累计付费(元)' : '客户' }}</span>
                  <span class="stat-value">{{ node.contentCount || 0 }}</span>
                </div>
                <div class="node-stat">
                  <span class="stat-label">状态</span>
                  <span class="stat-value" :class="{ active: node.isActive }">
                    {{ node.isActive ? '正常' : '停用' }}
                  </span>
                </div>
              </div>
            </div>

            <div
              v-if="level.code !== 'L4'"
              class="node-card add-card"
              @click="showAddModalForLevel(level.code)"
            >
              <div class="add-icon">
                <PlusOutlined />
              </div>
              <div class="add-text">添加{{ level.shortName }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="detail-section" v-if="selectedNode">
      <div class="detail-panel panel-card">
        <div class="detail-header">
          <h2>{{ selectedNode.name }}</h2>
          <a-button @click="selectedNode = null" size="small">
            <CloseOutlined />
          </a-button>
        </div>

        <div class="detail-content">
          <div class="info-block">
            <h3 class="info-block-title">基本信息</h3>
            <a-descriptions :column="1" bordered :size="'small'">
              <a-descriptions-item label="节点ID">{{ selectedNode.id }}</a-descriptions-item>
              <a-descriptions-item label="节点名称">{{ selectedNode.name }}</a-descriptions-item>
              <a-descriptions-item label="所属层级">{{ getLevelName(selectedNode.level) }}</a-descriptions-item>
              <a-descriptions-item label="创建时间">{{ formatDate(selectedNode.createdAt) }}</a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="selectedNode.isActive ? 'green' : 'red'">
                  {{ selectedNode.isActive ? '正常' : '停用' }}
                </a-tag>
              </a-descriptions-item>
            </a-descriptions>
          </div>

          <div class="info-block">
            <h3 class="info-block-title">数据统计</h3>
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-card-title">下级节点</div>
                <div class="stat-card-value">{{ selectedNode.childrenCount || 0 }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-card-title">产品数量</div>
                <div class="stat-card-value">{{ selectedNode.productCount || 0 }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-card-title">内容数量</div>
                <div class="stat-card-value">{{ selectedNode.contentCount || 0 }}</div>
              </div>
            </div>
          </div>

          <div class="info-block">
            <h3 class="info-block-title">权限管理</h3>
            <a-button type="primary" size="small" @click="showPermissionModal = true">
              <SettingOutlined />
              配置权限
            </a-button>
          </div>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="showAddModal"
      :title="editingNode ? '编辑节点' : '添加节点'"
      @ok="handleSaveNode"
      @cancel="handleCancelModal"
      width="500px"
    >
      <a-form :model="nodeForm" layout="vertical">
        <a-form-item label="节点名称" required>
          <a-input v-model:value="nodeForm.name" placeholder="请输入节点名称" />
        </a-form-item>
        <a-form-item label="所属层级" required>
          <a-select v-model:value="nodeForm.level" placeholder="请选择层级">
            <a-select-option v-for="level in hierarchyLevels" :key="level.code" :value="level.code">
              {{ level.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="上级节点" v-if="nodeForm.level !== 'L1'">
          <a-select v-model:value="nodeForm.parentId" placeholder="请选择上级节点" allow-clear>
            <a-select-option v-for="node in getParentNodes(nodeForm.level)" :key="node.id" :value="node.id">
              {{ node.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="nodeForm.isActive" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="showPermissionModal"
      title="权限配置"
      @ok="handleSavePermissions"
      @cancel="showPermissionModal = false"
      width="600px"
    >
      <a-form :model="permissionForm" layout="vertical">
        <a-form-item label="数据访问范围">
          <a-checkbox-group v-model:value="permissionForm.dataScope">
            <a-checkbox value="read">查看数据</a-checkbox>
            <a-checkbox value="write">编辑数据</a-checkbox>
            <a-checkbox value="delete">删除数据</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
        <a-form-item label="功能权限">
          <a-checkbox-group v-model:value="permissionForm.functions">
            <a-checkbox value="product">产品管理</a-checkbox>
            <a-checkbox value="content">内容管理</a-checkbox>
            <a-checkbox value="seo">SEO优化</a-checkbox>
            <a-checkbox value="analytics">数据分析</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { YdPage } from '@/components/youding';
import { useAuthStore } from '@/stores/auth';
import { message, Modal } from 'ant-design-vue';
import { ydConfirm } from '@/utils/ydModal';
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';
import {
  CrownOutlined,
  RightOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CloseOutlined,
  SettingOutlined,
  GlobalOutlined,
  EnvironmentOutlined,
  HomeOutlined,
} from '@ant-design/icons-vue';

const router = useRouter();
const auth = useAuthStore();

const displayName = computed(() => auth.username || '管理员');

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return '上午好';
  if (h < 18) return '下午好';
  return '晚上好';
});

const hierarchyLevels = [
  { code: 'L1', name: '超管', shortName: '超管', description: '平台侧最高运营主体', icon: CrownOutlined, color: '#55778f' },
  { code: 'L2', name: '省级代理', shortName: '省代', description: '管理下辖市级代理', icon: GlobalOutlined, color: '#0284c7' },
  { code: 'L3', name: '市级代理', shortName: '市代', description: '服务多个官网租户', icon: EnvironmentOutlined, color: '#f59e0b' },
  { code: 'L4', name: '官网租户', shortName: '租户', description: '维护自己的官网内容', icon: HomeOutlined, color: '#ef4444' },
];

type HierarchyNode = {
  id: string;
  name: string;
  level: string;
  childrenCount: number;
  isActive: boolean;
  createdAt: string;
  productCount: number;
  contentCount: number;
  parentId?: string;
  isTenant?: boolean;
  tenantId?: string;
};

const treeNodes = ref<HierarchyNode[]>([]);
const loadingTree = ref(false);
const hierarchyError = ref('');

function levelToUi(code: string): string {
  const c = (code || '').toLowerCase();
  return c.startsWith('l') ? c.toUpperCase() : code.toUpperCase();
}

function mapApiNode(raw: Record<string, unknown>): HierarchyNode {
  const stats = (raw.stats as Record<string, number> | undefined) || {};
  const id = String(raw.id ?? '');
  const isTenant = Boolean(raw.is_tenant) || id.startsWith('tenant:');
  return {
    id,
    name: String(raw.name ?? '未命名'),
    level: levelToUi(String(raw.level ?? 'l4')),
    childrenCount: Number(raw.total_children ?? 0),
    isActive: raw.is_active !== false,
    createdAt: String(raw.created_at ?? ''),
    productCount: stats.active_agents ?? 0,
    contentCount: isTenant
      ? Math.round((stats.total_revenue as number) ?? 0)
      : (stats.total_clients ?? 0),
    parentId: raw.parent_id ? String(raw.parent_id) : undefined,
    isTenant,
    tenantId: isTenant ? String(raw.tenant_id ?? id.replace(/^tenant:/, '')) : undefined,
  };
}

async function loadHierarchy() {
  loadingTree.value = true;
  hierarchyError.value = '';
  try {
    const data = await apiGet<{ levels?: Record<string, { nodes?: Record<string, unknown>[] }> }>(
      '/agent-tree/all-levels',
    );
    const nodes: HierarchyNode[] = [];
    const allowedLevels = new Set(['l1', 'l2', 'l3', 'l4']);
    for (const [lvl, block] of Object.entries(data?.levels || {})) {
      if (!allowedLevels.has(lvl.toLowerCase())) continue;
      for (const n of block?.nodes || []) {
        nodes.push(mapApiNode(n));
      }
    }
    treeNodes.value = nodes;
  } catch (e: unknown) {
    hierarchyError.value = e instanceof Error ? e.message : '层级数据加载失败，请确认超管权限';
    treeNodes.value = [];
  } finally {
    loadingTree.value = false;
  }
}

onMounted(() => {
  void loadHierarchy();
});

const selectedNode = ref<any>(null);
const showAddModal = ref(false);
const showPermissionModal = ref(false);
const editingNode = ref<any>(null);

const nodeForm = reactive({
  name: '',
  level: 'L4',
  parentId: '',
  isActive: true,
});

const permissionForm = reactive({
  dataScope: ['read'],
  functions: ['product', 'content'],
});

function getLevelCount(levelCode: string) {
  return treeNodes.value.filter(n => n.level === levelCode).length;
}

function getLevelNodes(levelCode: string) {
  return treeNodes.value.filter(n => n.level === levelCode);
}

function getLevelName(levelCode: string) {
  const level = hierarchyLevels.find(l => l.code === levelCode);
  return level?.name || levelCode;
}

function getParentNodes(currentLevel: string) {
  const levelIndex = hierarchyLevels.findIndex(l => l.code === currentLevel);
  if (levelIndex <= 0) return [];
  const parentLevel = hierarchyLevels[levelIndex - 1].code;
  return getLevelNodes(parentLevel);
}

function selectNode(node: any) {
  selectedNode.value = node;
}

function goTenant(node: HierarchyNode) {
  router.push('/admin/tenants');
}

function editNode(node: HierarchyNode) {
  if (node.isTenant) {
    goTenant(node);
    return;
  }
  editingNode.value = node;
  nodeForm.name = node.name;
  nodeForm.level = node.level;
  nodeForm.parentId = node.parentId || '';
  nodeForm.isActive = node.isActive;
  showAddModal.value = true;
}

function deleteNode(node: HierarchyNode) {
  if (node.isTenant) {
    message.info('租户请在「租户管理」中操作');
    return;
  }
  ydConfirm({
    title: '停用节点',
    content: `确定停用「${node.name}」？存在活跃下级时将无法停用。`,
    okText: '停用',
    okType: 'danger',
    cancelText: '取消',
    onOk() {
      return (async () => {
        try {
          await apiDelete(`/agent-tree/nodes/${node.id}`);
          message.success('节点已停用');
          if (selectedNode.value?.id === node.id) selectedNode.value = null;
          await loadHierarchy();
        } catch {
          message.error('停用失败');
        }
      })();
    },
  });
}

function showAddModalForLevel(levelCode: string) {
  nodeForm.level = levelCode;
  nodeForm.parentId = '';
  nodeForm.name = '';
  nodeForm.isActive = true;
  editingNode.value = null;
  showAddModal.value = true;
}

async function handleSaveNode() {
  if (!nodeForm.name.trim()) {
    message.warning('请输入节点名称');
    return;
  }
  const level = nodeForm.level.toLowerCase();
  const payload = {
    name: nodeForm.name.trim(),
    level,
    parent_id: nodeForm.parentId || null,
    is_active: nodeForm.isActive,
  };
  try {
    if (editingNode.value) {
      await apiPut(`/agent-tree/nodes/${editingNode.value.id}`, {
        name: payload.name,
        parent_id: payload.parent_id,
        is_active: payload.is_active,
      });
      message.success('节点已更新');
    } else {
      if (level !== 'l1' && !payload.parent_id) {
        message.warning('请选择上级节点');
        return;
      }
      await apiPost('/agent-tree/nodes', payload);
      message.success('节点已创建');
    }
    showAddModal.value = false;
    editingNode.value = null;
    nodeForm.name = '';
    nodeForm.parentId = '';
    await loadHierarchy();
  } catch {
    message.error(editingNode.value ? '更新失败' : '创建失败');
  }
}

function handleCancelModal() {
  showAddModal.value = false;
  editingNode.value = null;
  nodeForm.name = '';
  nodeForm.parentId = '';
}

function handleSavePermissions() {
  message.success('权限配置成功');
  showPermissionModal.value = false;
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

const heroStats = computed(() => [
  { value: String(getLevelCount('L1')), label: '超管' },
  { value: String(getLevelCount('L2')), label: '省代' },
  { value: String(getLevelCount('L3')), label: '市代' },
  { value: String(getLevelCount('L4')), label: '租户' },
]);
</script>

<style scoped lang="scss">
.hierarchy-root {
  min-height: 100%;
  padding-bottom: 2rem;
}

.page-header {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  align-items: stretch;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding: 1.25rem 1.5rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.page-header-main {
  flex: 1 1 280px;
  min-width: 0;
}

.page-kicker {
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
  margin: 0 0 0.35rem;
}

.page-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.page-title-icon {
  color: var(--uj-brand, #4a9b8c);
}

.page-desc {
  margin: 0.5rem 0 0;
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.5;
  max-width: 42rem;
}

.page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
}

.page-stats {
  flex: 0 1 320px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  align-content: center;
}

.page-stat {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.65rem 0.5rem;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  text-align: center;
}

.page-stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.page-stat-label {
  font-size: 0.65rem;
  letter-spacing: 0.04em;
  color: #64748b;
}

.panel-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.hierarchy-tree-section {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.25rem 0;
}

.section-desc {
  font-size: 0.875rem;
  color: #64748b;
  margin: 0;
}

.hierarchy-tree-visual {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.level-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.level-header-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.25);
}

.level-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.5rem;
}

.level-info {
  h3 {
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 0.15rem 0;
  }
  p {
    font-size: 0.75rem;
    color: #64748b;
    margin: 0;
  }
}

.level-nodes {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.node-card {
  background: rgba(255, 255, 255, 0.85);
  border: 2px solid rgba(148, 163, 184, 0.25);
  border-radius: 16px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    border-color: rgba(124, 92, 252, 0.35);
    box-shadow: 0 4px 14px rgba(124, 92, 252, 0.1);
  }

  &.selected {
    border-color: #55778f;
    box-shadow: 0 0 0 2px rgba(124, 92, 252, 0.1), 0 4px 16px rgba(124, 92, 252, 0.15);
  }
}

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.node-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: #0f172a;
}

.node-actions {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.node-card:hover .node-actions {
  opacity: 1;
}

.node-stats {
  display: flex;
  gap: 1.5rem;
}

.node-stat {
  .stat-label {
    font-size: 0.7rem;
    color: #64748b;
    display: block;
    margin-bottom: 0.2rem;
  }
  .stat-value {
    font-size: 0.95rem;
    font-weight: 600;
    color: #0f172a;

    &.active {
      color: #10b981;
    }
  }
}

.add-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100px;
  border-style: dashed;
  background: rgba(255, 255, 255, 0.5);

  &:hover {
    border-color: #55778f;
    background: rgba(124, 92, 252, 0.08);
  }
}

.add-icon {
  font-size: 1.75rem;
  color: #3d5566;
  margin-bottom: 0.25rem;
}

.add-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: #3d5566;
}

.detail-section {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}

.detail-panel {
  padding: 1.5rem;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);

  h2 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-block {
  .info-block-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #64748b;
    margin: 0 0 1rem 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
}

.stat-card-title {
  font-size: 0.78rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.stat-card-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #3d5566;
}

@media (max-width: 1200px) {
  .hierarchy-tree-visual {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hierarchy-tree-visual {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
