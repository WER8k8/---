import { ref, computed } from 'vue';
import { useSkillStore } from '@/stores/skill';
import * as skillAPI from '@/api/ubrain/skill';
import type { Skill, ExecuteSkillRequest } from '@/types/skill';

export function useSkill() {
  const skillStore = useSkillStore();
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 计算属性
  const skills = computed(() => skillStore.skills);
  const currentSkill = computed(() => skillStore.currentSkill);
  const coreSkills = computed(() => skillStore.coreSkills);
  const accioWorkSkills = computed(() => skillStore.accioWorkSkills);
  const deerFlowSkills = computed(() => skillStore.deerFlowSkills);
  const skillsByCategory = computed(() => skillStore.skillsByCategory);

  // 方法
  async function loadSkills() {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await skillAPI.getSkills();
      skillStore.setSkills(response.skills);
    } catch (err) {
      error.value = '加载技能包列表失败';
      console.error('加载技能包列表失败:', err);
    } finally {
      loading.value = false;
    }
  }

  async function loadSkillDetail(skillId: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await skillAPI.getSkillDetail(skillId);
      skillStore.updateSkill(skillId, response.skill);
      skillStore.setCurrentSkill(skillId);
      return response;
    } catch (err) {
      error.value = '加载技能包详情失败';
      console.error('加载技能包详情失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function executeSkill(skillId: string, parameters: Record<string, any>) {
    loading.value = true;
    error.value = null;
    
    try {
      skillStore.markSkillExecuting(skillId);
      
      const request: ExecuteSkillRequest = { parameters };
      const response = await skillAPI.executeSkill(skillId, request);
      
      return response;
    } catch (err) {
      error.value = '执行技能包失败';
      console.error('执行技能包失败:', err);
      throw err;
    } finally {
      loading.value = false;
      skillStore.unmarkSkillExecuting(skillId);
    }
  }

  async function getSkillExecutions(skillId: string, page: number = 1) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await skillAPI.getSkillExecutions(skillId, page);
      return response;
    } catch (err) {
      error.value = '获取执行历史失败';
      console.error('获取执行历史失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function searchSkills(query: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await skillAPI.searchSkills(query);
      return response.skills;
    } catch (err) {
      error.value = '搜索技能包失败';
      console.error('搜索技能包失败:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function favoriteSkill(skillId: string) {
    try {
      await skillAPI.favoriteSkill(skillId);
      // 可以在这里更新本地收藏状态
    } catch (err) {
      error.value = '收藏技能包失败';
      console.error('收藏技能包失败:', err);
      throw err;
    }
  }

  async function unfavoriteSkill(skillId: string) {
    try {
      await skillAPI.unfavoriteSkill(skillId);
      // 可以在这里更新本地收藏状态
    } catch (err) {
      error.value = '取消收藏失败';
      console.error('取消收藏失败:', err);
      throw err;
    }
  }

  function selectSkill(skillId: string) {
    skillStore.setCurrentSkill(skillId);
  }

  function getSkillById(skillId: string) {
    return skillStore.getSkillById(skillId);
  }

  function getSkillParameters(skillId: string) {
    return skillStore.getSkillParameters(skillId);
  }

  function validateSkillParameters(skillId: string, parameters: Record<string, any>) {
    return skillStore.validateSkillParameters(skillId, parameters);
  }

  function getDefaultParameters(skillId: string) {
    return skillStore.getDefaultParameters(skillId);
  }

  function isSkillExecuting(skillId: string) {
    return skillStore.isSkillExecuting(skillId);
  }

  return {
    // 状态
    loading,
    error,
    skills,
    currentSkill,
    coreSkills,
    accioWorkSkills,
    deerFlowSkills,
    skillsByCategory,
    
    // 方法
    loadSkills,
    loadSkillDetail,
    executeSkill,
    getSkillExecutions,
    searchSkills,
    favoriteSkill,
    unfavoriteSkill,
    selectSkill,
    getSkillById,
    getSkillParameters,
    validateSkillParameters,
    getDefaultParameters,
    isSkillExecuting,
  };
}