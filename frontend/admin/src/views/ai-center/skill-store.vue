/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="skill-store-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="icon-wrapper">
            <ShopOutlined class="main-icon" />
          </div>
          <div class="header-info">
            <h1 class="page-title">AI 技能商店</h1>
            <p class="page-subtitle">精选技能，安全可靠，助力外贸增长</p>
          </div>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <div class="stat-value">{{ catalogStats.total }}</div>
            <div class="stat-label">技能总数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ catalogStats.approved }}</div>
            <div class="stat-label">已审核</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ catalogStats.ratingAvg }}</div>
            <div class="stat-label">平均评分</div>
          </div>
        </div>
      </div>
    </div>

    <div class="featured-section">
      <h2 class="section-title">精选技能套装</h2>
      <div class="collections-grid">
        <div
          v-for="collection in featuredCollections"
          :key="collection.id"
          class="collection-card"
          @click="selectCollection(collection)"
        >
          <div class="collection-header">
            <ShakeOutlined class="collection-icon" />
            <div class="collection-info">
              <h3 class="collection-name">{{ collection.name }}</h3>
              <p class="collection-desc">{{ collection.description }}</p>
            </div>
          </div>
          <div class="collection-skills">
            <span
              v-for="skill in collection.skills.slice(0, 4)"
              :key="skill.id"
              class="skill-tag"
            >
              {{ skill.accio_analog }}
            </span>
            <span v-if="collection.skills.length > 4" class="skill-tag more">
              +{{ collection.skills.length - 4 }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="top-rated-section">
      <div class="section-header">
        <h2 class="section-title">
          <StarOutlined class="title-icon" />
          热门技能排行
        </h2>
      </div>
      <div class="top-skills-list">
        <div
          v-for="(skill, index) in topRatedSkills"
          :key="skill.id"
          class="top-skill-item"
        >
          <div class="rank-badge" :class="'rank-' + (index + 1)">
            {{ index + 1 }}
          </div>
          <div class="skill-info">
            <h4 class="skill-name">{{ skill.accio_analog }}</h4>
            <p class="skill-desc">{{ skill.description }}</p>
          </div>
          <div class="skill-meta">
            <div class="rating">
              <StarFilled class="star-icon" />
              <span>{{ skill.rating }}</span>
            </div>
            <div class="users">{{ skill.users_count.toLocaleString() }} 使用</div>
          </div>
          <div
            class="risk-badge"
            :style="{ backgroundColor: skill.risk_color + '20', color: skill.risk_color }"
          >
            {{ skill.risk_level }}级安全
          </div>
        </div>
      </div>
    </div>

    <div class="main-content">
      <div class="sidebar">
        <div class="filter-section">
          <h3 class="filter-title">分类筛选</h3>
          <div class="category-list">
            <div
              v-for="group in skillGroups"
              :key="group.id"
              class="category-item"
              :class="{ active: selectedGroup === group.id }"
              @click="selectedGroup = group.id"
            >
              <component :is="getIcon(group.icon)" class="category-icon" />
              <span class="category-name">{{ group.name }}</span>
              <span class="category-count">{{ group.skills.length }}</span>
            </div>
          </div>
        </div>

        <div class="filter-section">
          <h3 class="filter-title">安全等级</h3>
          <div class="risk-filter">
            <div
              v-for="level in riskLevels"
              :key="level.key"
              class="risk-item"
              :class="{ active: selectedRisk === level.key }"
              :style="{ borderColor: level.color }"
              @click="selectedRisk = selectedRisk === level.key ? '' : level.key"
            >
              <span class="risk-label">{{ level.key }}</span>
              <span class="risk-desc">{{ level.label }}</span>
            </div>
          </div>
        </div>

        <div class="filter-section">
          <h3 class="filter-title">排序方式</h3>
          <div class="sort-options">
            <div
              v-for="option in sortOptions"
              :key="option.value"
              class="sort-item"
              :class="{ active: selectedSort === option.value }"
              @click="selectedSort = option.value"
            >
              {{ option.label }}
            </div>
          </div>
        </div>
      </div>

      <div class="skills-grid">
        <div
          v-for="skill in filteredSkills"
          :key="skill.id"
          class="skill-card"
          @click="showSkillDetail(skill)"
        >
          <div class="skill-header">
            <div class="skill-icon-wrapper" :style="{ background: skill.risk_color + '15' }">
              <component :is="getGroupIcon(skill.group_id)" class="skill-icon" :style="{ color: skill.risk_color }" />
            </div>
            <div
              class="risk-level-badge"
              :style="{ backgroundColor: skill.risk_color }"
            >
              {{ skill.risk_level }}
            </div>
          </div>
          <div class="skill-body">
            <h3 class="skill-name">{{ skill.accio_analog }}</h3>
            <p class="skill-desc">{{ skill.description }}</p>
            <div class="skill-tags">
              <span class="tag">{{ skill.group_name }}</span>
              <span class="tag" :class="skill.implemented === true ? 'implemented' : 'partial'">
                {{ skill.implemented === true ? '已实现' : '部分实现' }}
              </span>
            </div>
          </div>
          <div class="skill-footer">
            <div class="skill-metrics">
              <div class="metric">
                <StarFilled class="metric-icon" />
                <span>{{ skill.rating }}</span>
              </div>
              <div class="metric">
                <UserOutlined class="metric-icon" />
                <span>{{ skill.users_count.toLocaleString() }}</span>
              </div>
            </div>
            <div
              class="audit-badge"
              :class="skill.audit_status"
            >
              {{ skill.audit_description }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="detailModalVisible"
      :title="selectedSkill?.accio_analog || '技能详情'"
      width="700px"
      :footer="null"
    >
      <div v-if="selectedSkill" class="skill-detail">
        <div class="detail-header">
          <div class="detail-icon-wrapper" :style="{ background: selectedSkill.risk_color + '15' }">
            <component :is="getGroupIcon(selectedSkill.group_id)" class="detail-icon" :style="{ color: selectedSkill.risk_color }" />
          </div>
          <div class="detail-info">
            <h2>{{ selectedSkill.accio_analog }}</h2>
            <div class="detail-meta">
              <span class="meta-item">{{ selectedSkill.group_name }}</span>
              <span class="meta-item" :style="{ color: selectedSkill.risk_color }">
                {{ selectedSkill.risk_level }}级安全
              </span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>功能描述</h3>
          <p>{{ selectedSkill.description }}</p>
        </div>

        <div class="detail-row">
          <div class="detail-card">
            <h4>安全评估</h4>
            <div class="security-info">
              <div class="security-level" :style="{ backgroundColor: selectedSkill.risk_color }">
                {{ selectedSkill.risk_level }}
              </div>
              <p>{{ selectedSkill.risk_description }}</p>
            </div>
          </div>
          <div class="detail-card">
            <h4>审核状态</h4>
            <div class="audit-info">
              <span class="audit-badge" :class="selectedSkill.audit_status">
                {{ selectedSkill.audit_description }}
              </span>
            </div>
          </div>
        </div>

        <div class="detail-row">
          <div class="detail-card">
            <h4>用户评分</h4>
            <div class="rating-display">
              <StarFilled class="star-large" />
              <span class="rating-value">{{ selectedSkill.rating }}</span>
            </div>
          </div>
          <div class="detail-card">
            <h4>使用人数</h4>
            <div class="users-display">
              <UserOutlined class="users-icon" />
              <span>{{ selectedSkill.users_count.toLocaleString() }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>API 接口</h3>
          <code class="api-code">{{ selectedSkill.api }}</code>
        </div>

        <div class="detail-actions">
          <a-button type="primary">立即使用</a-button>
          <a-button>查看文档</a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  ShopOutlined,
  ShakeOutlined,
  StarOutlined,
  StarFilled,
  UserOutlined,
  SearchOutlined,
  LayoutOutlined,
  RocketOutlined,
  StockOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue';
import type { Component } from 'vue';

interface Skill {
  id: string;
  accio_analog: string;
  implemented: boolean | string;
  api: string;
  risk_level: string;
  risk_color: string;
  risk_description: string;
  audit_status: string;
  audit_description: string;
  rating: number;
  users_count: number;
  description: string;
  group_id: string;
  group_name: string;
}

interface Group {
  id: string;
  name: string;
  icon: string;
  skills: Skill[];
}

interface Collection {
  id: string;
  name: string;
  description: string;
  skill_ids: string[];
  skills: Skill[];
}

const skillGroups = ref<Group[]>([]);
const featuredCollections = ref<Collection[]>([]);
const topRatedSkills = ref<Skill[]>([]);
const selectedGroup = ref('');
const selectedRisk = ref('');
const selectedSort = ref('rating');
const selectedSkill = ref<Skill | null>(null);
const detailModalVisible = ref(false);

const riskLevels = [
  { key: 'S', label: '最高安全', color: '#52c41a' },
  { key: 'A', label: '高安全', color: '#1890ff' },
  { key: 'B', label: '中等安全', color: '#faad14' },
  { key: 'C', label: '较低安全', color: '#ff7875' },
  { key: 'D', label: '危险', color: '#ff4d4f' },
];

const sortOptions = [
  { value: 'rating', label: '按评分排序' },
  { value: 'users', label: '按使用人数排序' },
  { value: 'name', label: '按名称排序' },
];

const iconMap: Record<string, Component> = {
  SearchOutlined,
  LayoutOutlined,
  RocketOutlined,
  StockOutlined,
  SettingOutlined,
};

const getIcon = (iconName: string): Component => {
  return iconMap[iconName] || SearchOutlined;
};

const getGroupIcon = (groupId: string): Component => {
  const icons: Record<string, Component> = {
    discovery: SearchOutlined,
    store: LayoutOutlined,
    marketing: RocketOutlined,
    supply: StockOutlined,
    ops: SettingOutlined,
  };
  return icons[groupId] || SearchOutlined;
};

const catalogStats = computed(() => {
  let total = 0;
  let approved = 0;
  let ratingSum = 0;
  let ratingCount = 0;

  skillGroups.value.forEach(group => {
    group.skills.forEach(skill => {
      total++;
      if (skill.audit_status === 'approved') approved++;
      if (skill.rating) {
        ratingSum += skill.rating;
        ratingCount++;
      }
    });
  });

  return {
    total,
    approved,
    ratingAvg: ratingCount > 0 ? (ratingSum / ratingCount).toFixed(1) : '0.0',
  };
});

const allSkills = computed(() => {
  const skills: Skill[] = [];
  skillGroups.value.forEach(group => {
    group.skills.forEach(skill => {
      skills.push(skill);
    });
  });
  return skills;
});

const filteredSkills = computed(() => {
  let skills = allSkills.value;

  if (selectedGroup.value) {
    skills = skills.filter(s => s.group_id === selectedGroup.value);
  }

  if (selectedRisk.value) {
    skills = skills.filter(s => s.risk_level === selectedRisk.value);
  }

  if (selectedSort.value === 'rating') {
    skills.sort((a, b) => (b.rating || 0) - (a.rating || 0));
  } else if (selectedSort.value === 'users') {
    skills.sort((a, b) => (b.users_count || 0) - (a.users_count || 0));
  } else if (selectedSort.value === 'name') {
    skills.sort((a, b) => a.accio_analog.localeCompare(b.accio_analog));
  }

  return skills;
});

const selectCollection = (collection: Collection) => {
  selectedSkill.value = collection.skills[0] || null;
  if (selectedSkill.value) {
    detailModalVisible.value = true;
  }
};

const showSkillDetail = (skill: Skill) => {
  selectedSkill.value = skill;
  detailModalVisible.value = true;
};

const loadCatalog = async () => {
  try {
    const response = await fetch('/api/v1/skill-store/catalog');
    const data = await response.json();
    if (data.groups) {
      skillGroups.value = data.groups;
    }
  } catch (error) {
    console.error('加载技能目录失败:', error);
  }
};

const loadFeatured = async () => {
  try {
    const response = await fetch('/api/v1/skill-store/featured');
    const data = await response.json();
    if (data.collections) {
      featuredCollections.value = data.collections;
    }
  } catch (error) {
    console.error('加载精选集合失败:', error);
  }
};

const loadTopRated = async () => {
  try {
    const response = await fetch('/api/v1/skill-store/top-rated?limit=5');
    const data = await response.json();
    if (data.skills) {
      topRatedSkills.value = data.skills;
    }
  } catch (error) {
    console.error('加载热门技能失败:', error);
  }
};

loadCatalog();
loadFeatured();
loadTopRated();
</script>

<style lang="scss" scoped>
.skill-store-container {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 24px;
}

.page-header {
  background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.icon-wrapper {
  width: 72px;
  height: 72px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-icon {
  font-size: 36px;
  color: #fff;
}

.header-info {
  color: #fff;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  text-align: center;
  color: #fff;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

.featured-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  color: #faad14;
}

.collections-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.collection-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
}

.collection-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.collection-icon {
  font-size: 24px;
  color: #4a9b8c;
}

.collection-info {
  flex: 1;
}

.collection-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.collection-desc {
  font-size: 13px;
  color: #999;
  margin: 0;
}

.collection-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-tag {
  background: #f5f5f5;
  color: #666;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 16px;

  &.more {
    background: #4a9b8c;
    color: #fff;
  }
}

.top-rated-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.top-skills-list {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
}

.top-skill-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }
}

.rank-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;

  &.rank-1 {
    background: linear-gradient(135deg, #ffd700, #ffb700);
    color: #fff;
  }
  &.rank-2 {
    background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
    color: #fff;
  }
  &.rank-3 {
    background: linear-gradient(135deg, #cd7f32, #b87333);
    color: #fff;
  }
  &.rank-4, &.rank-5 {
    background: #f0f0f0;
    color: #666;
  }
}

.skill-info {
  flex: 1;
}

.skill-name {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.skill-desc {
  font-size: 13px;
  color: #999;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.skill-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
}

.rating {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #faad14;
}

.star-icon {
  font-size: 14px;
}

.users {
  color: #999;
}

.risk-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 16px;
  font-weight: 500;
}

.main-content {
  display: flex;
  gap: 24px;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
}

.filter-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.filter-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #f5f5f5;
  }

  &.active {
    background: #4a9b8c;
    color: #fff;
  }
}

.category-icon {
  font-size: 16px;
}

.category-name {
  flex: 1;
  font-size: 13px;
}

.category-count {
  font-size: 12px;
  opacity: 0.7;
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.risk-filter {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;

  &:hover {
    background: #f5f5f5;
  }

  &.active {
    background: rgba(102, 126, 234, 0.1);
  }
}

.risk-label {
  font-size: 14px;
  font-weight: 600;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.risk-desc {
  font-size: 13px;
  color: #666;
}

.sort-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sort-item {
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;

  &:hover {
    background: #f5f5f5;
  }

  &.active {
    background: #4a9b8c;
    color: #fff;
  }
}

.skills-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.skill-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.skill-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.skill-icon {
  font-size: 24px;
}

.risk-level-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
}

.skill-body {
  margin-bottom: 16px;
}

.skill-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.skill-desc {
  font-size: 13px;
  color: #999;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.skill-tags {
  display: flex;
  gap: 8px;
}

.tag {
  background: #f5f5f5;
  color: #666;
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 4px;

  &.implemented {
    background: #e6f7ff;
    color: #1890ff;
  }

  &.partial {
    background: #fff7e6;
    color: #fa8c16;
  }
}

.skill-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-metrics {
  display: flex;
  gap: 16px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

.metric-icon {
  font-size: 14px;
}

.audit-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;

  &.approved {
    background: #f6ffed;
    color: #52c41a;
  }

  &.partial {
    background: #fff7e6;
    color: #fa8c16;
  }

  &.pending {
    background: #e6f7ff;
    color: #1890ff;
  }

  &.rejected {
    background: #fff2f0;
    color: #ff4d4f;
  }
}

.skill-detail {
  padding: 8px 0;
}

.detail-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-icon {
  font-size: 32px;
}

.detail-info h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.detail-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
}

.meta-item {
  background: #f5f5f5;
  padding: 4px 10px;
  border-radius: 4px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.detail-section p {
  font-size: 14px;
  color: #666;
  margin: 0;
  line-height: 1.6;
}

.detail-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.detail-card {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 16px;
}

.detail-card h4 {
  font-size: 13px;
  color: #999;
  margin: 0 0 12px 0;
}

.security-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.security-level {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.security-info p {
  font-size: 13px;
  color: #666;
  margin: 0;
  flex: 1;
}

.audit-info {
  display: flex;
  align-items: center;
}

.rating-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.star-large {
  font-size: 28px;
  color: #faad14;
}

.rating-value {
  font-size: 24px;
  font-weight: 700;
}

.users-display {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.users-icon {
  font-size: 20px;
  color: #666;
}

.api-code {
  background: #f6f8fa;
  border-radius: 6px;
  padding: 12px;
  font-size: 13px;
  color: #333;
  display: block;
  overflow-x: auto;
}

.detail-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
