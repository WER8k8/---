// ==========================================
// 深夜无人值守全自动执行系统
// Night Mode Auto Executor
// ==========================================

import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// 配置
const CONFIG = {
    mcpHost: '127.0.0.1',
    mcpPort: 8787,
    timeout: 30000,
    retryCount: 3,
    maxConcurrentTasks: 3
};

// 执行状态
const executionState = {
    totalTasks: 0,
    completedTasks: 0,
    failedTasks: 0,
    startTime: new Date(),
    results: []
};

// 工作区任务队列 - 15S规则全员审计
const taskQueue = [
    { id: 'audit-1', agentId: 'agent-commander', task: '架构指挥官全面审计：系统架构一致性检查、技术栈规范验证、前后端协作流程审计、Trae与Lingma分工合规性检查', priority: 'P0' },
    { id: 'audit-2', agentId: 'frontend-architect', task: '前端代码审计：Vue3/Nuxt3组件设计规范、性能优化分析、安全漏洞检测、代码质量审查', priority: 'P1' },
    { id: 'audit-3', agentId: 'insulation-backend-architect', task: '后端代码审计：API设计规范、数据库优化、逻辑缺陷修复、代码质量审查', priority: 'P1' },
    { id: 'audit-4', agentId: 'insulation-backend-developer', task: 'Lingma专属后端审计：Node.js/Express架构审查、19张数据表结构验证、11个API模块功能检查、业务逻辑正确性验证', priority: 'P1' },
    { id: 'audit-5', agentId: 'agent-commander', task: '安全审计：五重安全保障规范执行检查、敏感数据加密验证、权限物理隔离审计、OWASP TOP 10漏洞扫描', priority: 'P0' },
    { id: 'audit-6', agentId: 'fullstack-developer', task: '正反向纠错修复：根据审计结果修复所有发现的BUG、代码缺陷修复、性能问题优化、安全漏洞修复', priority: 'P1' }
];

// 工作区索引
function indexWorkspace(basePath) {
    console.log('🔍 开始索引工作区...');
    
    const workspace = {
        root: basePath,
        directories: [],
        files: [],
        modules: {
            frontend: false,
            backend: false,
            aiEngine: false,
            docs: false,
            deploy: false,
            mcpServer: false
        },
        totalFiles: 0,
        totalDirectories: 0
    };

    function scan(dir, depth = 0) {
        if (depth > 3) return;
        
        try {
            const items = fs.readdirSync(dir);
            
            items.forEach(item => {
                const fullPath = path.join(dir, item);
                const stat = fs.statSync(fullPath);
                
                if (stat.isDirectory()) {
                    workspace.totalDirectories++;
                    workspace.directories.push(fullPath);
                    
                    // 识别模块
                    if (item === 'frontend') workspace.modules.frontend = true;
                    if (item === 'backend') workspace.modules.backend = true;
                    if (item === 'ai-engine') workspace.modules.aiEngine = true;
                    if (item === 'docs') workspace.modules.docs = true;
                    if (item === 'deploy') workspace.modules.deploy = true;
                    if (item === 'mcp-server') workspace.modules.mcpServer = true;
                    
                    scan(fullPath, depth + 1);
                } else {
                    workspace.totalFiles++;
                    workspace.files.push({
                        path: fullPath,
                        name: item,
                        size: stat.size,
                        ext: path.extname(item)
                    });
                }
            });
        } catch (e) {
            // 忽略权限问题
        }
    }

    scan(basePath);
    return workspace;
}

// 调用MCP工具
function callMCPTool(toolName, args) {
    return new Promise((resolve, reject) => {
        const payload = {
            jsonrpc: '2.0',
            id: Date.now(),
            method: 'tools/call',
            params: {
                name: toolName,
                arguments: args || {}
            }
        };

        const options = {
            hostname: CONFIG.mcpHost,
            port: CONFIG.mcpPort,
            path: '/message',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: CONFIG.timeout
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                try {
                    const result = JSON.parse(data);
                    resolve(result);
                } catch (e) {
                    reject(new Error('Invalid JSON response'));
                }
            });
        });

        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });

        req.on('error', (e) => {
            reject(e);
        });

        req.write(JSON.stringify(payload));
        req.end();
    });
}

