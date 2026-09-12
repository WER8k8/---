"""
Talking-Stick 文件锁机制
确保同一时间只有一个Agent可以访问代码仓库
"""

import asyncio
import time
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass


@dataclass
class LockInfo:
    """锁信息"""
    lock_id: str
    target_path: str
    acquired_at: float
    timeout: int


class FileLock:
    """文件锁管理器"""
    def __init__(self, lock_dir: str = ".talking-stick-locks", timeout: int = 300):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param lock_dir: 参数 lock_dir
        :param timeout: 参数 timeout
        :return: 返回处理结果。
        """
        self.lock_dir = Path(lock_dir)
        self.timeout = timeout
        self._locks: dict[str, LockInfo] = {}
        # 确保锁目录存在
        self.lock_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_lock_path(self, target_path: str) -> Path:
        """获取锁文件路径"""
        # 使用目标路径的哈希作为锁文件名
        import hashlib
        path_hash = hashlib.md5(target_path.encode()).hexdigest()
        return self.lock_dir / f"{path_hash}.lock"
    
    async def acquire(self, target_path: str, timeout: Optional[int] = None) -> str:
        """获取文件锁"""
        timeout = timeout or self.timeout
        lock_path = self._get_lock_path(target_path)
        lock_id = f"lock_{int(time.time() * 1000)}"
        start_time = time.time()
        while True:
            try:
                # 尝试创建锁文件
                if not lock_path.exists():
                    lock_path.write_text(lock_id, encoding='utf-8')
                    # 记录锁信息
                    self._locks[lock_id] = LockInfo(
                        lock_id=lock_id,
                        target_path=target_path,
                        acquired_at=time.time(),
                        timeout=timeout
                    )
                    return lock_id
                else:
                    # 检查锁是否超时
                    lock_content = lock_path.read_text(encoding='utf-8').strip()
                    if lock_content in self._locks:
                        lock_info = self._locks[lock_content]
                        if time.time() - lock_info.acquired_at > lock_info.timeout:
                            # 锁已超时，强制释放
                            await self._force_release(lock_content)
                            continue
                    
                    # 等待后重试
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"获取文件锁超时: {target_path}")
                    
                    await asyncio.sleep(1)
                    
            except (IOError, OSError) as e:
                # 文件操作失败，等待后重试
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"获取文件锁失败: {target_path}, 错误: {e}")
                
                await asyncio.sleep(1)
    
    async def release(self, lock_id: str) -> None:
        """释放文件锁"""
        if lock_id not in self._locks:
            return
        
        lock_info = self._locks[lock_id]
        lock_path = self._get_lock_path(lock_info.target_path)
        try:
            # 删除锁文件
            if lock_path.exists():
                lock_path.unlink()
        except (IOError, OSError):
            pass
        
        # 移除锁记录
        del self._locks[lock_id]
    
    async def _force_release(self, lock_id: str) -> None:
        """强制释放文件锁"""
        if lock_id in self._locks:
            lock_info = self._locks[lock_id]
            lock_path = self._get_lock_path(lock_info.target_path)
            try:
                if lock_path.exists():
                    lock_path.unlink()
            except (IOError, OSError):
                pass
            
            del self._locks[lock_id]
    
    @asynccontextmanager
    async def lock(self, target_path: str, timeout: Optional[int] = None):
        """上下文管理器，自动获取和释放锁"""
        lock_id = await self.acquire(target_path, timeout)
        try:
            yield lock_id
        finally:
            await self.release(lock_id)
    
    def is_locked(self, target_path: str) -> bool:
        """检查目标路径是否被锁定"""
        lock_path = self._get_lock_path(target_path)
        return lock_path.exists()
    
    def get_lock_info(self, lock_id: str) -> Optional[LockInfo]:
        """获取锁信息"""
        return self._locks.get(lock_id)
    
    async def cleanup(self) -> None:
        """清理所有锁"""
        # 释放所有持有的锁
        for lock_id in list(self._locks.keys()):
            await self.release(lock_id)
        
        # 清理过期的锁文件
        try:
            for lock_file in self.lock_dir.glob("*.lock"):
                try:
                    # 检查锁文件是否过期（超过24小时）
                    if lock_file.stat().st_mtime < time.time() - 86400:
                        lock_file.unlink()
                except (IOError, OSError):
                    pass
        except Exception:
            pass
