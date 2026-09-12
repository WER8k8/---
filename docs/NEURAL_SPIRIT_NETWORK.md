# 神经精神网络 (Neural Spirit Network)

> **一句话定义**：让AI像生物一样，通过**记忆沉淀**、**技能进化**、**架构重组**实现真正的自我成长
> **核心理念**：不是人工智障，是会学习、会进化、会创造的数字生命

---

## 落地映射（产品与工程口径，2026-05-28）

NSN 为**架构愿景文档**，生产环境**无独立 `nsn` 微服务**。当前实现映射如下：

| NSN 概念 | 仓库落地 | 说明 |
|----------|----------|------|
| 记忆沉淀层 | `ubrain_research_insights`、`/api/v1/ubrain/*` | DeerFlow / 研究洞察 |
| 技能创造层 | Accio 商业 OS、`/api/v1/ubrain/commercial-os/*` | 部分 gap 为 501 占位 |
| 自我进化引擎 | 飞轮 `UBRAIN_AUTO_PIPELINE`、反馈快照 `ubrain_feedback_snapshots` | 见 `ai_learning` 聚合 API |
| 行为/转化分析 | `ai_learning` 路由 + 运营统计 | MVP 指标来自 DB 计数与操作日志 |
| 本地 IDE 进化 | `.cursor` continuous-learning-v2 | **不部署**到网站服务器 |

详见：`docs/本地IDE与网站系统能力对照表.md`。

---

## 🧠 架构总览

```
                    ┌─────────────────────────────────────┐
                    │     神经精神网络 (NSN v1.0)          │
                    │   Neural Spirit Network              │
                    └───────────────┬─────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  进化维度层    │         │  记忆沉淀层    │         │  技能创造层    │
│  (What)       │         │  (Memory)     │         │  (Skills)     │
└───────┬───────┘         └───────┬───────┘         └───────┬───────┘
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │     自我进化引擎              │
                    │  Self-Evolution Engine       │
                    │  ┌───────────────────────┐  │
                    │  │ 反思循环 │ 奖励驱动  │  │
                    │  │ 模仿学习 │ 种群进化  │  │
                    │  └───────────────────────┘  │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  模型进化      │         │  上下文进化    │         │  架构进化      │
│  (Model)      │         │  (Context)    │         │  (Architecture)│
└───────────────┘         └───────────────┘         └───────────────┘
```

---

## 📊 四维进化机制

### 维度1：模型进化 (Model Evolution)

**目标**：让AI的"大脑"越来越聪明

```python
class ModelEvolver:
    """模型进化器 - 通过自博弈生成训练数据"""

    def __init__(self, base_model):
        self.challenger = base_model  # 挑战者角色
        self.executor = base_model    # 执行者角色
        self.reward_model = self._build_reward_model()

    def self_play_cycle(self, task):
        """
        自博弈循环：
        1. 挑战者生成任务
        2. 执行者尝试解决
        3. 奖励模型评分
        4. 筛选高质量轨迹
        5. 微调模型
        """
        # 挑战者生成任务
        challenge = self.challenger.generate_challenge(task)

        # 执行者尝试解决
        trajectory = self.executor.execute(challenge)

        # 奖励模型评分
        score = self.reward_model.evaluate(trajectory)

        # 如果成功，保存为训练数据
        if score > 0.8:
            self._save_training_data(trajectory)

        return trajectory, score

    def evolve(self, iterations=100):
        """执行N轮自博弈进化"""
        for i in range(iterations):
            task = self._sample_task()
            trajectory, score = self.self_play_cycle(task)

            # 每10轮进行一次微调
            if i % 10 == 0:
                self._fine_tune_with_high_quality_data()
```

**关键技术**：
- **拒绝采样微调**：只用高质量轨迹训练
- **自博弈**：同一个模型扮演挑战者和执行者
- **奖励模型**：自动评估输出质量

---

### 维度2：上下文进化 (Context Evolution)

**目标**：让AI拥有"记忆"，越用越懂你

