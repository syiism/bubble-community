import multiprocessing
import os
from dotenv import load_dotenv

# ========== 加载环境变量 ==========
load_dotenv()  # 自动读取 .env 文件

# ========== 基础配置 ==========
# 绑定 IP 和端口（只监听内网，通过 Nginx 访问）
bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8000")

# Worker 数量（CPU核数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# ========== FastAPI 关键配置 ==========
# 必须使用 UvicornWorker（支持 ASGI）
worker_class = "uvicorn.workers.UvicornWorker"

# ========== 性能调优 ==========
max_requests = 1000
max_requests_jitter = 100
timeout = 120
graceful_timeout = 30

# ========== 日志配置 ==========
loglevel = "info"
# accesslog = "/www/server/python_project/bubble-community/backend/logs/access.log"
# errorlog = "/www/server/python_project/bubble-community/backend/logs/error.log"

# 确保日志目录存在
import os
# os.makedirs("/www/server/python_project/bubble-community/backend/logs", exist_ok=True)

# ========== 进程管理 ==========
daemon = False
preload_app = True

# ========== 环境变量（重要！） ==========
# 如果你的应用需要读取 .env 或环境变量，在这里设置
# os.environ["DATABASE_URL"] = "your_db_url"
# os.environ["REDIS_URL"] = "your_redis_url"