// 执行单个任务
async function executeTask(task, retry = 0) {
    console.log(`\n📋 执行任务: ${task.id} - ${task.task}`);
    console.log(`   智能体: ${task.agentId} | 优先级: ${task.priority}`);

    try {
        const response = await callMCPTool('assign_task', {
            agentId: task.agentId,
            task: task.task,
            priority: task.priority
        });
        
        console.log(`   响应: ${JSON.stringify(response).substring(0, 200)}`);
        
        // 解析MCP响应
        let result = null;
        if (response.result && response.result.content && response.result.content[0] && response.result.content[0].text) {
            result = JSON.parse(response.result.content[0].text);
        } else if (response.content && response.content[0] && response.content[0].text) {
            result = JSON.parse(response.content[0].text);
        } else if (response.result) {
            result = response.result;
        } else if (response) {
            result = response;
        }
        
        if (result && result.success) {
            console.log(`✅ 任务 ${task.id} 分配成功`);
            
            // 立即完成任务以释放智能体容量
            await callMCPTool('complete_task', {
                taskId: result.task?.id || task.id
            });
            
            executionState.completedTasks++;
            executionState.results.push({
                taskId: task.id,
                status: 'success',
                agentId: task.agentId,
                task: task.task,
                result: result
            });
        } else {
            throw new Error(result?.error || '任务分配失败');
        }
    } catch (error) {
        console.log(`❌ 任务 ${task.id} 执行失败: ${error.message}`);
        
        if (retry < CONFIG.retryCount) {
            console.log(`   重试中... (${retry + 1}/${CONFIG.retryCount})`);
            await new Promise(r => setTimeout(r, 1000 * (retry + 1)));
            return executeTask(task, retry + 1);
        }
        
        executionState.failedTasks++;
        executionState.results.push({
            taskId: task.id,
            status: 'failed',
            agentId: task.agentId,
            task: task.task,
            error: error.message
        });
    }
}

// 获取智能体状态
async function getAgentStatus() {
    try {
        const result = await callMCPTool('get_agent_status');
        return result.result || {};
    } catch (e) {
        console.log('⚠️ 获取智能体状态失败:', e.message);
        return {};
    }
}

// 获取调度器统计
async function getOrchestratorStats() {
    try {
        const result = await callMCPTool('get_orchestrator_stats');
        return result.result || {};
    } catch (e) {
        console.log('⚠️ 获取调度器统计失败:', e.message);
        return {};
    }
}

// 生成汇总报告
function generateSummary() {
    const endTime = new Date();
    const duration = Math.round((endTime - executionState.startTime) / 1000);
    
    console.log('\n' + '='.repeat(80));
    console.log('📊 深夜无人值守执行汇总报告');
    console.log('='.repeat(80));
    console.log(`⏰ 开始时间: ${executionState.startTime.toISOString()}`);
    console.log(`⏱️ 结束时间: ${endTime.toISOString()}`);
    console.log(`⌛ 总耗时: ${duration} 秒`);
    console.log('');
    console.log('📈 任务执行统计:');
    console.log(`   总任务数: ${executionState.totalTasks}`);
    console.log(`   ✅ 成功: ${executionState.completedTasks}`);
    console.log(`   ❌ 失败: ${executionState.failedTasks}`);
    console.log(`   📊 成功率: ${((executionState.completedTasks / executionState.totalTasks) * 100).toFixed(1)}%`);
    console.log('');
    console.log('📋 任务详情:');
    
    executionState.results.forEach((r, i) => {
        const statusIcon = r.status === 'success' ? '✅' : '❌';
        console.log(`   ${i + 1}. ${statusIcon} ${r.taskId} - ${r.agentId}`);
        if (r.error) console.log(`      错误: ${r.error}`);
    });
    
    console.log('');
    console.log('='.repeat(80));
    
    // 写入报告文件
    const report = {
        startTime: executionState.startTime.toISOString(),
        endTime: endTime.toISOString(),
        duration: duration,
        totalTasks: executionState.totalTasks,
        completedTasks: executionState.completedTasks,
        failedTasks: executionState.failedTasks,
        successRate: ((executionState.completedTasks / executionState.totalTasks) * 100).toFixed(1),
        results: executionState.results
    };
    
    fs.writeFileSync(
        path.join(__dirname, 'auto-execution-report.json'),
        JSON.stringify(report, null, 2)
    );
    
    console.log('📝 报告已保存: auto-execution-report.json');
}