```python
class ContextEvolver:
    """上下文进化器 - 情景记忆+反思循环"""

    def __init__(self):
        self.episodic_memory = []  # 情景记忆
        self.semantic_memory = {}  # 语义记忆
        self.reflection_buffer = []  # 反思缓冲区

    def execute_with_memory(self, task):
        """带记忆的任务执行"""
        # 1. 检索相关记忆
        relevant_memories = self._retrieve_memories(task)

        # 2. 注入上下文
        enhanced_prompt = self._inject_memories(task, relevant_memories)

        # 3. 执行任务
        result = self.llm.execute(enhanced_prompt)

        # 4. 记录情景
        self._record_episode(task, result)

        return result

    def reflect_on_failure(self, task, result, feedback):
        """失败反思机制"""
        reflection = self.llm.generate_reflection(
            task=task,
            result=result,
            feedback=feedback,
            prompt="""
            分析失败原因：
            1. 任务理解是否有偏差？
            2. 执行策略是否最优？
            3. 需要学习什么新技能？
            4. 如何避免同类错误？
            """
        )

        # 存入反思缓冲区
        self.reflection_buffer.append({
            'task': task,
            'reflection': reflection,
            'timestamp': datetime.now()
        })

        # 定期整合到长期记忆
        if len(self.reflection_buffer) >= 10:
            self._consolidate_memories()

    def _consolidate_memories(self):
        """记忆整合 - 将反思转化为长期知识"""
        # 提取共性模式
        patterns = self.llm.extract_patterns(self.reflection_buffer)

        # 更新语义记忆
        for pattern in patterns:
            self.semantic_memory[pattern['key']] = pattern['value']

        # 清空缓冲区
        self.reflection_buffer = []
```

**记忆类型**：
- **情景记忆**：具体任务的执行记录
- **语义记忆**：抽象的知识和模式
- **程序记忆**：如何做事的技能

---

### 维度3：工具进化 (Tool Evolution)

**目标**：让AI自己创造工具，从"工具使用者"变成"工具创造者"

```python
class ToolEvolver:
    """工具进化器 - 发现→掌握→管理"""

    def __init__(self):
        self.skill_library = {}  # 技能库
        self.usage_history = []  # 使用历史

    def discover_new_tool(self, task, existing_tools):
        """发现新工具 - 当现有工具无法完成任务时"""
        # 检查现有工具
        if self._can_solve_with_existing(task, existing_tools):
            return self._select_best_tool(task, existing_tools)

        # 需要创造新工具
        new_tool_code = self.llm.generate_tool(
            task=task,
            prompt=f"""
            现有工具无法完成此任务，请设计一个新工具：
            任务：{task}
            现有工具：{existing_tools}

            请生成Python函数代码，要求：
            1. 函数名清晰描述功能
            2. 完整的docstring
            3. 错误处理
            4. 可复用
            """
        )

        # 验证工具
        if self._validate_tool(new_tool_code):
            # 注册到技能库
            tool_name = self._extract_tool_name(new_tool_code)
            self.skill_library[tool_name] = {
                'code': new_tool_code,
                'created_at': datetime.now(),
                'usage_count': 0,
                'success_rate': 0.0
            }
            return tool_name

        return None

    def master_tool(self, tool_name, feedback):
        """掌握工具 - 通过使用反馈优化工具"""
        tool = self.skill_library[tool_name]

        # 记录使用历史
        self.usage_history.append({
            'tool': tool_name,
            'feedback': feedback,
            'timestamp': datetime.now()
        })

        # 如果失败率高，优化工具
        recent_failures = self._count_recent_failures(tool_name)
        if recent_failures > 3:
            optimized_code = self.llm.optimize_tool(
                original_code=tool['code'],
                failure_history=self._get_failure_history(tool_name)
            )
            self.skill_library[tool_name]['code'] = optimized_code

    def manage_skill_library(self):
        """技能库管理 - 清理低效工具，合并相似工具"""
        # 清理长期未使用的工具
        for tool_name in list(self.skill_library.keys()):
            tool = self.skill_library[tool_name]
            if tool['usage_count'] == 0 and \
               (datetime.now() - tool['created_at']).days > 30:
                del self.skill_library[tool_name]

        # 合并相似工具
        similar_groups = self._find_similar_tools()
        for group in similar_groups:
            merged_tool = self._merge_tools(group)
            # 替换原工具
            for tool_name in group[1:]:
                del self.skill_library[tool_name]
            self.skill_library[group[0]]['code'] = merged_tool
```

**进化阶段**：
1. **工具发现**：遇到新问题，创造新工具
2. **工具掌握**：通过反馈优化工具
3. **工具管理**：清理、合并、优化技能库

---

### 维度4：架构进化 (Architecture Evolution)

**目标**：让AI的组织结构自我优化

