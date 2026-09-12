import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Skill, SkillParameter, SkillCategory } from '@/types/skill';

export const useSkillStore = defineStore('skill', () => {
  // 状态
  const skills = ref<Skill[]>([]);
  const currentSkillId = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const executingSkills = ref<Set<string>>(new Set());

  // 计算属性
  const currentSkill = computed(() => {
    if (!currentSkillId.value) return null;
    return skills.value.find(s => s.id === currentSkillId.value) || null;
  });

  const coreSkills = computed(() => {
    return skills.value.filter(s => s.isCore);
  });

  const accioWorkSkills = computed(() => {
    return skills.value.filter(s => s.category === 'accio_work');
  });

  const deerFlowSkills = computed(() => {
    return skills.value.filter(s => s.category === 'deer_flow');
  });

  const skillsByCategory = computed(() => {
    const grouped: Record<SkillCategory, Skill[]> = {
      accio_work: [],
      deer_flow: [],
    };
    skills.value.forEach(skill => {
      grouped[skill.category].push(skill);
    });
    return grouped;
  });

  const isSkillExecuting = computed(() => {
    return (skillId: string) => executingSkills.value.has(skillId);
  });

  // 方法
  function setSkills(newSkills: Skill[]) {
    skills.value = newSkills;
  }

  function addSkill(skill: Skill) {
    skills.value.push(skill);
  }

  function updateSkill(id: string, updates: Partial<Skill>) {
    const index = skills.value.findIndex(s => s.id === id);
    if (index !== -1) {
      skills.value[index] = { ...skills.value[index], ...updates };
    }
  }

  function removeSkill(id: string) {
    skills.value = skills.value.filter(s => s.id !== id);
    if (currentSkillId.value === id) {
      currentSkillId.value = null;
    }
  }

  function setCurrentSkill(id: string | null) {
    currentSkillId.value = id;
  }

  function setLoading(value: boolean) {
    loading.value = value;
  }

  function setError(value: string | null) {
    error.value = value;
  }

  function markSkillExecuting(skillId: string) {
    executingSkills.value.add(skillId);
  }

  function unmarkSkillExecuting(skillId: string) {
    executingSkills.value.delete(skillId);
  }

  function getSkillById(id: string): Skill | undefined {
    return skills.value.find(s => s.id === id);
  }

  function getSkillParameters(skillId: string): SkillParameter[] {
    const skill = getSkillById(skillId);
    return skill?.parameters || [];
  }

  function validateSkillParameters(skillId: string, parameters: Record<string, any>): boolean {
    const skillParams = getSkillParameters(skillId);
    for (const param of skillParams) {
      if (param.required && !(param.name in parameters)) {
        return false;
      }
    }
    return true;
  }

  function getDefaultParameters(skillId: string): Record<string, any> {
    const skillParams = getSkillParameters(skillId);
    const defaults: Record<string, any> = {};
    for (const param of skillParams) {
      if (param.defaultValue !== undefined) {
        defaults[param.name] = param.defaultValue;
      }
    }
    return defaults;
  }

  return {
    // 状态
    skills,
    currentSkillId,
    loading,
    error,
    executingSkills,
    // 计算属性
    currentSkill,
    coreSkills,
    accioWorkSkills,
    deerFlowSkills,
    skillsByCategory,
    isSkillExecuting,
    // 方法
    setSkills,
    addSkill,
    updateSkill,
    removeSkill,
    setCurrentSkill,
    setLoading,
    setError,
    markSkillExecuting,
    unmarkSkillExecuting,
    getSkillById,
    getSkillParameters,
    validateSkillParameters,
    getDefaultParameters,
  };
});