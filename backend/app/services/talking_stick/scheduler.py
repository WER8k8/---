# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Talking-Stick 调度器
负责协调三个Agent的工作，管理任务队列
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from .config import ConfigManager
from .task_queue import TaskQueue, TaskStatus
from .file_lock import FileLock
from .report_generator import ReportGenerator
from .agents.recon_agent import ReconAgent
from .agents.audit_agent import AuditAgent
from .agents.verify_agent import VerifyAgent


class Scheduler:
    """Talking-Stick 调度器"""
    def __init__(self, config_manager: ConfigManager):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param config_manager: 参数 config_manager
        :return: 返回处理结果。
        """
        self.config_manager = config_manager
        self.task_queue = TaskQueue()
        self.file_lock = None
        self.report_generator = None
        # Agent实例
        self.recon_agent = None
        self.audit_agent = None
        self.verify_agent = None
        # 初始化组件
        self._init_components()
    
    def _init_components(self) -> None:
        """初始化组件"""
        # 初始化文件锁
        file_lock_config = self.config_manager.get('file_lock')
        if file_lock_config:
            self.file_lock = FileLock(
                lock_dir=file_lock_config.lock_dir,
                timeout=file_lock_config.timeout
            )
        
        # 初始化报告生成器
        output_config = self.config_manager.get('output')
        if output_config:
            self.report_generator = ReportGenerator(
                output_dir=output_config.dir,
                formats=output_config.formats
            )
        
        # 初始化Agent
        self.recon_agent = ReconAgent(self.config_manager)
        self.audit_agent = AuditAgent(self.config_manager)
        self.verify_agent = VerifyAgent(self.config_manager)
    
    async def submit_scan_task(self, target_path: str, options: Dict[str, Any] = None) -> str:
        """提交扫描任务"""
        task_id = self._generate_task_id()
        # 创建任务并加入队列
        await self.task_queue.enqueue(task_id, target_path, options)
        # 启动后台处理
        asyncio.create_task(self._process_task(task_id))
        return task_id
    
    async def _process_task(self, task_id: str) -> None:
        """处理扫描任务"""
        task = self.task_queue.get_task(task_id)
        if not task:
            return
        
        try:
            # 更新任务状态为运行中
            self.task_queue.update_task_status(task_id, TaskStatus.RUNNING)
            # 执行三层Agent协作
            result = await self._execute_agent_pipeline(task.target_path, task.options)
            # 生成报告
            report_paths = await self._generate_reports(task_id, result)
            # 更新任务状态为完成
            self.task_queue.update_task_status(
                task_id, 
                TaskStatus.COMPLETED, 
                result={
                    "scan_result": result,
                    "report_paths": report_paths
                }
            )
            
        except Exception as e:
            # 更新任务状态为失败
            self.task_queue.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                error=str(e)
            )
    
    async def _execute_agent_pipeline(self, target_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行Agent管道：侦察 → 审计 → 验证"""
        # 第一阶段：侦察Agent
        self._log(f"开始侦察阶段 - 目标: {target_path}")
        recon_result = await self.recon_agent.execute(target_path, options)
        # 第二阶段：审计Agent
        self._log("开始审计阶段")
        audit_result = await self.audit_agent.execute(recon_result, options)
        # 第三阶段：验证Agent
        self._log("开始验证阶段")
        verify_result = await self.verify_agent.execute(audit_result, options)
        # 整合结果
        return {
            "recon": recon_result,
            "audit": audit_result,
            "verification": verify_result,
            "summary": self._generate_summary(recon_result, audit_result, verify_result)
        }
    
    async def _generate_reports(self, task_id: str, result: Dict[str, Any]) -> Dict[str, str]:
        """生成报告"""
        if not self.report_generator:
            return {}
        
        # 生成报告
        reports = self.report_generator.generate(
            task_id=task_id,
            scan_result=result.get("recon", {}),
            audit_result=result.get("audit", {}),
            verification_result=result.get("verification", {}),
            summary=result.get("summary", {})
        )
        return reports
    
    def _generate_summary(self, recon_result: Dict[str, Any], 
                         audit_result: Dict[str, Any], 
                         verify_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成摘要"""
        # 从各阶段结果中提取关键信息
        total_files = recon_result.get("summary", {}).get("total_files", 0)
        risk_files = recon_result.get("summary", {}).get("risk_files", 0)
        vulnerabilities = audit_result.get("vulnerabilities", [])
        total_vulnerabilities = len(vulnerabilities)
        # 按严重程度分类
        critical_count = sum(1 for v in vulnerabilities if v.get("severity") == "critical")
        high_count = sum(1 for v in vulnerabilities if v.get("severity") == "high")
        medium_count = sum(1 for v in vulnerabilities if v.get("severity") == "medium")
        low_count = sum(1 for v in vulnerabilities if v.get("severity") == "low")
        # 验证结果
        verified_vulnerabilities = verify_result.get("vulnerabilities_verified", 0)
        false_positives = verify_result.get("summary", {}).get("false_positives", 0)
        confirmed = verify_result.get("summary", {}).get("confirmed", 0)
        return {
            "total_files": total_files,
            "risk_files": risk_files,
            "total_vulnerabilities": total_vulnerabilities,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "verified_vulnerabilities": verified_vulnerabilities,
            "false_positives": false_positives,
            "confirmed_vulnerabilities": confirmed,
            "scan_timestamp": datetime.now().isoformat()
        }
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"scan_{timestamp}_{id(self)}"
    
    def _log(self, message: str) -> None:
        """记录日志"""
        logger.info("[SCHEDULER] %s", message)
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        return self.task_queue.get_task_status(task_id)
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        task = self.task_queue.get_task(task_id)
        if not task or task.status != TaskStatus.COMPLETED:
            return None
        
        return task.result
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.task_queue.get_task(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.QUEUED:
            self.task_queue.update_task_status(task_id, TaskStatus.CANCELLED)
            return True
        
        return False
    
    async def get_all_tasks(self) -> list:
        """获取所有任务"""
        return self.task_queue.get_all_tasks()
    
    async def clear_completed_tasks(self) -> int:
        """清理已完成的任务"""
        return self.task_queue.clear_completed_tasks()
    
    async def cleanup(self) -> None:
        """清理资源"""
        # 清理文件锁
        if self.file_lock:
            await self.file_lock.cleanup()
        
        # 清理任务队列
        await self.clear_completed_tasks()