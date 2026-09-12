"""
Talking-Stick 安全扫描测试脚本
直接调用扫描功能，无需通过API
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.talking_stick.config import ConfigManager
from app.services.talking_stick.scheduler import Scheduler


async def main():
    """主函数"""
    print("=" * 50)
    print("Talking-Stick 安全扫描测试")
    print("=" * 50)
    
    # 初始化配置
    config_manager = ConfigManager()
    
    # 创建调度器
    scheduler = Scheduler(config_manager)
    
    # 扫描目标
    target_path = "backend/app/services"
    print(f"\n扫描目标: {target_path}")
    print("开始扫描...\n")
    
    try:
        # 提交扫描任务
        task_id = await scheduler.submit_scan_task(target_path, {"scan_type": "quick"})
        print(f"任务ID: {task_id}")
        
        # 等待任务完成
        while True:
            status = await scheduler.get_task_status(task_id)
            print(f"状态: {status['status']}", end="\r")
            
            if status["status"] in ["completed", "failed", "cancelled"]:
                break
            
            await asyncio.sleep(1)
        
        print("\n")
        
        # 获取结果
        if status["status"] == "completed":
            result = await scheduler.get_task_result(task_id)
            
            print("=" * 50)
            print("扫描结果摘要")
            print("=" * 50)
            
            summary = result.get("summary", {})
            print(f"总文件数: {summary.get('total_files', 0)}")
            print(f"风险文件: {summary.get('risk_files', 0)}")
            print(f"发现漏洞: {summary.get('total_vulnerabilities', 0)}")
            print()
            
            print("漏洞严重程度分布:")
            print(f"  严重: {summary.get('critical_count', 0)}")
            print(f"  高危: {summary.get('high_count', 0)}")
            print(f"  中危: {summary.get('medium_count', 0)}")
            print(f"  低危: {summary.get('low_count', 0)}")
            print()
            
            # 显示报告路径
            report_paths = result.get("report_paths", {})
            if report_paths:
                print("报告已生成:")
                for fmt, path in report_paths.items():
                    print(f"  {fmt}: {path}")
            
            print("\n扫描完成!")
        else:
            print(f"扫描失败: {status.get('error', '未知错误')}")
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        await scheduler.cleanup()


if __name__ == "__main__":
    asyncio.run(main())