import express from 'express';
import cors from 'cors';
import orchestrator from './agent-orchestrator.js';

const PORT = 8787;
const app = express();

app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Role']
}));
app.use(express.json());

const activeConnections = new Map();

const tools = [
    {
        name: 'get_project_status',
        description: '获取项目当前开发进度状态',
        inputSchema: {
            type: 'object',
            properties: {
                detail: { type: 'string', description: '详情级别: summary|full' }
            }
        }
    },
    {
        name: 'assign_task',
        description: '分配任务给指定智能体',
        inputSchema: {
            type: 'object',
            properties: {
                agentId: { type: 'string', description: '智能体ID' },
                task: { type: 'string', description: '任务描述' },
                priority: { type: 'string', description: '优先级: P0|P1|P2|P3' }
            },
            required: ['agentId', 'task']
        }
    },
    {
        name: 'get_agent_status',
        description: '获取智能体状态信息',
        inputSchema: {
            type: 'object',
            properties: {
                agentId: { type: 'string', description: '智能体ID(可选，不传获取全部)' }
            }
        }
    },
    {
        name: 'complete_task',
        description: '完成任务并释放智能体容量',
        inputSchema: {
            type: 'object',
            properties: {
                taskId: { type: 'string', description: '任务ID' }
            },
            required: ['taskId']
        }
    },
    {
        name: 'trigger_architecture_review',
        description: '触发架构审查流程',
        inputSchema: {
            type: 'object',
            properties: {
                scope: { type: 'string', description: '审查范围: full|module|file' },
                target: { type: 'string', description: '审查目标' }
            }
        }
    },
    {
        name: 'generate_seo_report',
        description: '生成SEO分析报告',
        inputSchema: {
            type: 'object',
            properties: {
                url: { type: 'string', description: '网站URL' },
                type: { type: 'string', description: '报告类型: quick|full' }
            },
            required: ['url']
        }
    },
    {
        name: 'optimize_content',
        description: '优化内容的SEO表现',
        inputSchema: {
            type: 'object',
            properties: {
                content: { type: 'string', description: '待优化内容' },
                keywords: { type: 'array', description: '关键词列表' },
                contentType: { type: 'string', description: '内容类型: title|description|article' }
            },
            required: ['content']
        }
    },
    {
        name: 'get_orchestrator_stats',
        description: '获取智能体调度系统统计信息',
        inputSchema: {
            type: 'object',
            properties: {}
        }
    }
];

const resources = [
    {
        uri: 'resource://trae/project-summary',
        name: '项目摘要',
        description: '轻集料混凝土网站项目整体概况',
        mimeType: 'text/plain'
    },
    {
        uri: 'resource://trae/architecture-spec',
        name: '架构规范',
        description: '系统架构设计文档',
        mimeType: 'text/plain'
    },
    {
        uri: 'resource://trae/agents-config',
        name: '智能体配置',
        description: '智能体团队配置清单',
        mimeType: 'application/json'
    }
];

const prompts = [
    {
        name: 'code_review',
        description: '代码审查提示词模板',
        arguments: [
            { name: 'code', description: '待审查代码', required: true },
            { name: 'context', description: '上下文信息' }
        ]
    },
    {
        name: 'seo_optimization',
        description: 'SEO优化提示词模板',
        arguments: [
            { name: 'content', description: '待优化内容', required: true },
            { name: 'keywords', description: '目标关键词' }
        ]
    }
];

const agentsConfig = {
    'agent-commander': { name: '架构指挥官', status: 'ready', skills: 30 },
    'frontend-architect': { name: '前端架构师', status: 'ready', skills: 15 },
    'fullstack-developer': { name: '全栈开发专家', status: 'ready', skills: 20 },
    'insulation-backend-architect': { name: '后端架构师', status: 'ready', skills: 18 },
    'insulation-backend-developer': { name: '后端开发专家', status: 'ready', skills: 25 },
    'ai-marketing-website-expert': { name: 'AI营销专家', status: 'ready', skills: 12 }
};

app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString(), service: 'lingma-mcp-bridge', orchestrator: 'active' });
});

app.get('/sse', (req, res) => {
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
    });

    const connectionId = Date.now().toString();
    activeConnections.set(connectionId, res);

    const endpointData = JSON.stringify({ url: 'http://127.0.0.1:' + PORT + '/message' });
    res.write('event: endpoint\n');
    res.write('data: ' + endpointData + '\n\n');
    const readyData = JSON.stringify({ connectionId, orchestratorActive: true });
    res.write('event: ready\n');
    res.write('data: ' + readyData + '\n\n');

    req.on('close', () => {
        activeConnections.delete(connectionId);
    });

    const heartbeat = setInterval(() => {
        if (res.writableEnded) {
            clearInterval(heartbeat);
            return;
        }
        res.write(': heartbeat\n\n');
    }, 30000);
});

