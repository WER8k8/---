# 异步数据库技术学习总结

**学习时间**: 2026-05-23  
**学习者**: 小鹅  
**学习目的**: 解决SourceChain-GEO项目合并到UJ项目时的架构冲突（SourceChain使用asyncpg+raw SQL，UJ使用SQLAlchemy ORM）

---

## 一、核心问题回顾

### 1.1 架构冲突描述
- **SourceChain项目**: 使用 `asyncpg` + **原生SQL**（raw SQL）- 高性能但数据库耦合
- **UJ项目**: 使用 `SQLAlchemy ORM` + **ORM模型** - 易维护但性能稍低
- **冲突点**: 两个项目的数据库访问层完全不兼容，无法直接合并代码

### 1.2 技术解决方案探索
通过系统学习科技巨头的最佳实践，确定采用 **`databases`库** 作为桥接方案：
- `databases`库提供统一的异步数据库接口
- 支持 PostgreSQL (`asyncpg`) 和 SQLite (`aiosqlite`) 双数据库
- 允许在SQLAlchemy ORM项目中嵌入原生SQL操作

---

## 二、科技巨头技术学习总结

### 2.1 微软 (Microsoft) - FastAPI + Azure PostgreSQL 最佳实践

**学习来源**: [Microsoft Learn - FastAPI tutorial](https://learn.microsoft.com/en-us/azure/app-service/tutorial-python-postgresql-app-fastapi)

#### 核心学习点：

1. **异步引擎配置** - 生产级配置模板
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import os

# 异步引擎配置 - 支持本地和Azure环境
DB_HOST = os.getenv("DBHOST", "localhost")
DB_PORT = os.getenv("DBPORT", "5432")
DB_NAME = os.getenv("DBNAME", "youding_dev")
DB_USER = os.getenv("DBUSER", "postgres")
DB_PASS = os.getenv("DBPASS", "password")

# SQLAlchemy连接URL格式
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 创建异步引擎 - 关键配置参数
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 生产环境关闭
    pool_size=5,  # 连接池大小
    max_overflow=10,  # 最大溢出连接数
    pool_timeout=30,  # 获取连接超时时间
    pool_recycle=1800,  # 连接回收时间(30分钟)
    connect_args={
        "ssl": "require"  # Azure PostgreSQL强制SSL
    }
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()
```

2. **FastAPI依赖注入模式** - 会话生命周期管理
```python
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging

async def get_db_session() -> AsyncSession:
    """FastAPI依赖注入 - 异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logging.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed"
            )
        except Exception as e:
            await session.rollback()
            logging.error(f"Session error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
```

3. **Azure环境适配** - 生产环境配置管理
```python
# Azure App Service环境变量注入
if os.getenv("WEBSITE_HOSTNAME"):  # Azure环境变量
    # 解析Azure自动生成的连接字符串
    env_connection_string = os.getenv("AZURE_POSTGRESQL_CONNECTIONSTRING")
    details = dict(item.split('=') for item in env_connection_string.split())
    
    # 转换为SQLAlchemy URL格式
    DATABASE_URL = (
        f"postgresql+asyncpg://{quote_plus(details['user'])}:{quote_plus(details['password'])}"
        f"@{details['host']}:{details['port']}/{details['dbname']}?sslmode={details['sslmode']}"
    )
else:
    # 本地环境使用.env文件
    load_dotenv()
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

#### 微软最佳实践总结：
- ✅ **连接池配置**: 必须设置`pool_size`、`max_overflow`、`pool_timeout`
- ✅ **SSL安全**: Azure PostgreSQL强制`sslmode=require`
- ✅ **错误处理**: 捕获`SQLAlchemyError`，执行`rollback()`
- ✅ **日志调试**: 使用`logging`模块，不在生产环境开启`echo=True`
- ✅ **环境隔离**: 本地`.env` vs Azure应用设置，避免硬编码敏感信息

---

### 2.2 苹果 (Apple) - Swift 并发编程范式

**学习来源**: [Apple Developer - Concurrency](https://developer.apple.com/documentation/swift/concurrency)

#### 核心学习点：

1. **async/await并发模型** - 现代异步编程基础
```swift
// Swift的async/await - 非阻塞挂起
func fetchData() async throws -> Data {
    let (data, _) = try await URLSession.shared.data(from: url)
    return data
}

// 调用异步函数 - 必须用在async上下文中
Task {
    do {
        let data = try await fetchData()
        let result = try await parseData(data)
        print(result)
    } catch {
        print("Error: \(error)")
    }
}
```

2. **Actor模型** - 解决数据竞争
```swift
// Actor保护共享状态 - 线程安全
actor DatabaseManager {
    private var connections: [String: Connection] = [:]
    
    func getConnection(for database: String) -> Connection {
        // Actor内部访问 - 线程安全
        if let conn = connections[database] {
            return conn
        }
        let newConn = Connection(database: database)
        connections[database] = newConn
        return newConn
    }
}

// 跨Actor访问 - 需要await
let manager = DatabaseManager()
let conn = await manager.getConnection(for: "users_db")
```

3. **结构化并发** - TaskGroup管理并发任务
```python
# Swift的TaskGroup - 结构化并发（类似Python的asyncio.gather）
func fetchMultipleData(urls: [URL]) async throws -> [Data] {
    try await withThrowingTaskGroup(of: Data.self) { group in
        var results: [Data] = []
        
        # 添加并发任务
        for url in urls {
            group.addTask {
                try await URLSession.shared.data(from: url).0
            }
        }
        
        # 收集结果
        for try await data in group {
            results.append(data)
        }
        
        return results
    }
}
```

4. **CoreData异步操作** - iOS数据库最佳实践
```swift
// CoreData异步查询 - 不阻塞UI
let context = persistentContainer.newBackgroundContext()
await context.perform {
    let fetchRequest = NSFetchRequest<Entity>(entityName: "User")
    let results = try? context.fetch(fetchRequest)
    // 处理结果
}

// 批量操作 - 高性能
let batchInsert = NSBatchInsertRequest(entityName: "User", objects: users)
_ = try? context.execute(batchInsert)
```

#### 苹果最佳实践总结：
- ✅ **Actor隔离**: 用Actor保护共享状态，避免数据竞争
- ✅ **结构化并发**: TaskGroup管理生命周期，避免任务泄漏
- ✅ **协作式取消**: 检查`Task.isCancelled`，优雅停止任务
- ✅ **CoreData性能**: 使用`NSBatchInsertRequest`批量操作，后台上下文执行

---

### 2.3 SQLAlchemy 2.0 官方异步模式

**学习来源**: [SQLAlchemy 2.0 Async IO](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

#### 核心学习点：

1. **异步引擎和会话** - 标准配置
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# 异步引擎
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

# 异步会话工厂
AsyncSessionFactory = async_sessionmaker(async_engine, class_=AsyncSession)

# 声明基类
Base = declarative_base()
```

2. **异步会话使用** - 上下文管理器
```python
async def get_user(user_id: int):
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user
```

3. **异步迁移** - 使用Alembic
```python
# Alembic异步迁移配置
# env.py
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context

async def run_migrations_online():
    connectable = AsyncEngine(
        engine=engine,
        synchronous_engine_cls=Engine
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(context.run_migrations)
```

#### SQLAlchemy 2.0最佳实践：
- ✅ **异步会话**: 使用`async with AsyncSessionFactory() as session`
- ✅ **异步查询**: `await session.execute(select(...))`
- ✅ **异步迁移**: Alembic + `connection.run_sync()`
- ✅ **连接管理**: 异步引擎自动管理连接池

---

### 2.4 databases库 - 统一异步数据库接口

**学习来源**: [encode/databases](https://www.encode.io/databases/)

#### 核心学习点：

1. **统一数据库接口** - 支持多种数据库
```python
from databases import Database

# PostgreSQL + asyncpg
postgres_db = Database("postgresql://user:pass@localhost/youding")

# SQLite + aiosqlite  
sqlite_db = Database("sqlite:///youding_dev.db")

# MySQL + aiomysql
mysql_db = Database("mysql://user:pass@localhost/youding")
```

2. **连接生命周期** - 应用启动/关闭管理
```python
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup():
    await postgres_db.connect()

@app.on_event("shutdown")
async def shutdown():
    await postgres_db.disconnect()
```

3. **异步查询操作** - 原生SQL执行
```python
# 查询多条记录
query = "SELECT * FROM users WHERE active = :active"
rows = await postgres_db.fetch_all(query=query, values={"active": True})

# 查询单条记录
query = "SELECT * FROM users WHERE id = :id"
user = await postgres_db.fetch_one(query=query, values={"id": 1})

# 查询单个值
query = "SELECT count(*) FROM users"
count = await postgres_db.fetch_val(query=query)

# 执行写入操作
query = "INSERT INTO users(name, email) VALUES(:name, :email)"
last_record_id = await postgres_db.execute(query=query, values={"name": "John", "email": "john@example.com"})
```

4. **事务管理** - 手动事务控制
```python
async with postgres_db.transaction():
    await postgres_db.execute("INSERT INTO users VALUES (1, 'John')")
    await postgres_db.execute("INSERT INTO profiles VALUES (1, 'Developer')")
    # 如果这里抛出异常，两个INSERT都会回滚
```

#### databases库最佳实践：
- ✅ **统一接口**: 同一套代码支持PostgreSQL/SQLite/MySQL
- ✅ **原生SQL**: 可以写原生SQL，性能最优
- ✅ **事务支持**: `async with db.transaction()`自动管理事务
- ✅ **返回值处理**: `execute()`返回最后插入行的ID（自动处理`RETURNING`）

---

## 三、技术方案确定：databases库桥接方案

### 3.1 方案选择理由

通过学习科技巨头的最佳实践，确定采用 **databases库** 作为桥接方案：

1. **兼容性**: databases库支持PostgreSQL(asyncpg)和SQLite(aiosqlite)，完美适配UJ项目当前使用SQLite的场景
2. **统一性**: 提供统一的异步数据库接口，SourceChain的代码只需最小修改即可运行
3. **性能**: 支持原生SQL操作，性能接近直接使用asyncpg
4. **成熟度**: encode/databases是Starlette/FastAPI生态的官方推荐库，社区活跃

### 3.2 具体修改方案

#### 修改前 (SourceChain原始代码):
```python
# SourceChain使用asyncpg原生连接
import asyncpg

async def get_lead_summary(project_id: int, start_date: date, end_date: date):
    conn = await asyncpg.connect()
    row = await conn.fetchrow("""
        SELECT COUNT(*) as total_count,
               COUNT(*) FILTER (WHERE status = 'NEW') as new_count
        FROM lead_inquiries 
        WHERE project_id = $1 AND created_at BETWEEN $2 AND $3
    """, project_id, start_date, end_date)
    await conn.close()
    return row
```

#### 修改后 (UJ项目适配代码):
```python
# UJ项目使用databases库统一接口
from databases import Database

# 创建databases连接 - 支持SQLite和PostgreSQL
geo_db = Database("sqlite:///./youding_dev.db")

async def get_lead_summary(project_id: int, start_date: date, end_date: date):
    # databases库 - 统一接口
    query = """
        SELECT COUNT(*) as total_count,
               COUNT(*) FILTER (WHERE status = 'NEW') as new_count
        FROM lead_inquiries 
        WHERE project_id = :project_id AND created_at BETWEEN :start_date AND :end_date
    """
    row = await geo_db.fetch_one(
        query=query, 
        values={"project_id": project_id, "start_date": start_date, "end_date": end_date}
    )
    return row
```

#### 关键修改点：

1. **导入变更**: `import asyncpg` → `from databases import Database`
2. **连接管理**: `asyncpg.connect()` → `Database("sqlite:///...")`
3. **参数格式**: `$1, $2` → `:param_name`（命名参数）
4. **执行方法**: `conn.fetchrow()` → `geo_db.fetch_one()`
5. **返回值**: `await conn.close()` → 连接由databases自动管理

---

## 四、立即行动计划

### 4.1 当前任务状态

- ✅ **数据库层已完成**: 创建了8个GEO表
- ✅ **模型层已完成**: 创建了Pydantic schemas (geo_schemas.py)
- ⚠️ **服务层未完成**: repositories.py已复制，但未修改完成

### 4.2 下一步行动

**立即开始修改 `repositories.py`**:

1. **修改导入语句**:
   - 删除 `import asyncpg`
   - 添加 `from databases import Database`
   - 添加 `from app.geo_engine.database import geo_db`

2. **修改函数签名**:
   - 删除 `asyncpg.Connection` 参数
   - 添加 `database: Database = Depends(get_db_connection)`

3. **修改数据库操作**:
   - `connection.fetch()` → `geo_db.fetch_all()`
   - `connection.fetchrow()` → `geo_db.fetch_one()`
   - `connection.fetchval()` → `geo_db.fetch_val()`
   - `connection.execute()` → `geo_db.execute()`

4. **修改参数格式**:
   - `$1, $2, $3` → `:param1, :param2, :param3`（命名参数）

5. **删除RETURNING语法**:
   - PostgreSQL的`RETURNING id` → databases库`execute()`自动返回ID

### 4.3 时间估算

- **修改16个函数**: 预计1-1.5小时
- **语法检查**: 15分钟
- **功能测试**: 30分钟
- **总计**: 约2小时

---

## 五、学习心得总结

### 5.1 科技巨头技术特点

1. **微软**: 注重生产环境适配，Azure服务集成，错误处理完善
2. **苹果**: 注重开发体验，现代编程范式，类型安全
3. **SQLAlchemy**: 注重ORM抽象，跨数据库兼容，生态完整
4. **databases**: 注重统一接口，原生SQL性能，轻量级设计

### 5.2 异步数据库设计原则

1. **连接池管理**: 必须配置合理的连接池参数
2. **错误处理**: 必须捕获异常并执行rollback()
3. **事务管理**: 写操作必须使用事务保证一致性
4. **环境适配**: 本地开发 vs 生产环境的配置分离
5. **日志监控**: 合理的日志记录帮助排查问题

### 5.3 避免的坑

1. **不要混用异步库**: asyncpg和aiosqlite不能直接混用
2. **不要忽略SSL**: 生产环境数据库连接必须启用SSL
3. **不要硬编码凭证**: 使用环境变量或密钥管理服务
4. **不要忘记关闭连接**: 使用上下文管理器自动管理

---

**文档版本**: v1.0  
**最后更新**: 2026-05-23 05:54  
**下一步**: 开始修改 `repositories.py` 文件