"""
Talking-Stick 独立扫描脚本
不依赖backend应用，直接测试核心功能
"""

import asyncio
import sys
from pathlib import Path

# 添加talking_stick模块路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "app" / "services"))

from talking_stick.config import ConfigManager
from talking_stick.scheduler import Scheduler


async def main():
    """主函数"""
    print("=" * 60)
    print("Talking-Stick 安全扫描测试 (独立模式)")
    print("=" * 60)
    
    # 初始化配置
    config_path = Path(__file__).parent.parent / ".talking-stick" / "config.yaml"
    config_manager = ConfigManager(str(config_path))
    
    # 创建调度器
    scheduler = Scheduler(config_manager)
    
    # 扫描目标
    target_path = str(Path(__file__).parent.parent / "backend" / "app" / "services")
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
            
            print("=" * 60)
            print("扫描结果摘要")
            print("=" * 60)
            
            # 侦察结果
            recon = result.get("scan_result", {}).get("recon", {})
            recon_summary = recon.get("summary", {})
            print("\n【侦察阶段】")
            print(f"  总文件数: {recon_summary.get('total_files', 0)}")
            print(f"  风险文件: {recon_summary.get('risk_files', 0)}")
            print(f"  依赖数量: {recon_summary.get('total_dependencies', 0)}")
            
            # 审计结果
            audit = result.get("scan_result", {}).get("audit", {})
            audit_summary = audit.get("summary", {})
            print("\n【审计阶段】")
            print(f"  发现漏洞: {audit_summary.get('total_vulnerabilities', 0)}")
            
            severity = audit_summary.get("severity_counts", {})
            print(f"    严重: {severity.get('critical', 0)}")
            print(f"    高危: {severity.get('high', 0)}")
            print(f"    中危: {severity.get('medium', 0)}")
            print(f"    低危: {severity.get('low', 0)}")
            
            # 验证结果
            verify = result.get("scan_result", {}).get("verification", {})
            verify_summary = verify.get("summary", {})
            print("\n【验证阶段】")
            print(f"  确认漏洞: {verify_summary.get('confirmed', 0)}")
            print(f"  误报数量: {verify_summary.get('false_positives', 0)}")
            print(f"  需要修复: {verify_summary.get('critical_fixes_needed', 0) + verify_summary.get('high_fixes_needed', 0)}")
            
            # 总体摘要
            summary = result.get("scan_result", {}).get("summary", {})
            print("\n" + "=" * 60)
            print("总体评估")
            print("=" * 60)
            print(f"  扫描时间: {summary.get('scan_timestamp', 'N/A')}")
            print(f"  风险等级: {'高' if severity.get('critical', 0) > 0 else '中' if severity.get('high', 0) > 0 else '低'}")
            
            # 显示报告路径
            report_paths = result.get("report_paths", {})
            if report_paths:
                print("\n报告已生成:")
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