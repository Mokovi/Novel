# Phase 1 验收文档 — MVP 核心可用

> **目标：** 跑通「写摘要 → 生成正文 → 保存」核心链路，可配置 API Key，可单章生成。
>
> **验收日期：** 2026-05-17
>
> **前置条件：** Python 3.11+、Node.js 18.19.1、npm

---

## 目录

1. [测试环境准备](#1-测试环境准备)
2. [P1-T1 项目骨架](#2-p1-t1-项目骨架)
3. [P1-T2 数据库初始化](#3-p1-t2-数据库初始化)
4. [P1-T3 章节 CRUD](#4-p1-t3-章节-crud)
5. [P1-T4 模型路由配置](#5-p1-t4-模型路由配置)
6. [P1-T5 提示词模板引擎](#6-p1-t5-提示词模板引擎)
7. [P1-T6 流式生成与编辑器](#7-p1-t6-流式生成与编辑器)
8. [端到端里程碑验收](#8-端到端里程碑验收)
9. [边界情况与故障注入](#9-边界情况与故障注入)

---

## 1. 测试环境准备

### 1.1 启动后端

```bash
cd AI_Novel

# 初始化数据库（首次或重置）
python backend/init_db.py

# 启动 FastAPI 开发服务器
uvicorn backend.main:app --reload
```

- 预期：控制台输出 `Application startup complete.`
- **重要：** 启动命令必须在项目根目录 `AI_Novel/` 下执行（即 `backend/` 和 `frontend/` 的父目录），否则 `config.py` 中的 `ROOT_DIR` 路径解析会出错。
- 验证：浏览器打开 `http://localhost:8000/docs`，应看到 Swagger OpenAPI 页面

### 1.2 启动前端

```bash
cd AI_Novel/frontend
npm run dev
```

- 预期：控制台输出 `http://localhost:5173`
- 验证：浏览器打开 `http://localhost:5173`，应看到左侧导航栏 + 右侧内容区

---

## 2. P1-T1 — 项目骨架

### 2.1 目录结构检查

确认以下文件和目录存在：

```
AI_Novel/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置加载
│   ├── database.py          # SQLAlchemy 引擎
│   ├── init_db.py           # 数据库初始化脚本
│   ├── routers/             # REST 路由
│   ├── services/            # 业务逻辑
│   ├── models/              # ORM 模型
│   ├── repositories/        # 数据访问层
│   ├── schemas/             # Pydantic 模型
│   └── requirements.txt     # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── main.js          # Vue 入口
│   │   ├── App.vue          # 根组件
│   │   ├── router/          # Vue Router
│   │   ├── views/           # 页面组件
│   │   ├── stores/          # Pinia 状态
│   │   ├── api/             # HTTP 封装
│   │   ├── components/      # UI 组件
│   │   └── assets/          # 静态资源
│   ├── vite.config.js
│   └── package.json
├── data/
│   ├── config.json          # 模块开关
│   ├── templates/           # 提示词模板
│   ├── worldview.json       # 世界观设定
│   └── writing_style.json   # 写作风格
├── .env.example
└── .gitignore
```

### 2.2 验证项

| # | 操作 | 预期结果 |
|---|------|---------|
| 1 | 访问 `http://localhost:8000/docs` | 返回 Swagger UI，列出所有 API 路由 |
| 2 | 访问 `http://localhost:5173` | 显示左侧导航（工作台/大纲视图/章节编辑器/API 配置） |
| 3 | `git status` 输出中无 `.env` | `.env` 不在 Git 追踪中 |
| 4 | 检查 `data/config.json` | JSON 格式正确，所有模块 `true` |

---

## 3. P1-T2 — 数据库初始化

### 3.1 初始化

```bash
python backend/init_db.py
```

预期输出：
```
Creating database at: /path/to/novel.db
All tables created successfully.
Seeded 5 model route presets.
Database initialization complete.
```

### 3.2 表结构验证

用 SQLite 命令行检查：

```bash
sqlite3 novel.db ".tables"
```

应列出：

| 表名 | 说明 |
|------|------|
| `volumes` | 卷 |
| `chapters` | 章节 |
| `chapter_versions` | 章节版本历史 |
| `characters` | 人物 |
| `character_relations` | 人物关系 |
| `items` | 物品 |
| `item_ownership_history` | 物品归属历史 |
| `world_events` | 世界事件 |
| `event_participants` | 事件参与人物 |
| `model_routes` | 模型路由配置（含 5 条预设） |
| `story_lines` | 剧情线 |
| `chapter_story_lines` | 章节-剧情线关联 |
| `chapter_characters` | 章节-人物关联 |

详细结构检查：

```bash
sqlite3 novel.db ".schema chapters"
```

- `chapters` 表应有外键 `volume_id REFERENCES volumes(id) ON DELETE CASCADE`
- `chapter_versions` 表应有外键 `chapter_id REFERENCES chapters(id) ON DELETE CASCADE`
- `model_routes` 表应有 5 条预设记录，`task_key` 分别为 `outline_design`、`chapter_writing`、`character_design`、`worldbuilding`、`revision`，所有字段为 NULL，`enabled` 为 `0`

---

## 4. P1-T3 — 章节 CRUD

使用 Swagger UI (`http://localhost:8000/docs`) 或 `curl` 测试。

### 4.1 卷操作

| # | 操作 | 请求 | 预期结果 |
|---|------|------|---------|
| 1 | **创建卷** | `POST /api/v1/volumes` `{"title": "第一卷", "description": "序章", "sort_order": 1}` | 201，返回卷对象含 `id: 1` |
| 2 | **创建卷 2** | `POST /api/v1/volumes` `{"title": "第二卷", "sort_order": 2}` | 201，返回 `id: 2` |
| 3 | **列表卷** | `GET /api/v1/volumes` | 200，返回数组含 2 个卷 |

### 4.2 章节操作

| # | 操作 | 请求 | 预期结果 |
|---|------|------|---------|
| 4 | **创建章节** | `POST /api/v1/chapters` `{"volume_id": 1, "title": "第一章 开端", "summary": "主角苏醒", "sort_order": 1}` | 201，`word_count: 0`，`status: "pending"` |
| 5 | **创建章节 2** | `POST /api/v1/chapters` `{"volume_id": 1, "title": "第二章 探索", "summary": "主角探索环境", "sort_order": 2}` | 201 |
| 6 | **创建章节 3** | `POST /api/v1/chapters` `{"volume_id": 2, "title": "第十一章 新篇章", "sort_order": 1}` | 201 |
| 7 | **列表章节** | `GET /api/v1/chapters` | 200，返回 3 个章节 |
| 8 | **按卷过滤** | `GET /api/v1/chapters?volume_id=1` | 200，返回 2 个章节 |
| 9 | **获取详情** | `GET /api/v1/chapters/1` | 200，`title: "第一章 开端"` |
| 10 | **更新内容** | `PUT /api/v1/chapters/1` `{"content": "这是正文内容……", "title": "第一章 觉醒"}` | 200，`content` 和 `title` 更新 |
| 11 | **删除章节** | `DELETE /api/v1/chapters/3` | 204 |
| 12 | **验证删除** | `GET /api/v1/chapters/3` | 404 |
| 13 | **重排序** | `PUT /api/v1/chapters/reorder` `{"items": [{"id": 2, "sort_order": 1}, {"id": 1, "sort_order": 2}]}` | 204 |
| 14 | **验证排序** | `GET /api/v1/chapters` | 章节 2 的 `sort_order` 为 1，章节 1 的 `sort_order` 为 2 |

### 4.3 curl 快捷测试

```bash
# 创建卷
curl -s -X POST http://localhost:8000/api/v1/volumes \
  -H 'Content-Type: application/json' \
  -d '{"title":"测试卷"}' | python -m json.tool

# 创建章节
curl -s -X POST http://localhost:8000/api/v1/chapters \
  -H 'Content-Type: application/json' \
  -d '{"volume_id":1,"title":"测试章","summary":"摘要"}' | python -m json.tool

# 列表
curl -s http://localhost:8000/api/v1/chapters | python -m json.tool
```

---

## 5. P1-T4 — 模型路由配置

### 5.1 初始状态

```bash
curl -s http://localhost:8000/api/v1/model-routes | python -m json.tool
```

预期：返回 5 个任务，所有 `enabled: false`，`api_key_mask: null`

### 5.2 配置章节写作路由

```bash
curl -s -X PUT http://localhost:8000/api/v1/model-routes/chapter_writing \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4o-mini",
    "api_key": "sk-your-real-key-here",
    "api_base_url": "",
    "enabled": true,
    "max_tokens": 4096,
    "temperature": 0.8
  }' | python -m json.tool
```

预期：200，`api_key_mask` 显示 `...-here`，`enabled: true`

### 5.3 验证加密存储

```bash
sqlite3 novel.db "SELECT task_key, api_key_encrypted, enabled FROM model_routes WHERE task_key='chapter_writing';"
```

预期：
- `api_key_encrypted` 字段**不是**明文 `sk-your-real-key-here`，而是 base64 编码的密文
- `enabled` 为 `1`

### 5.4 测试连接

```bash
curl -s -X POST http://localhost:8000/api/v1/model-routes/chapter_writing/test
```

预期（取决于 API Key 有效性）：
- `{"success": true}` — 连接成功
- 或 `{"success": false, "error": "..."}` — 连接失败（HTTP 错误在 expected 范围内）

### 5.5 未配置路由

```bash
# 将路由设为禁用
curl -s -X PUT http://localhost:8000/api/v1/model-routes/chapter_writing \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false}' | python -m json.tool
```

预期：`enabled: false`，其他字段不变

> **验证完成后记得重新启用路由**，否则生成章节会失败。

---

## 6. P1-T5 — 提示词模板引擎

### 6.1 查看默认模板

```bash
curl -s http://localhost:8000/api/v1/templates | python -m json.tool
```

预期：返回列表，含 `chapter_writing_default.md`

### 6.2 读取模板详情

```bash
curl -s http://localhost:8000/api/v1/templates/chapter_writing_default.md | python -m json.tool
```

预期：返回 `file_name`、`frontmatter`（含 `required_variables`）、`body`、`token_estimate`

### 6.3 构建预览

```bash
curl -s -X POST http://localhost:8000/api/v1/templates/build-preview \
  -H 'Content-Type: application/json' \
  -d '{
    "file_name": "chapter_writing_default.md",
    "variables": {
      "chapter_title": "第一章",
      "chapter_summary": "主角醒来",
      "writing_style": "第三人称",
      "worldview": "奇幻世界"
    }
  }' | python -m json.tool
```

预期：
- `prompt` 中 `{{chapter_title}}` 被替换为「第一章」
- `{{chapter_summary}}` 被替换为「主角醒来」
- 条件块 `{{#chapter_outline}}...{{/chapter_outline}}` 因未提供变量而被移除
- `token_estimate` 为整数

### 6.4 缺少必填变量

```bash
curl -s -X POST http://localhost:8000/api/v1/templates/build-preview \
  -H 'Content-Type: application/json' \
  -d '{
    "file_name": "chapter_writing_default.md",
    "variables": {"chapter_title": "第一章"}
  }' | python -m json.tool
```

预期：400 `Missing required template variable(s): chapter_summary, writing_style, worldview`

### 6.5 创建新模板

```bash
curl -s -X POST http://localhost:8000/api/v1/templates \
  -H 'Content-Type: application/json' \
  -d '{
    "file_name": "my_test_template.md",
    "frontmatter": {
      "task_type": "test",
      "name": "测试模板",
      "is_default": false,
      "version": "1.0"
    },
    "body": "你好，{{name}}！"
  }' | python -m json.tool
```

预期：201，`file_name: "my_test_template.md"`

### 6.6 验证磁盘文件

```bash
cat data/templates/my_test_template.md
```

预期：文件内容为 YAML frontmatter + body 的 .md 格式

### 6.7 删除模板

```bash
curl -s -X DELETE http://localhost:8000/api/v1/templates/my_test_template.md
```

预期：204 No Content，磁盘文件已被删除

### 6.8 校验默认模板保护

```bash
curl -s -X DELETE http://localhost:8000/api/v1/templates/chapter_writing_default.md
```

预期：400 `Cannot delete default template: chapter_writing_default.md`

---

## 7. P1-T6 — 流式生成与编辑器

### 7.1 准备工作

确保：
- 数据库已初始化（`python backend/init_db.py`）
- 至少有一个卷和一个章节存在
- `chapter_writing` 路由已配置并启用（见 5.2 节）
- 后端和前端均已启动

### 7.2 前端功能验证

| # | 操作 | 预期结果 |
|---|------|---------|
| 1 | 浏览器打开 `http://localhost:5173/outline` | 大纲视图渲染，显示已创建的卷和章节 |
| 2 | 点击「创建卷」，填入标题，点击创建 | 新卷出现在列表中 |
| 3 | 点击「创建章节」，选择卷、填写标题和摘要 | 新章节出现在对应卷下 |
| 4 | 点击章节列表中的某个章节 | 跳转到 `http://localhost:5173/editor/{id}` |
| 5 | 在编辑器右栏修改标题和摘要 | 输入框响应正常 |
| 6 | 在编辑器中间正文区输入内容 | Tiptap 编辑器正常工作，文字显示 |
| 7 | 点击「保存」按钮 | 提示「已保存」，刷新后内容保留 |
| 8 | 访问 `http://localhost:5173/settings` | 显示 5 个任务类型的配置卡片 |
| 9 | 修改某个路由的提供商/模型/Key，点击保存 | 提示「保存成功」 |

### 7.3 SSE 流式生成验证

**方法 A：通过前端**

| # | 操作 | 预期结果 |
|---|------|---------|
| 1 | 在编辑器页面，确保 `chapter_writing` 路由已配置有效 API Key | — |
| 2 | 点击「生成」按钮 | 按钮变为「生成中...」并显示加载状态 |
| 3 | 观察正文区 | 逐字显示 AI 返回的文字，实时刷新 |
| 4 | 等待生成完成 | 按钮恢复为「重新生成」，提示「生成完成」 |
| 5 | 检查章节字数 | 右栏「字数」显示为生成内容字数 |
| 6 | 刷新页面，重新打开该章节 | 生成的内容已保存，持久化不丢失 |

**方法 B：通过 curl（无需前端）**

```bash
# 确保 chapter_writing 路由已配置
curl -s -N -X POST http://localhost:8000/api/v1/generate/chapter/1 \
  -H 'Content-Type: application/json' \
  -d '{}'
```

预期看到 SSE 事件流：

```
data: {"event": "start", "model": "gpt-4o-mini", "token_estimate": 186}

data: {"event": "token", "token": "在"}
data: {"event": "token", "token": "一"}
data: {"event": "token", "token": "片"}
...（逐字输出）

data: {"event": "done", "word_count": 1523, "model": "gpt-4o-mini"}
```

### 7.4 版本记录验证

```bash
sqlite3 novel.db "SELECT id, chapter_id, word_count, model_used, version_type, created_at FROM chapter_versions;"
```

预期：有一条或多条记录，`version_type` 为 `generated`，`model_used` 为模型名称

```bash
sqlite3 novel.db "SELECT id, content, word_count, status FROM chapters WHERE id=1;"
```

预期：`content` 不为 NULL，`word_count > 0`，`status = 'completed'`

### 7.5 参数覆盖

```bash
curl -s -N -X POST http://localhost:8000/api/v1/generate/chapter/1 \
  -H 'Content-Type: application/json' \
  -d '{"temperature": 0.3, "max_tokens": 1024}'
```

预期：生成使用 `temperature=0.3`、`max_tokens=1024`（而非路由配置中的默认值）

---

## 8. 端到端里程碑验收

### 完整链路测试

从零开始完成一章生成：

```bash
# 1. 重置数据库
rm -f novel.db && python backend/init_db.py

# 2. 创建卷
VOL_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/volumes \
  -H 'Content-Type: application/json' \
  -d '{"title":"第一卷","description":"序章","sort_order":1}')
echo "卷创建: $VOL_RESULT" | head -1

# 3. 创建章节
CHAPTER_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/chapters \
  -H 'Content-Type: application/json' \
  -d '{"volume_id":1,"title":"第一章 开端","summary":"主角在一片陌生的环境中醒来，发现自己失去了记忆。","sort_order":1}')
echo "章节创建: $CHAPTER_RESULT" | head -1

# 4. 配置 API Key（替换为真实 Key）
curl -s -X PUT http://localhost:8000/api/v1/model-routes/chapter_writing \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4o-mini",
    "api_key": "sk-your-real-key",
    "enabled": true,
    "max_tokens": 4096,
    "temperature": 0.8
  }' | python -m json.tool | grep -E '"enabled"|"api_key_mask"|"model_name"'

# 5. 流式生成
echo "===== 开始生成 ====="
curl -s -N -X POST http://localhost:8000/api/v1/generate/chapter/1 \
  -H 'Content-Type: application/json' \
  -d '{}'
echo ""
echo "===== 生成完成 ====="

# 6. 验证保存结果
sqlite3 novel.db "SELECT id, title, word_count, status FROM chapters WHERE id=1;"
sqlite3 novel.db "SELECT id, word_count, model_used, version_type FROM chapter_versions WHERE chapter_id=1;"
```

### 验收检查清单

| 步骤 | 操作 | 通过条件 | 结果 |
|------|------|---------|------|
| 1 | 创建卷 | API 返回 201，数据库 `volumes` 表有记录 | [ ] |
| 2 | 写摘要（创建章节时填写 summary） | API 返回 201，`summary` 不为空 | [ ] |
| 3 | 配置 API Key | 写入后 `enabled: true`，数据库中非明文存储 | [ ] |
| 4 | 触发生成 | SSE 事件流开始输出 token | [ ] |
| 5 | 看到流式输出 | 前端逐字显示 / curl 看到 `"event": "token"` | [ ] |
| 6 | 保存 | 生成完成后 `chapter_versions` 有记录，`chapters.content` 不为空，`word_count > 0` | [ ] |

---

## 9. 边界情况与故障注入

### 9.1 无 API Key 时生成

```bash
# 将路由设为禁用
curl -s -X PUT http://localhost:8000/api/v1/model-routes/chapter_writing \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false}'

# 尝试生成
curl -s -N -X POST http://localhost:8000/api/v1/generate/chapter/1 \
  -H 'Content-Type: application/json' \
  -d '{}'
```

预期 SSE：
```
data: {"event": "error", "message": "chapter_writing route is not enabled"}
```

### 9.2 章节不存在时生成

```bash
curl -s -N -X POST http://localhost:8000/api/v1/generate/chapter/9999 \
  -H 'Content-Type: application/json' \
  -d '{}'
```

预期 SSE：
```
data: {"event": "error", "message": "Chapter not found"}
```

### 9.3 生成中断

- 在生成过程中关闭浏览器或按 Ctrl+C 终止 curl
- 后端不应崩溃，日志不应出现未处理异常
- 检查数据库：已保存的部分内容不受影响（当前实现是生成完成后一次性保存，中断不会保存不完整内容）

### 9.4 LLM API 返回错误

- 使用错误的 API Key 或已过期的 Key
- 预期：SSE 返回 `"event": "error"`，包含 HTTP 状态码和错误摘要

### 9.5 模板文件被删除

```bash
# 备份后删除默认模板
cp data/templates/chapter_writing_default.md /tmp/
rm data/templates/chapter_writing_default.md

# 尝试生成
curl -s -N -X POST http://localhost:8000/api/v1/generate/chapter/1 \
  -H 'Content-Type: application/json' \
  -d '{}'
```

预期 SSE：
```
data: {"event": "error", "message": "No default template found for task type: chapter_writing"}
```

恢复：
```bash
cp /tmp/chapter_writing_default.md data/templates/
```

### 9.6 大文本生成压力测试

- 设置 `max_tokens: 8192` 触发生成长文本
- 前端应持续接收 SSE 事件，不出现内存泄漏
- 生成完成后字数统计应基本正确

---

## 附录：关键 API 路由汇总

### 后端端点

| 方法 | 路径 | 说明 | 任务 |
|------|------|------|------|
| GET | `/api/v1/health` | 健康检查 | P1-T1 |
| GET | `/api/v1/volumes` | 卷列表 | P1-T3 |
| POST | `/api/v1/volumes` | 创建卷 | P1-T3 |
| GET | `/api/v1/chapters` | 章节列表（支持 volume_id/skip/limit） | P1-T3 |
| POST | `/api/v1/chapters` | 创建章节 | P1-T3 |
| GET | `/api/v1/chapters/{id}` | 章节详情 | P1-T3 |
| PUT | `/api/v1/chapters/{id}` | 更新章节 | P1-T3 |
| DELETE | `/api/v1/chapters/{id}` | 删除章节 | P1-T3 |
| PUT | `/api/v1/chapters/reorder` | 批量排序 | P1-T3 |
| GET | `/api/v1/model-routes` | 路由列表（Key 掩码） | P1-T4 |
| PUT | `/api/v1/model-routes/{task_key}` | 更新路由 | P1-T4 |
| POST | `/api/v1/model-routes/{task_key}/test` | 测试连接 | P1-T4 |
| GET | `/api/v1/templates` | 模板列表 | P1-T5 |
| GET | `/api/v1/templates/{name}` | 模板详情 | P1-T5 |
| POST | `/api/v1/templates` | 创建模板 | P1-T5 |
| PUT | `/api/v1/templates/{name}` | 更新模板 | P1-T5 |
| DELETE | `/api/v1/templates/{name}` | 删除模板 | P1-T5 |
| POST | `/api/v1/templates/build-preview` | 预览渲染 | P1-T5 |
| POST | `/api/v1/generate/chapter/{id}` | SSE 流式生成 | P1-T6 |

### 前端路由

| 路径 | 视图 | 说明 |
|------|------|------|
| `/` | Dashboard | 工作台 |
| `/outline` | OutlineView | 大纲视图（卷/章节管理） |
| `/editor/:id?` | ChapterEditor | 章节编辑器 |
| `/settings` | ModelRouteSettings | API Key 配置 |

---

## 附录：已知限制

| 编号 | 说明 | 影响 |
|------|------|------|
| D-01 | API Key 使用 base64 + salt 混淆，非生产级加密 | 仅防意外泄露 |
| D-02 | SSE 未实现断点续传，中断需重新生成 | 网络不稳定时需重试 |
| KN-01 | Node.js 18.19.1 不兼容 create-vite@9.x | 已固定 create-vite@5 |

---

*文档版本: v1.0 · 2026-05-17 · 对应提交: `c6b21dd` `152a98a` `46df4e4` `b85cd9e` `a1250a3` `f2c046c`*
