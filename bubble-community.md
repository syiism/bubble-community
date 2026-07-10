# 段评气泡社区

一个基于 SVG 的气泡样式创作与分享平台。

## 技术栈

| 层次 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | - |
| 后端语言 | Python | 3.14 |
| 数据库 | MySQL / MariaDB | - |
| ORM框架 | SQLAlchemy | 2.0+ |
| 数据库驱动 | PyMySQL | - |
| 前端框架 | Vue | 3.5.x |
| 前端构建 | Vite | 8.1.x |
| CSS框架 | TailwindCSS | 3.4.x |
| 部署方式 | Docker | - |

## 项目结构

```
bubble-community/
├── backend/                    # 后端代码
│   ├── app/                    # 应用源码
│   │   ├── modules/            # 数据库模块（SQLAlchemy）
│   │   │   ├── __init__.py     # 模块导出
│   │   │   ├── database.py     # SQLAlchemy 引擎配置
│   │   │   ├── repositories.py # 数据库操作封装（Repository模式）
│   │   │   ├── user.py         # User 模型（users 表）
│   │   │   ├── bubble.py       # Bubble 模型（bubbles 表）
│   │   │   ├── user_current_bubble.py   # 用户当前气泡模型
│   │   │   ├── imported_bubble.py       # 导入气泡模型
│   │   │   ├── user_favorite.py         # 用户收藏模型
│   │   │   └── session_model.py         # Session 模型（sessions 表）
│   │   ├── routers/            # API路由模块
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 用户认证路由
│   │   │   ├── bubbles.py      # 气泡管理路由
│   │   │   └── user.py         # 用户设置路由
│   │   ├── __init__.py
│   │   ├── auth.py             # 认证核心逻辑
│   │   ├── config.py           # 配置项
│   │   ├── db.py               # 旧版数据库连接（已弃用）
│   │   ├── main.py             # 应用入口
│   │   ├── schema.sql          # 旧版表结构（已弃用）
│   │   ├── seed.py             # 初始数据填充
│   │   ├── session.py          # Session管理
│   │   ├── svg_util.py         # SVG渲染工具
│   │   ├── ucenter.py          # UCenter集成
│   │   └── official_bubbles.json # 官方气泡数据
│   ├── entrypoint.sh           # Docker启动脚本
│   └── pyproject.toml          # Python依赖配置
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── components/         # Vue组件
│   │   │   ├── BubbleCard.vue
│   │   │   ├── BubbleList.vue
│   │   │   ├── Editor.vue
│   │   │   ├── Navbar.vue
│   │   │   └── Toast.vue
│   │   ├── data/
│   │   │   └── mockData.js     # Mock数据
│   │   ├── router/
│   │   │   └── index.js        # 路由配置
│   │   ├── stores/
│   │   │   └── auth.js         # 状态管理
│   │   ├── utils/
│   │   │   └── svgHelper.js    # SVG辅助工具
│   │   ├── views/              # 页面视图
│   │   │   ├── Home.vue
│   │   │   ├── Login.vue
│   │   │   ├── Profile.vue
│   │   │   └── Register.vue
│   │   ├── App.vue
│   │   ├── api.js              # API调用封装
│   │   ├── main.js
│   │   └── style.css
│   ├── dist/                   # 前端构建产物
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── Dockerfile                  # Docker镜像构建
├── docker-compose.yml          # Docker Compose配置
└── entrypoint.sh               # 项目启动脚本
```

## 核心功能

### 1. 用户认证

- **注册**: 通过 vossc.com Discuz! 论坛进行注册，自动同步用户信息
- **登录**: 支持用户名密码登录，集成 Discuz! 认证系统
- **退出**: 清除本地 Session 和 Discuz! Cookie

### 2. 气泡管理

- **创建气泡**: 用户可上传自定义 SVG 模板，设置名称、描述、颜色等
- **编辑气泡**: 修改已创建气泡的各项属性
- **删除气泡**: 删除自己创建的气泡（级联删除关联数据）
- **可见性设置**: 切换气泡的公开/私有状态
- **分享气泡**: 生成分享码，供他人导入使用
- **导入气泡**: 通过分享码导入他人的气泡样式
- **收藏气泡**: 收藏喜欢的气泡样式
- **设置当前气泡**: 选择当前使用的气泡样式

### 3. SVG 渲染

- 根据模板动态填充颜色和文字颜色
- 支持生成 12 个气泡的预览图
- 实时预览气泡效果

### 4. 用户设置

- 设置/修改署名（用于气泡作者展示）
- 署名唯一性校验

## 数据库设计

### 用户表 (users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 用户ID（主键，Discuz! UID） |
| username | VARCHAR(64) | 用户名（唯一） |
| author_name | VARCHAR(32) | 署名（可空，唯一） |
| avatar_url | VARCHAR(255) | 头像URL（可空） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

