# AI_Novel

本地化人机协作长篇小说创作系统。作者负责顶层创意（大纲、细纲、章节摘要），AI 根据既定设定自动生成符合要求的正文内容。

**目标：** 120 万字长篇创作，约 600 章。

---

## 核心特性

- **多用户 + 多作品支持** — 注册登录，独立管理多部小说的世界观、人物、章节
- **四层级纲要生成** — Arc 模型 + 三级大纲，SSE 流式生成完整故事框架
- **章节流式生成** — 基于提示词模板 + 世界观注入 + 人物关联，AI 逐章生成正文
- **世界观编辑器** — 分区块 Markdown 编辑（背景/地理/历史/力量体系等），注入预览
- **人物管理** — 人物 CRUD + 关系图（图谱数据），关联到章节自动注入 prompt
- **提示词模板库** — 带 YAML frontmatter 的 Markdown 模板，变量自动补全与预览
- **Prompt Injection 2.0** — 动态上下文注入面板，灵活控制注入变量内容
- **模型路由配置** — 三层架构（API 配置 → Plan → 任务绑定），支持 Round-Robin 轮询
- **管理员模式** — Ctrl+U 快捷键进入，提示词预览与生成调试

---

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000/docs for the interactive API documentation.

### 前端

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 for the Vite dev server.

### 环境变量

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

### 初始化

```bash
python init_db.py      # 创建/初始化 SQLite 数据库表
```

启动后，访问前端页面注册第一个用户，登录后即可开始创作。

---

## 项目文档

| 文档 | 说明 |
|------|------|
| [docs/design.md](docs/design.md) | 完整架构设计文档 |
| [docs/task_moc.md](docs/task_moc.md) | 分阶段任务拆分 |
| [docs/progress.md](docs/progress.md) | 当前进度与完成状态 |
| [docs/phase2_acceptance.md](docs/phase2_acceptance.md) | Phase 2 验收报告 |

---

## 技术栈

**前端：** Vite 5 + Vue 3.4+ + Vue Router 4 + Pinia 2 + Naive UI 2 + Tiptap 2 + axios

**后端：** Python 3.11+ + FastAPI 0.110+ + SQLAlchemy 2.x + SQLite + loguru + httpx + Pydantic v2

---

## 目录结构

```
AI_Novel/
├── backend/
│   ├── main.py                   # FastAPI 入口，路由注册
│   ├── config.py                 # 配置读取（.env + config.json）
│   ├── database.py               # SQLAlchemy 引擎 + Session
│   ├── logger.py                 # loguru 日志配置
│   ├── init_db.py                # 数据库初始化脚本
│   ├── routers/                  # REST 端点（按模块分文件）
│   ├── services/                 # 业务逻辑层
│   ├── models/                   # SQLAlchemy ORM 模型
│   ├── repositories/             # 数据访问层（Repository 模式）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/                # 页面组件
│   │   ├── stores/               # Pinia 状态管理
│   │   ├── api/                  # Axios + SSE API 封装
│   │   └── components/           # 通用组件
│   ├── vite.config.js
│   └── package.json
├── data/
│   ├── config.json               # 模块开关 + 系统配置 + 版本号
│   ├── worldview.json            # 世界观设定
│   ├── map.json                  # 地图数据（Vue Flow 格式）
│   ├── writing_style.json        # 全局写作风格
│   └── templates/                # 提示词模板（.md 文件）
├── docs/                         # 项目文档
├── logs/                         # 自动生成的日志文件
├── novel.db                      # SQLite 数据库
├── .env                          # API Keys（不提交 git）
├── .env.example
└── README.md
```

---

## 开发阶段

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 1 — MVP 核心可用 | ✅ 完成 | 章节 CRUD、模型路由、生成链路、基础编辑器 |
| Phase 2 — 世界观管理 | ✅ 完成 | 世界观、人物、模板库、多用户多作品、纲要生成 |
| Phase 3 — 高级功能 | ⏳ 待开始 | 地图、时间线、批量生成、日志查看、版本历史 |
| Phase 4 — 完善体验 | ⏳ 待开始 | 仪表板、剧情线、物品追踪、导出 |
