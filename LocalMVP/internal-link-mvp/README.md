# SEO 内链 MVP

这是一个用于 SEO 内链审核的单人本机测试工具。当前阶段提供可运行的项目骨架：

- FastAPI 后端：`http://localhost:8000`
- Vite React 前端：`http://localhost:5173`
- 通过 Docker Compose 管理 PostgreSQL 16
- 健康检查 API：`GET /api/health`

## 当前阶段

已完成：Phase 1-8 的本机 MVP 主流程。

已实现：页面导入、数据库模型、正文解析、候选锚文本、链接推荐、审核决策、插入预览、本地写回快照、回滚、LLM 配置持久化、样例数据和基础测试。

## 前置条件

- Python 3.11+
- Node.js and npm
- Docker Desktop，用于运行 PostgreSQL

在 Windows PowerShell 中，`npm.ps1` 可能会被执行策略拦截。请优先使用 `npm.cmd`。

## 启动 PostgreSQL

需要先安装并启动 Docker Desktop。

```bash
docker compose up -d
```

如果尚未安装 Docker，请先安装 Docker Desktop：

https://www.docker.com/products/docker-desktop/

## 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

如果默认 PyPI 连接较慢，或返回的元数据不完整，可以改用清华镜像：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e .
alembic upgrade head
```

macOS/Linux 激活虚拟环境：

```bash
source .venv/bin/activate
```

健康检查：

```bash
curl http://localhost:8000/api/health
```

预期响应：

```json
{"status":"ok"}
```

## 启动前端

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

如果安装依赖时卡在网络审计或资助信息请求，可以使用：

```bash
npm.cmd install --ignore-scripts --no-audit --no-fund
```

打开：

```text
http://localhost:5173
```

## 运行测试

```bash
cd backend
.venv\Scripts\activate
pytest
```

## 本机验收脚本

```powershell
PowerShell -ExecutionPolicy Bypass -File scripts\verify-local.ps1
```

该脚本会运行后端测试、前端构建，并在检测到 Docker 后启动 PostgreSQL、执行 `alembic upgrade head`。如果 Docker 尚未安装，它会明确提示并跳过真实 PostgreSQL 验收。

## 本机一键启动

Windows 用户在依赖安装完成后，可以使用以下任一入口：

- `start-local.vbs`：推荐双击入口，完全隐藏启动窗口。
- `start-local.bat`：兼容入口，Windows 可能会短暂闪过 `cmd.exe` 窗口，但不会再输出乱码命令错误。

启动脚本会检查 Docker，启动 PostgreSQL，启动后端和前端，然后打开浏览器。如果检测不到 Docker，它会把原因写入 `logs/start-local.log` 并停止。`.bat` 本身保持纯 ASCII，避免 Windows `cmd.exe` 读取中文脚本时出现乱码命令。

Docker Desktop 需要手动下载安装并启动，本项目不会自动安装系统级软件：

```text
https://www.docker.com/products/docker-desktop/
```