模型文件: [modules/user.py](file:///home/muyang/work/modelscope/bubble-community/backend/app/modules/user.py)

### 气泡表 (bubbles)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 气泡ID（主键，自增） |
| user_id | BIGINT | 创建者ID（可空，官方气泡为空） |
| name | VARCHAR(64) | 气泡名称 |
| description | VARCHAR(120) | 气泡描述 |
| svg_template | TEXT | SVG模板内容 |
| color | VARCHAR(32) | 颜色值 |
| text_color | VARCHAR(32) | 文字颜色值 |
| is_public | BOOLEAN | 是否公开 |
| is_official | BOOLEAN | 是否官方气泡 |
| share_code | VARCHAR(32) | 分享码（唯一） |
| author_name | VARCHAR(32) | 作者署名 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

模型文件: [modules/bubble.py](file:///home/muyang/work/modelscope/bubble-community/backend/app/modules/bubble.py)

### 用户当前气泡表 (user_current_bubble)

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | BIGINT | 用户ID（主键） |
| bubble_id | BIGINT | 当前气泡ID |
| set_at | DATETIME | 设置时间 |

模型文件: [modules/user_current_bubble.py](file:///home/muyang/work/modelscope/bubble-community/backend/app/modules/user_current_bubble.py)

### 导入气泡表 (imported_bubbles)

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | BIGINT | 用户ID（主键） |
| bubble_id | BIGINT | 导入的气泡ID（主键） |
| imported_at | DATETIME | 导入时间 |

模型文件: [modules/imported_bubble.py](file:///home/muyang/work/modelscope/bubble-community/backend/app/modules/imported_bubble.py)

### 用户收藏表 (user_favorites)

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | BIGINT | 用户ID（主键） |
| bubble_id | BIGINT | 收藏的气泡ID（主键） |
| favorited_at | DATETIME | 收藏时间 |

模型文件: [modules/user_favorite.py](file:///home/muyang/work/modelscope/bubble-community/backend/app/modules/user_favorite.py)

### 会话表 (sessions)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | Session ID（主键，UUID） |
| user_id | BIGINT | 用户ID |
| username | VARCHAR(64) | 用户名 |
| expires_at | DATETIME | 过期时间 |
| created_at | DATETIME | 创建时间 |

模型文件: [modules/session_model.py](file:///home/muyang/work/modelscope/bubble-community/backend/app/modules/session_model.py)

## 数据库模块说明

### modules/database.py

SQLAlchemy 核心配置，包含：
- `engine`: 数据库连接引擎
- `SessionLocal`: 会话工厂
- `Base`: 所有模型的基类
- `get_db()`: FastAPI 依赖注入函数
- `get_db_context()`: 上下文管理器
- `create_all_tables()`: 自动创建所有表

### modules/repositories.py

Repository 模式封装，每个表对应一个 Repository 类：

| Repository | 说明 |
|------------|------|
| `UserRepository` | 用户数据操作 |
| `BubbleRepository` | 气泡数据操作 |
| `UserCurrentBubbleRepository` | 当前气泡操作 |
| `ImportedBubbleRepository` | 导入气泡操作 |
| `UserFavoriteRepository` | 收藏操作 |
| `SessionRepository` | 会话管理 |

## API 接口文档

### 认证接口 (/api/auth)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/check-username?username=xxx` | 检查用户名是否可用 |
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录 |
| GET | `/me` | 获取当前用户信息 |
| POST | `/logout` | 用户退出 |

### 气泡接口 (/api/bubbles)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 获取气泡列表 |
| POST | `/` | 创建气泡 |
| PUT | `/{bubble_id}` | 更新气泡 |
| DELETE | `/{bubble_id}` | 删除气泡 |
| POST | `/visibility` | 设置气泡可见性 |
| POST | `/share` | 生成分享码 |
| POST | `/redeem` | 兑换分享码（导入气泡） |
| POST | `/current` | 设置当前气泡 |
| POST | `/favorite` | 设置收藏状态 |

### 用户接口 (/api/user)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/author-name` | 设置署名 |

## 本地开发

### 环境要求

- Python 3.14+
- Node.js 22+
- MySQL / MariaDB 5.7+

### 后端启动

```bash
cd backend

# 安装依赖
pip install uv
uv sync

# 配置环境变量（可选，默认值见 config.py）
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=123456
export DB_NAME=bubble_community

# 填充初始数据（自动创建数据库和表结构）
uv run python -m app.seed

# 启动服务
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

> **注意**: 表结构通过 SQLAlchemy 的 `Base.metadata.create_all()` 自动创建，无需手动执行 `schema.sql`。

### 前端启动

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

前端开发服务器运行在 `http://localhost:5173`，后端 API 运行在 `http://localhost:8001`。

## Docker 部署

### 使用 docker-compose

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

服务启动后访问 `http://localhost:8001/bubble-community`。

### 构建镜像

```bash
docker build -t bubble-community .
```

### 运行容器

```bash
docker run -d \
  -p 8001:8001 \
  -e DB_HOST=localhost \
  -e DB_PORT=3306 \
  -e DB_USER=bubble_community \
  -e DB_PASSWORD=xp3jEFdc5HsZKC7H \
  -e DB_NAME=bubble_community \
  bubble-community
```

## 配置说明

后端配置通过环境变量进行设置：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DB_HOST | 127.0.0.1 | 数据库主机 |
| DB_PORT | 3306 | 数据库端口 |
| DB_USER | root | 数据库用户名 |
| DB_PASSWORD | 123456 | 数据库密码 |
| DB_NAME | bubble_community | 数据库名称 |
| UC_KEY | L6r4t3X9I... | UCenter 通信密钥 |

## 注意事项

1. **认证集成**: 用户认证通过 vossc.com 的 Discuz! 论坛实现，注册和登录请求会转发到该论坛进行验证。

2. **前端挂载**: 生产环境中，前端构建产物由后端通过 `SPAStaticFiles` 挂载，统一在 `http://localhost:8001/bubble-community` 提供服务。

3. **Session 管理**: 使用本地 Session 机制，Session ID 通过 Cookie (`bubble_session`) 传递，有效期 2 小时。

4. **Docker 中的 MySQL**: Dockerfile 中安装了 MariaDB，但 `docker-compose.yml` 未定义 MySQL 服务，需要确保数据库已在外部运行或修改配置。

5. **官方气泡**: `seed.py` 会从 `official_bubbles.json` 导入官方气泡数据。

6. **SQLAlchemy**: 项目已迁移至 SQLAlchemy ORM，表结构通过模型定义自动创建，`schema.sql` 已弃用。

7. **Repository 模式**: 数据库操作封装在 Repository 类中，便于维护和测试。
