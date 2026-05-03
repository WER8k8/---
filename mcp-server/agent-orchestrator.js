// ==========================================
// 智能体任务调度系统
// Agent Orchestrator System
// ==========================================

class AgentOrchestrator {
    constructor() {
        this.agents = new Map();
        this.taskQueue = [];
        this.runningTasks = new Map();
        this.completedTasks = [];
        this.maxConcurrent = 3;
        this.taskIdCounter = 1;
        this.loadConfig();
    }

    loadConfig() {
        // 注册智能体
        const agentDefs = [
            {
                id: 'agent-commander',
                name: '架构指挥官',
                skills: ['architecture-design', 'task-decomposition', 'conflict-resolution'],
                capacity: 5,
                currentLoad: 0
            },
            {
                id: 'frontend-architect',
                name: '前端架构师',
                skills: ['frontend-architecture', 'component-design', 'performance-optimization'],
                capacity: 4,
                currentLoad: 0
            },
            {
                id: 'fullstack-developer',
                name: '全栈开发专家',
                skills: ['frontend', 'backend', 'integration'],
                capacity: 5,
                currentLoad: 0
            },
            {
                id: 'insulation-backend-architect',
                name: '后端架构师',
                skills: ['backend-architecture', 'database-design', 'api-design'],
                capacity: 4,
                currentLoad: 0
            },
            {
                id: 'insulation-backend-developer',
                name: '后端开发专家',
                skills: ['backend-development', 'api-development', 'testing'],
                capacity: 5,
                currentLoad: 0
            },
            {
                id: 'ai-marketing-website-expert',
                name: 'AI营销专家',
                skills: ['seo-optimization', 'content-generation'],
                capacity: 3,
                currentLoad: 0
            }
        ];

        agentDefs.forEach(agent => {
            this.agents.set(agent.id, { ...agent, status: 'ready', assignedTasks: [] });
        });
    }

    analyzeTask(taskDescription) {
        const lowerDesc = taskDescription.toLowerCase();
        
        let primaryAgent = null;
        let priority = 'P2';
        
        // 智能体匹配
        if (lowerDesc.includes('架构') || lowerDesc.includes('设计')) {
            primaryAgent = 'agent-commander';
            priority = lowerDesc.includes('紧急') ? 'P0' : 'P1';
        } else if (lowerDesc.includes('前端') || lowerDesc.includes('vue') || lowerDesc.includes('nuxt')) {
            primaryAgent = 'frontend-architect';
        } else if (lowerDesc.includes('后端') || lowerDesc.includes('api') || lowerDesc.includes('fastapi')) {
            primaryAgent = 'insulation-backend-architect';
        } else if (lowerDesc.includes('seo') || lowerDesc.includes('营销')) {
            primaryAgent = 'ai-marketing-website-expert';
        } else if (lowerDesc.includes('开发') || lowerDesc.includes('功能') || lowerDesc.includes('实现')) {
            primaryAgent = 'fullstack-developer';
        } else {
            primaryAgent = 'fullstack-developer';
        }

        return { primaryAgent, priority, skills: this.agents.get(primaryAgent)?.skills || [] };
    }

    createTask(description, agentId = null, priority = 'P2') {
        let analysis;
        if (!agentId) {
            analysis = this.analyzeTask(description);
            agentId = analysis.primaryAgent;
            priority = analysis.priority;
        }

        const task = {
            id: 'task-' + this.taskIdCounter++,
            description,
            agentId,
            priority,
            status: 'queued',
            createdAt: new Date().toISOString(),
            startedAt: null,
            completedAt: null,
            result: null
        };

        this.taskQueue.push(task);
        console.log('📋 任务创建: ' + task.id + ' -> ' + agentId);
        
        return task;
    }