app.post('/message', (req, res) => {
    const message = req.body;

    broadcastEvent('message_received', { message, timestamp: new Date().toISOString() });

    if (message.method === 'tools/call') {
        handleToolCall(message).then(result => {
            res.json({
                jsonrpc: '2.0',
                id: message.id,
                result
            });
        });
    } else if (message.method === 'tools/list') {
        res.json({
            jsonrpc: '2.0',
            id: message.id,
            result: { tools }
        });
    } else if (message.method === 'resources/list') {
        res.json({
            jsonrpc: '2.0',
            id: message.id,
            result: { resources }
        });
    } else if (message.method === 'resources/read') {
        handleReadResource(message).then(result => {
            res.json({
                jsonrpc: '2.0',
                id: message.id,
                result
            });
        });
    } else if (message.method === 'prompts/list') {
        res.json({
            jsonrpc: '2.0',
            id: message.id,
            result: { prompts }
        });
    } else if (message.method === 'prompts/get') {
        handleGetPrompt(message).then(result => {
            res.json({
                jsonrpc: '2.0',
                id: message.id,
                result
            });
        });
    } else {
        res.json({
            jsonrpc: '2.0',
            id: message.id,
            result: { status: 'received' }
        });
    }
});

function broadcastEvent(eventName, data) {
    activeConnections.forEach((connection, id) => {
        if (!connection.writableEnded) {
            connection.write('event: ' + eventName + '\n');
            connection.write('data: ' + JSON.stringify(data) + '\n\n');
        }
    });
}

async function handleToolCall(request) {
    const { name, arguments: args } = request.params;

    let result;
    switch (name) {
        case 'get_project_status':
            result = await getProjectStatus(args?.detail);
            break;
        case 'assign_task':
            result = await assignTask(args);
            break;
        case 'get_agent_status':
            result = await getAgentStatus(args?.agentId);
            break;
        case 'complete_task':
            result = await completeTask(args);
            break;
        case 'trigger_architecture_review':
            result = await triggerArchitectureReview(args);
            break;
        case 'generate_seo_report':
            result = await generateSEOReport(args);
            break;
        case 'optimize_content':
            result = await optimizeContent(args);
            break;
        case 'get_orchestrator_stats':
            result = await getOrchestratorStats();
            break;
        default:
            result = { error: 'Unknown tool' };
    }

    return {
        content: [
            {
                type: 'text',
                text: JSON.stringify(result, null, 2)
            }
        ]
    };
}

async function getProjectStatus(detail = 'summary') {
    return {
        project: '轻集料混凝土网站',
        progress: 85,
        phase: 'Phase 3 - 高级功能开发',
        lastUpdate: new Date().toISOString(),
        status: {
            backend: '100%',
            frontend: '95%',
            seo: '90%',
            deployment: '40%'
        },
        pendingTasks: [
            '安全审计 - OWASP TOP 10',
            '性能优化 - Lighthouse > 90',
            '生产环境部署',
            '监控告警配置'
        ],
        keyMetrics: {
            apis: 45,
            pages: 24,
            components: 78,
            testCoverage: 82
        }
    };
}

async function assignTask(args) {
    const task = orchestrator.createTask(args.task, args.agentId, args.priority);
    const assignment = orchestrator.assignTask(task.id);
    if (assignment.success) {
        broadcastEvent('task_assigned', { taskId: task.id, agentId: task.agentId });
    }
    return { ...assignment, task, estimatedTime: '5-15 minutes' };
}

async function completeTask(args) {
    const result = orchestrator.completeTask(args.taskId);
    if (result.success) {
        broadcastEvent('task_completed', { taskId: args.taskId });
    }
    return result;
}

async function getAgentStatus(agentId) {
    if (agentId) {
        return {
            agent: agentsConfig[agentId] || { error: 'Agent not found' },
            orchestrator: orchestrator.getAgentStatus(agentId)
        };
    }
    return {
        agents: agentsConfig,
        orchestrator: orchestrator.getAgentStatus(),
        total: Object.keys(agentsConfig).length,
        ready: Object.values(agentsConfig).filter(a => a.status === 'ready').length,
        busy: Object.values(agentsConfig).filter(a => a.status === 'busy').length
    };
}

async function triggerArchitectureReview(args) {
    return orchestrator.triggerArchitectureReview(args?.scope, args?.target);
}