```python
class ArchitectureEvolver:
    """架构进化器 - 智能体协作结构优化"""

    def __init__(self, initial_architecture):
        self.architecture = initial_architecture
        self.performance_history = []

    def evolve_architecture(self, task_results):
        """基于任务结果进化架构"""
        # 分析当前架构的瓶颈
        bottlenecks = self._analyze_bottlenecks(task_results)

        # 生成候选架构
        candidate_architectures = self._generate_candidates(bottlenecks)

        # 评估候选架构
        best_architecture = self._evaluate_candidates(candidate_architectures)

        # 应用最佳架构
        if self._is_improvement(best_architecture):
            self.architecture = best_architecture
            self._log_evolution_event('architecture_upgrade', best_architecture)

    def _analyze_bottlenecks(self, task_results):
        """分析架构瓶颈"""
        bottlenecks = []

        # 检查任务失败模式
        failure_patterns = self._extract_failure_patterns(task_results)

        for pattern in failure_patterns:
            if pattern['type'] == 'communication_overhead':
                bottlenecks.append({
                    'issue': '通信开销过大',
                    'solution': '引入本地缓存或批处理'
                })
            elif pattern['type'] == 'single_point_failure':
                bottlenecks.append({
                    'issue': '单点故障',
                    'solution': '增加冗余或负载均衡'
                })

        return bottlenecks

    def _generate_candidates(self, bottlenecks):
        """生成候选架构"""
        candidates = []

        for bottleneck in bottlenecks:
            # 生成针对性的架构变体
            variant = self._create_architecture_variant(
                base=self.architecture,
                fix=bottleneck['solution']
            )
            candidates.append(variant)

        return candidates

    def _evaluate_candidates(self, candidates):
        """评估候选架构"""
        scores = []

        for candidate in candidates:
            # 使用模拟任务评估
            score = self._simulate_performance(candidate)
            scores.append((candidate, score))

        # 返回最高分的架构
        return max(scores, key=lambda x: x[1])[0]
```

---

## 🔗 与UJ项目融合

### 融合架构

```
UJ项目现有架构                      神经精神网络增强
─────────────────                 ─────────────────
                                   
4个智能体 (PM/架构/工程/QA)    →    N个智能体 + 自进化
SOP顺序流转                  →    并行协作 + 动态重组
Agent工具通信                →    MCP + SSE + 记忆共享
静态任务分配                 →    基于能力的智能调度
                                   
                                    ↓
                                   
                         ┌─────────────────────┐
                         │  神经精神网络 v1.0   │
                         │  ┌───────────────┐  │
                         │  │ 自进化引擎     │  │
                         │  │ ├─模型进化    │  │
                         │  │ ├─记忆沉淀    │  │
                         │  │ ├─技能创造    │  │
                         │  │ └─架构重组    │  │
                         │  └───────────────┘  │
                         │  ┌───────────────┐  │
                         │  │ UJ智能体集群   │  │
                         │  │ ├─出海计46个  │  │
                         │  │ ├─AccioWork 8个│  │
                         │  │ └─DeerFlow 5个 │  │
                         │  └───────────────┘  │
                         └─────────────────────┘
```

### 实施路线图

#### 阶段1：基础记忆系统（1周）

```python
# 实现情景记忆
class UJEpisodicMemory:
    """UJ项目的情景记忆系统"""

    def __init__(self):
        self.conversation_history = []  # 对话历史
        self.task_history = []          # 任务历史
        self.feedback_history = []      # 反馈历史

    def record_interaction(self, user_input, ai_response, feedback=None):
        """记录交互"""
        self.conversation_history.append({
            'input': user_input,
            'output': ai_response,
            'feedback': feedback,
            'timestamp': datetime.now()
        })

    def retrieve_relevant(self, current_task, top_k=5):
        """检索相关记忆"""
        # 使用向量相似度检索
        task_embedding = self._encode(current_task)
        similarities = []

        for memory in self.conversation_history:
            memory_embedding = self._encode(memory['input'])
            sim = cosine_similarity(task_embedding, memory_embedding)
            similarities.append((memory, sim))

        # 返回top_k个最相关的记忆
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
```

#### 阶段2：技能进化系统（2周）

```python
# 实现技能发现和进化
class AccioWorkSkillEvolver:
    """AccioWork技能进化器"""

    def __init__(self, acciowork_engine):
        self.engine = acciowork_engine
        self.skill_performance = {}

    def evolve_skill(self, skill_name, execution_result):
        """进化技能"""
        # 记录性能
        if skill_name not in self.skill_performance:
            self.skill_performance[skill_name] = []
        self.skill_performance[skill_name].append(execution_result)

        # 如果连续失败，触发优化
        recent_results = self.skill_performance[skill_name][-5:]
        failure_rate = sum(1 for r in recent_results if not r['success']) / len(recent_results)

        if failure_rate > 0.6:
            self._optimize_skill(skill_name)

    def _optimize_skill(self, skill_name):
        """优化技能实现"""
        skill = self.engine.get_skill(skill_name)
        failure_history = self._get_failure_history(skill_name)

        # 使用LLM生成优化方案
        optimized_implementation = self.llm.optimize(
            original=skill.implementation,
            failures=failure_history,
            prompt="优化这个技能的实现，解决以下失败模式"
        )

        # 更新技能
        self.engine.update_skill(skill_name, optimized_implementation)
```