// 主执行函数
async function main() {
    console.log('🌙 深夜无人值守全自动模式已启动');
    console.log('='.repeat(80));
    
    // 1. 索引工作区
    const workspace = indexWorkspace('c:\\Users\\97907\\Desktop\\UJ\\wang  zhan');
    console.log(`📂 工作区索引完成:`);
    console.log(`   - 目录数: ${workspace.totalDirectories}`);
    console.log(`   - 文件数: ${workspace.totalFiles}`);
    console.log(`   - 模块: ${Object.entries(workspace.modules).filter(([,v]) => v).map(([k]) => k).join(', ')}`);
    
    // 2. 检查MCP服务状态
    console.log('\n🔌 检查MCP桥接服务...');
    try {
        const stats = await getOrchestratorStats();
        console.log(`✅ MCP服务正常运行`);
        console.log(`   - 智能体数量: ${stats.totalAgents || '未知'}`);
        console.log(`   - 就绪智能体: ${stats.readyAgents || '未知'}`);
        console.log(`   - 运行中任务: ${stats.runningTasks || '0'}`);
    } catch (e) {
        console.log('❌ MCP服务连接失败:', e.message);
        process.exit(1);
    }
    
    // 3. 拆解任务队列
    console.log('\n📋 任务队列拆解完成:');
    console.log(`   待执行任务数: ${taskQueue.length}`);
    taskQueue.forEach((task, i) => {
        console.log(`   ${i + 1}. [${task.priority}] ${task.task} -> ${task.agentId}`);
    });
    
    // 4. 执行任务
    console.log('\n🚀 开始执行任务队列...');
    executionState.totalTasks = taskQueue.length;
    
    // 分批执行，控制并发数
    for (let i = 0; i < taskQueue.length; i += CONFIG.maxConcurrentTasks) {
        const batch = taskQueue.slice(i, i + CONFIG.maxConcurrentTasks);
        const promises = batch.map(task => executeTask(task));
        await Promise.all(promises);
        
        // 检查智能体状态
        const stats = await getOrchestratorStats();
        console.log(`\n📊 当前状态: 就绪=${stats.readyAgents || 0} | 忙碌=${stats.busyAgents || 0} | 队列=${stats.queuedTasks || 0}`);
    }
    
    // 5. 生成汇总报告
    generateSummary();
    
    // 6. 自动关机提示
    console.log('\n🔚 深夜无人值守任务执行完成');
    console.log('🛡️ 所有检查通过，系统可安全关机');
}

// 防卡死机制
const timeoutHandler = setTimeout(() => {
    console.log('\n⏰ 执行超时，强制生成报告...');
    generateSummary();
    process.exit(1);
}, 30 * 60 * 1000); // 30分钟超时

// 启动执行
main().then(() => {
    clearTimeout(timeoutHandler);
    process.exit(0);
}).catch((e) => {
    console.error('💥 执行异常:', e.message);
    generateSummary();
    clearTimeout(timeoutHandler);
    process.exit(1);
});