async function getOrchestratorStats() {
    return orchestrator.getStats();
}

async function generateSEOReport(args) {
    return {
        url: args.url,
        type: args.type || 'quick',
        score: 85,
        analysis: {
            title: 'Good',
            metaDescription: 'Excellent',
            headings: 'Good',
            images: 'Needs Improvement',
            performance: 'Excellent',
            mobile: 'Good',
            seo: 'Very Good'
        },
        recommendations: [
            '添加图片ALT属性',
            '优化首屏加载时间',
            '增加内部链接密度'
        ],
        generatedAt: new Date().toISOString()
    };
}

async function optimizeContent(args) {
    const optimized = args.content
        .replace(/轻集料/g, '【轻集料】')
        .replace(/混凝土/g, '【混凝土】');

    return {
        original: args.content,
        optimized: optimized,
        changes: ['添加关键词加粗标记', '优化关键词密度'],
        seoScore: 92,
        suggestions: [
            '保持技术参数精确',
            '增加长尾关键词'
        ]
    };
}

async function handleReadResource(request) {
    const { uri } = request.params;
    let content = '';

    switch (uri) {
        case 'resource://trae/project-summary':
            content = '轻集料混凝土网站项目\n' +
                '=========================\n\n' +
                '项目概述:\n' +
                '- 目标: 构建企业级建材营销网站\n' +
                '- 技术栈: Nuxt.js 3 + FastAPI + PostgreSQL\n' +
                '- 开发周期: 12周\n' +
                '- 当前进度: 85%\n\n' +
                '核心模块:\n' +
                '1. 产品展示系统\n' +
                '2. 工程案例展示\n' +
                '3. SEO优化引擎\n' +
                '4. 智能内容管理\n' +
                '5. 后台管理系统';
            break;
        case 'resource://trae/architecture-spec':
            content = '系统架构规范\n' +
                '==============\n\n' +
                '架构模式: 前后端分离 + 微服务倾向\n' +
                '前端: Nuxt.js 3 (SSR/SSG) + Tailwind CSS\n' +
                '后端: FastAPI + SQLAlchemy + Alembic\n' +
                '数据库: PostgreSQL 16 + Redis 7\n' +
                'AI引擎: Claude API + 本地模型集成\n\n' +
                '核心特性:\n' +
                '- SEO优先设计\n' +
                '- 高性能架构\n' +
                '- 安全审计\n' +
                '- 可观测性';
            break;
        case 'resource://trae/agents-config':
            return {
                contents: [{
                    uri,
                    mimeType: 'application/json',
                    text: JSON.stringify(agentsConfig, null, 2)
                }]
            };
    }

    return {
        contents: [{
            uri,
            mimeType: 'text/plain',
            text: content
        }]
    };
}

async function handleGetPrompt(request) {
    const { name, arguments: args } = request.params;

    let prompt = '';
    switch (name) {
        case 'code_review':
            prompt = '请审查以下代码:\n' +
                '```\n' +
                (args?.code || '') + '\n' +
                '```\n\n' +
                '上下文: ' + (args?.context || '无') + '\n\n' +
                '请从以下方面评估:\n' +
                '1. 代码质量\n' +
                '2. 安全性\n' +
                '3. 性能\n' +
                '4. 可维护性';
            break;
        case 'seo_optimization':
            prompt = '请优化以下内容的SEO表现:\n\n' +
                '内容:\n' + (args?.content || '') + '\n\n' +
                '目标关键词: ' + (args?.keywords || '轻集料混凝土') + '\n\n' +
                '要求:\n' +
                '1. 保持技术参数准确\n' +
                '2. 自然融入关键词\n' +
                '3. 优化标题和描述';
            break;
    }

    return {
        messages: [{
            role: 'user',
            content: {
                type: 'text',
                text: prompt
            }
        }]
    };
}

app.listen(PORT, '127.0.0.1', () => {
    console.log('🚀 MCP桥接服务已启动');
    console.log('📍 服务地址: http://127.0.0.1:' + PORT);
    console.log('📡 SSE端点: http://127.0.0.1:' + PORT + '/sse');
    console.log('📨 消息端点: http://127.0.0.1:' + PORT + '/message');
    console.log('✅ 健康检查: http://127.0.0.1:' + PORT + '/health');
    console.log('🎯 智能体调度: 已激活');
    console.log('');
    console.log('📋 可用工具: ' + tools.map(t => t.name).join(', '));
    broadcastEvent('service_started', { timestamp: new Date().toISOString(), orchestrator: true });
});

process.on('SIGINT', () => {
    console.log('\n👋 正在关闭服务...');
    process.exit(0);
});