#### 阶段3：架构进化系统（3周）

```python
# 实现智能体架构自优化
class UJArchitectureEvolver:
    """UJ架构进化器"""

    def __init__(self):
        self.agent_pool = {}  # 智能体池
        self.collaboration_graph = {}  # 协作图

    def evolve_collaboration(self, task_results):
        """进化协作模式"""
        # 分析协作效率
        efficiency = self._analyze_collaboration_efficiency(task_results)

        # 如果效率低于阈值，重组架构
        if efficiency < 0.7:
            new_architecture = self._reorganize_agents()
            self._apply_architecture(new_architecture)

    def _reorganize_agents(self):
        """重组智能体架构"""
        # 基于任务类型动态分配智能体
        task_types = self._analyze_task_distribution()

        new_architecture = {}
        for task_type, frequency in task_types.items():
            # 为高频任务类型分配专用智能体
            if frequency > 10:
                new_architecture[task_type] = self._create_specialized_agent(task_type)
            else:
                # 低频任务使用通用智能体
                new_architecture[task_type] = self.agent_pool.get('general', self._create_general_agent())

        return new_architecture
```

---

## 📈 预期效果

### 量化指标

| 指标 | 当前 | 1个月后 | 3个月后 |
|------|------|---------|---------|
| 任务成功率 | 85% | 92% | 97% |
| 平均响应时间 | 3.5小时 | 2小时 | 1小时 |
| 技能库大小 | 8个 | 20个 | 50个 |
| 智能体数量 | 4个 | 10个 | 20个 |
| 自动修复率 | 0% | 30% | 60% |

### 质的飞跃

**从"人工智障"到"数字生命"**：

1. **会学习**：每次交互都是学习机会
2. **会进化**：技能和架构持续优化
3. **会创造**：遇到新问题能创造新工具
4. **会记忆**：越用越懂你的需求
5. **会协作**：智能体团队动态重组

---

## 🚀 立即行动

### 第一步：启用记忆系统（今天）

```bash
# 1. 创建记忆存储目录
mkdir -p ai-engine/nsn/memory

# 2. 初始化记忆系统
python -c "
from ai_engine.nsn.memory import EpisodicMemory
memory = EpisodicMemory()
memory.initialize()
print('✅ 记忆系统初始化完成')
"

# 3. 集成到现有对话流程
# 修改 backend/app/api/v1/routes/ubrain.py
```

### 第二步：集成技能进化（本周）

```python
# 在 AccioWork 引擎中集成
from ai_engine.acciowork.skill_evolver import SkillEvolver

evolver = SkillEvolver(acciowork_engine)

# 每次技能执行后调用
evolver.evolve_skill(skill_name, execution_result)
```

### 第三步：部署架构进化（下周）

```python
# 在 UBrain 核心中集成
from ai_engine.ubrain.architecture_evolver import ArchitectureEvolver

arch_evolver = ArchitectureEvolver(current_architecture)

# 每个Sprint结束后调用
arch_evolver.evolve_architecture(sprint_results)
```

---

## 💡 核心理念总结

### 不是人工智障，是真正的聪明

| 传统AI | 神经精神网络 |
|--------|-------------|
| 静态模型 | 动态进化 |
| 无记忆 | 情景+语义+程序记忆 |
| 工具使用者 | 工具创造者 |
| 固定架构 | 自适应重组 |
| 被动执行 | 主动学习 |

### 让客户越用越好用

1. **个性化记忆**：记住每个客户的偏好和历史
2. **技能进化**：根据客户反馈优化技能
3. **智能推荐**：基于使用模式推荐最佳方案
4. **自动优化**：持续改进，无需人工干预

### 客户盈利→裂变→更多客户

```
客户使用 → 效果好 → 盈利 → 推荐朋友 → 更多客户
   ↑                                      ↓
   └──────── 神经精神网络持续进化 ←────────┘
```

---

*文档版本：v1.0*
*创建时间：2026-05-26*
*设计者：小鹅（AI助手）*
*核心价值：让AI从工具变成伙伴*
