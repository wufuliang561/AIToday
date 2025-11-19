# AIToday - AI 热点资讯聚合平台

AIToday 是一个智能化的 AI 资讯聚合平台，旨在解决 AI 领域信息爆炸的问题。它自动从 YouTube、Reddit、X (Twitter) 和 RSS 等多个高质量信源获取信息，利用大语言模型（LLM）进行翻译、摘要、去重和热点聚合，为用户提供高价值、低噪点的 AI 行业动态。

## 🌟 核心特性

- **多源数据采集**：支持 YouTube, Reddit, X (Twitter), RSS 等多种数据源。
- **智能降噪与去重**：通过算法和 LLM 语义分析，去除重复和低质量内容。
- **AI 驱动处理**：
    - **自动翻译**：将外文标题和内容翻译为中文。
    - **智能摘要**：自动总结长文和推文核心内容。
    - **热点聚合**：自动识别并聚合全网热点事件，生成综述。
- **现代化 UI**：采用 "Neo-Brutalist" 风格的 Clean Grid 设计，专注于内容阅读体验。

## 🛠 技术栈

### Backend (后端)
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL (with SQLAlchemy ORM)
- **Scheduling**: APScheduler (定时任务)
- **AI Integration**: OpenAI API (LangChain)

### Frontend (前端)
- **Framework**: Next.js (React)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React

## 🚀 快速开始

### 前置要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- OpenAI API Key

### 1. 安装与配置

**克隆项目**
```bash
git clone https://github.com/wufuliang561/AIToday.git
cd AIToday
```

**后端配置**
1. 进入后端目录：`cd backend`
2. 创建虚拟环境并安装依赖：
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. 配置环境变量：
   复制 `.env.example` (如果有) 或新建 `.env` 文件，填入以下内容：
   ```env
   OPENAI_API_KEY=your_key
   POSTGRES_SERVER=localhost
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=password
   POSTGRES_DB=aitoday
   # 其他 API Keys (Youtube, Reddit, X)...
   ```

**前端配置**
1. 进入前端目录：`cd frontend`
2. 安装依赖：
   ```bash
   npm install
   ```

### 2. 启动项目

项目根目录提供了便捷的启动脚本：

**启动所有服务 (后端 + 前端)**
```bash
./start.sh
```
*后端运行在 http://localhost:8000，前端运行在 http://localhost:3000*

**停止所有服务**
```bash
./stop.sh
```

### 3. 手动启动 (可选)

如果需要分别启动：

**后端**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**前端**
```bash
cd frontend
npm run dev
```

## 📂 项目结构

### 根目录
- `start.sh`: **一键启动脚本**，同时启动后端 API 和前端页面。
- `stop.sh`: **一键停止脚本**，关闭所有相关服务。
- `prd.md`: **产品需求文档**，详细定义了项目的功能、架构和技术指标。
- `docker-compose.yaml`: Docker 配置文件，用于启动本地 PostgreSQL 数据库。

### Backend (后端) - `backend/`
后端基于 FastAPI 构建，负责数据采集、AI 处理和 API 接口。

- `app/`: 应用核心代码目录
  - `main.py`: **程序入口**，定义 FastAPI 应用和路由。
  - `api/`: **接口层**，定义 HTTP API 路由 (如 `/api/v1/hotspots`)。
  - `core/`: **核心配置**，包含 `config.py` (环境变量读取) 等。
  - `db/`: **数据库层**，包含数据库连接 Session 和基础 Model 定义。
  - `models/`: **数据模型**，定义 SQLAlchemy ORM 模型 (如 `Hotspot`, `RawItem`)。
  - `services/`: **业务逻辑**，包含爬虫 (`collectors/`) 和 AI 处理逻辑。
- `sources.yaml`: **数据源配置**，定义要抓取的 YouTube 频道、RSS 源等。
- `requirements.txt`: Python 依赖列表。
- `alembic/`: 数据库迁移脚本 (如果有)。

### Frontend (前端) - `frontend/`
前端基于 Next.js (App Router) 构建，负责界面展示。

- `src/`: 源代码目录
  - `app/`: **页面路由**，Next.js App Router 的页面定义 (如 `page.tsx`)。
  - `components/`: **组件库**，可复用的 UI 组件 (如 `NewsCard`, `HotspotList`)。
  - `lib/`: **工具库**，包含 API 请求客户端 (`api.ts`) 和通用工具函数。
- `public/`: 静态资源目录 (图片、图标等)。
- `next.config.ts`: Next.js 配置文件。
- `tailwind.config.ts`: Tailwind CSS 样式配置文件。

## 📄 License

[MIT License](LICENSE)