    assignTask(taskId) {
        const taskIndex = this.taskQueue.findIndex(t => t.id === taskId);
        if (taskIndex === -1) {
            return { success: false, error: 'Task not found' };
        }

        const task = this.taskQueue[taskIndex];
        const agent = this.agents.get(task.agentId);

        if (!agent) {
            return { success: false, error: 'Agent not found' };
        }

        if (agent.currentLoad >= agent.capacity) {
            return { success: false, error: 'Agent capacity reached' };
        }

        // 分配任务
        this.taskQueue.splice(taskIndex, 1);
        task.status = 'in-progress';
        task.startedAt = new Date().toISOString();
        agent.currentLoad++;
        agent.status = 'busy';
        agent.assignedTasks.push(taskId);

        this.runningTasks.set(taskId, task);
        console.log('✅ 任务分配: ' + taskId + ' -> ' + agent.name);

        return { success: true, task, agent };
    }

    completeTask(taskId, result = null) {
        const task = this.runningTasks.get(taskId);
        if (!task) {
            return { success: false, error: 'Task not found in running tasks' };
        }

        const agent = this.agents.get(task.agentId);

        task.status = 'completed';
        task.completedAt = new Date().toISOString();
        task.result = result;

        this.runningTasks.delete(taskId);
        this.completedTasks.push(task);

        if (agent) {
            agent.currentLoad--;
            agent.assignedTasks = agent.assignedTasks.filter(t => t !== taskId);
            if (agent.currentLoad === 0) {
                agent.status = 'ready';
            }
        }

        console.log('✅ 任务完成: ' + taskId);

        return { success: true, task };
    }

    getTaskQueue() {
        return {
            queued: this.taskQueue,
            running: Array.from(this.runningTasks.values()),
            completed: this.completedTasks.slice(-20)
        };
    }

    getAgentStatus(agentId = null) {
        if (agentId) {
            const agent = this.agents.get(agentId);
            return agent || { error: 'Agent not found' };
        }
        return Object.fromEntries(this.agents);
    }

    triggerArchitectureReview(scope = 'full', target = null) {
        const reviewId = 'review-' + Date.now();
        const reviewTask = this.createTask('架构审查: ' + scope + ' ' + (target || '整个项目'), 'agent-commander', 'P0');

        const review = {
            id: reviewId,
            scope,
            target,
            status: 'initiated',
            timestamp: new Date().toISOString(),
            steps: [
                '启动架构审查引擎',
                '扫描代码库结构',
                '检查技术栈一致性',
                '评估性能瓶颈',
                '生成审查报告'
            ],
            eta: '2-5 minutes',
            taskId: reviewTask.id
        };

        this.assignTask(reviewTask.id);

        return review;
    }

    startOrchestration() {
        console.log('🎯 智能体调度系统已激活');
        console.log('🤖 注册智能体: ' + this.agents.size);

        setInterval(() => this.processQueue(), 2000);
    }

    processQueue() {
        if (this.taskQueue.length === 0) return;

        const availableSlots = this.maxConcurrent - this.runningTasks.size;
        if (availableSlots <= 0) return;

        const sorted = [...this.taskQueue].sort((a, b) => {
            const priorityOrder = { P0: 0, P1: 1, P2: 2, P3: 3 };
            return priorityOrder[a.priority] - priorityOrder[b.priority];
        });

        for (let i = 0; i < Math.min(availableSlots, sorted.length); i++) {
            const task = sorted[i];
            const agent = this.agents.get(task.agentId);
            if (agent && agent.currentLoad < agent.capacity) {
                this.assignTask(task.id);
            }
        }
    }

    getStats() {
        return {
            totalAgents: this.agents.size,
            readyAgents: Array.from(this.agents.values()).filter(a => a.status === 'ready').length,
            busyAgents: Array.from(this.agents.values()).filter(a => a.status === 'busy').length,
            queuedTasks: this.taskQueue.length,
            runningTasks: this.runningTasks.size,
            completedTasks: this.completedTasks.length,
            overallLoad: Array.from(this.agents.values()).map(a => ({ id: a.id, load: a.currentLoad, capacity: a.capacity }))
        };
    }
}

const orchestrator = new AgentOrchestrator();
orchestrator.startOrchestration();

export default orchestrator;
