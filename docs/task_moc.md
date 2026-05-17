# AI_Novel 项目任务拆分

**版本：** v1.0  
**日期：** 2026-05-17  
**原则：** 渐进式披露 · 单任务单边界 · 可独立交付

---

## 阅读指南

每个任务卡片包含以下字段：

| 字段         | 说明                                 |
| ------------ | ------------------------------------ |
| **任务 ID**  | `Px-Ty` 格式，P=阶段，T=任务序号     |
| **模块边界** | 对应代码目录/文件，即「动哪里」      |
| **类型**     | `backend` / `frontend` / `fullstack` |
| **依赖**     | 必须先完成的任务 ID                  |
| **交付物**   | 该任务完成后可验收的具体产物         |
| **验收标准** | 判断「做完了」的最低可通过条件       |

---

## Phase 1 — MVP · 核心可用

> 目标：跑通「写摘要 → 生成正文 → 保存」核心链路，可配置 API Key，可单章生成。

---

### P1-T1 · 项目骨架与工程化配置

**模块边界：** 根目录、`backend/`、`frontend/`

**类型：** fullstack

**依赖：** 无

**描述：**  
初始化前后端工程结构，约定目录规范，配置开发环境。不写任何业务逻辑，只建脚手架。

**交付物：**

- `backend/` 目录结构（`main.py` 骨架、`routers/`、`services/`、`models/`、`repositories/` 空目录）
- `backend/requirements.txt`（FastAPI、SQLAlchemy、loguru、python-dotenv、httpx、Pydantic v2）
- `frontend/` Vite + Vue 3 脚手架（含 Vue Router 4、Pinia、Naive UI、axios）
- `.env.example`（列出所有需要的环境变量键）
- `.gitignore`（排除 `.env`、`*.db`、`logs/`、`node_modules/`、`__pycache__/`）
- `data/config.json` 模块开关骨架（所有模块默认 `true`）
- `README.md`（启动命令说明）

**验收标准：**

- `uvicorn main:app` 启动后访问 `http://localhost:8000/docs` 返回 OpenAPI 页面
- `npm run dev` 启动后访问 `http://localhost:5173` 返回 Vue 默认页
- Git 初始化，`.env` 不在追踪列表中

---

### P1-T2 · 数据库初始化与 ORM 配置

**模块边界：** `backend/database.py`、`backend/models/`

**类型：** backend

**依赖：** P1-T1

**描述：**  
配置 SQLAlchemy 引擎，定义所有业务表的 ORM 模型（按需求文档第 5 节），提供数据库初始化脚本。此阶段不实现 CRUD 接口，只建表。

**交付物：**

- `database.py`：SQLAlchemy 引擎 + Session 工厂（`get_db` 依赖注入函数）
- `models/chapter.py`：`Volume`、`Chapter`、`ChapterVersion` ORM 类
- `models/character.py`：`Character`、`CharacterRelation` ORM 类
- `models/item.py`：`Item`、`ItemOwnershipHistory` ORM 类
- `models/event.py`：`WorldEvent`、`EventParticipant` ORM 类
- `models/model_route.py`：`ModelRoute` ORM 类
- `models/story_line.py`：`StoryLine`、`ChapterStoryLine`、`ChapterCharacter` ORM 类
- `init_db.py`：运行即创建所有表的脚本

**验收标准：**

- `python init_db.py` 执行后 `novel.db` 文件存在，SQLite 浏览器可查看所有表结构
- 所有外键约束正确定义
- `get_db` 依赖注入可在路由中正常使用

---

### P1-T3 · 章节 CRUD 接口

**模块边界：** `backend/routers/chapters.py`、`backend/repositories/chapter_repo.py`

**类型：** backend

**依赖：** P1-T2

**描述：**  
实现章节与卷的完整 CRUD REST 接口。所有数据库操作通过 Repository 封装，路由层只做参数校验和调用。

**交付物：**

- `repositories/chapter_repo.py`：封装所有章节/卷 SQL 操作的函数
- `routers/chapters.py`：以下接口实现：

| 方法   | 路径                       | 说明                       |
| ------ | -------------------------- | -------------------------- |
| GET    | `/api/v1/chapters`         | 列表（含分页、卷过滤）     |
| POST   | `/api/v1/chapters`         | 创建章节                   |
| GET    | `/api/v1/chapters/{id}`    | 章节详情                   |
| PUT    | `/api/v1/chapters/{id}`    | 更新章节（标题/摘要/内容） |
| DELETE | `/api/v1/chapters/{id}`    | 删除章节                   |
| PUT    | `/api/v1/chapters/reorder` | 批量更新 sort_order        |
| GET    | `/api/v1/volumes`          | 卷列表                     |
| POST   | `/api/v1/volumes`          | 创建卷                     |

- Pydantic Schema（`ChapterCreate`、`ChapterUpdate`、`ChapterResponse`、`VolumeCreate`）

**验收标准：**

- 通过 `/docs` 可对所有接口进行测试并返回正确数据
- 创建章节后 `word_count` 默认为 0，`status` 默认为 `pending`
- 删除章节不影响其他章节排序

---

### P1-T4 · 模型路由配置接口与存储

**模块边界：** `backend/routers/model_routes.py`、`backend/services/model_router.py`

**类型：** backend

**依赖：** P1-T2

**描述：**  
实现模型路由配置的 CRUD，支持 5 个预定义任务 key，API Key 简单混淆后存库，提供测试连接接口。

**交付物：**

- `routers/model_routes.py`：

| 方法 | 路径                                   | 说明                             |
| ---- | -------------------------------------- | -------------------------------- |
| GET  | `/api/v1/model-routes`                 | 获取所有路由配置（Key 返回掩码） |
| PUT  | `/api/v1/model-routes/{task_key}`      | 更新指定任务路由                 |
| POST | `/api/v1/model-routes/{task_key}/test` | 发送测试请求验证连通性           |

- `services/model_router.py`：`get_route_config(task_key)` 函数，返回解密后的完整配置
- API Key 加解密工具函数（base64 + 本地 salt，存入 `api_key_encrypted` 字段）
- 数据库预置 5 个任务 key 的空行（`outline_design` / `chapter_writing` / `character_design` / `worldbuilding` / `revision`）

**验收标准：**

- 写入 API Key 后，数据库中存储的不是明文
- `test` 接口向对应 LLM 发送 `"hello"` 并返回 `{"success": true}` 或错误信息
- 未配置的路由返回 `enabled: false`

---

### P1-T5 · 提示词模板引擎（后端）

**模块边界：** `backend/services/prompt_builder.py`、`backend/routers/templates.py`、`data/templates/`

**类型：** backend

**依赖：** P1-T4

**描述：**  
实现 Markdown + YAML frontmatter 模板的读取、解析和变量填充，提供模板 CRUD 接口（操作磁盘文件）。

**交付物：**

- `services/prompt_builder.py`：
  - `load_template(task_type)` — 读取 `data/templates/` 下对应 `is_default: true` 的模板文件
  - `build_prompt(template, variables: dict)` — `{{变量名}}` 替换，返回最终 prompt 字符串
  - `estimate_tokens(text)` — 简单 token 估算（字符数 / 3.5）
- `routers/templates.py`：模板文件 CRUD（列表/读取/创建/更新/删除 `.md` 文件）
- `data/templates/chapter_writing_default.md` — 完整示例模板（含所有内置变量）

**验收标准：**

- `build_prompt()` 能正确替换所有 `{{变量名}}` 占位符
- 缺少 `required: true` 变量时抛出明确错误
- 模板 CRUD 接口对文件系统操作正确（创建/读取/删除对应 `.md` 文件）

---

### P1-T6 · 单章流式生成 + 前端章节编辑器（MVP）

**模块边界：** `backend/services/generator.py`、`backend/routers/generate.py`、`frontend/src/views/ChapterEditor.vue`、`frontend/src/components/common/StreamOutput.vue`

**类型：** fullstack

**依赖：** P1-T3、P1-T4、P1-T5

**描述：**  
打通核心生成链路：前端触发 → 后端组装 prompt → 调用 LLM → SSE 流式返回 → 前端实时渲染 → 自动保存版本。同步实现章节列表页和基础设置页（API Key 配置）。

**交付物：**

**后端：**

- `services/generator.py`：
  - 调用 `prompt_builder` 组装 prompt
  - 通过 `model_router` 获取模型配置
  - 用 `httpx` 异步流式调用 LLM API
  - 生成完成后自动保存 `chapter_versions` 记录，更新章节 `content` 和 `word_count`
- `routers/generate.py`：`POST /api/v1/generate/chapter/{id}`（SSE 响应，`text/event-stream`）

**前端：**

- `views/ChapterEditor.vue`：三列布局
  - 左栏：章节列表导航（复用章节列表 API）
  - 中栏：Tiptap 正文编辑区 + 生成/重新生成按钮
  - 右栏：章节元信息（标题、摘要、生成参数覆盖）
- `components/common/StreamOutput.vue`：通用 SSE 流式文本显示组件
- `views/OutlineView.vue`：章节列表树形视图（基础版，无拖拽）
- `views/ModelRouteSettings.vue`：API Key 配置页（基础版，每任务一行）
- `api/generate.js`：封装 EventSource 连接逻辑
- `stores/chapters.js`：Pinia store，管理章节列表和当前编辑章节状态

**验收标准：**

- 点击「生成」后，正文区开始流式显示 LLM 输出的文字
- 生成完成后数据库中存在对应 `chapter_versions` 记录
- 手动编辑正文后，点击「保存」可更新 `chapters.content`
- 生成中途关闭 SSE 连接不导致后端崩溃

---

## Phase 2 — 世界观管理

> 目标：完成世界观、人物、关系图等设定管理模块，并将设定注入生成 prompt。

---

### P2-T1 · 世界观设定编辑器

**模块边界：** `backend/routers/worldview.py`、`data/worldview.json`、`frontend/src/views/WorldviewEditor.vue`

**类型：** fullstack

**依赖：** P1-T1

**描述：**  
世界观以 JSON 文件存储，后端提供读写接口，前端按区块展示可编辑的设定内容，含注入预览功能。

**交付物：**

- `data/worldview.json` Schema（含所有字段的空模板）
- `routers/worldview.py`：`GET /worldview`、`PUT /worldview`（支持整体或分区块更新）
- `views/WorldviewEditor.vue`：分区块 Tab 布局（背景/地理/历史/力量体系/社会结构/势力/规则/术语表），每区块独立保存
- 「注入预览」侧滑面板：展示当前设定被注入 prompt 时的实际文本 + token 估算
- 术语表：表格形式（term / definition），支持增删行

**验收标准：**

- 修改某区块保存后，`worldview.json` 对应字段更新
- 注入预览能正确显示经 `prompt_builder` 处理后的实际文本
- 术语表增删操作即时保存

---

### P2-T2 · 人物 CRUD 与 Repository

**模块边界：** `backend/routers/characters.py`、`backend/repositories/character_repo.py`、`frontend/src/views/CharacterList.vue`、`frontend/src/views/CharacterDetail.vue`

**类型：** fullstack

**依赖：** P1-T2

**描述：**  
实现人物及人物关系的完整 CRUD，前端提供人物列表和人物详情页。

**交付物：**

- `repositories/character_repo.py`：封装所有人物/关系 SQL
- `routers/characters.py`：

| 方法   | 路径                                | 说明                           |
| ------ | ----------------------------------- | ------------------------------ |
| GET    | `/api/v1/characters`                | 人物列表（支持按角色类型过滤） |
| POST   | `/api/v1/characters`                | 创建人物                       |
| GET    | `/api/v1/characters/{id}`           | 人物详情                       |
| PUT    | `/api/v1/characters/{id}`           | 更新人物                       |
| DELETE | `/api/v1/characters/{id}`           | 删除人物                       |
| GET    | `/api/v1/characters/relations`      | 全部关系（图数据格式）         |
| POST   | `/api/v1/characters/relations`      | 创建关系                       |
| PUT    | `/api/v1/characters/relations/{id}` | 更新关系                       |
| DELETE | `/api/v1/characters/relations/{id}` | 删除关系                       |

- `views/CharacterList.vue`：卡片列表 + 角色类型筛选
- `views/CharacterDetail.vue`：人物完整信息编辑表单

**验收标准：**

- 创建/编辑/删除人物后列表即时刷新
- `GET /characters/relations` 返回可直接用于 Vue Flow 的 nodes + edges 格式

---

### P2-T3 · 人物关系图（Canvas）

**模块边界：** `frontend/src/views/CharacterGraph.vue`

**类型：** frontend

**依赖：** P2-T2

**描述：**  
基于 Vue Flow 实现人物关系可视化画布，支持拖拽编辑、关系类型着色、过滤和导出。

**交付物：**

- `views/CharacterGraph.vue`：全屏 Vue Flow 画布
  - 节点：人物卡片（姓名 + 角色类型 + 状态标签）
  - 边：关系类型（颜色区分：友好/敌对/中立/血缘/师徒/爱情）
  - 右侧面板：选中节点/边的属性查看与编辑（调用 P2-T2 接口）
- 左侧人物列表（可拖入画布）
- 过滤工具栏：按角色类型过滤节点、按关系类型过滤边
- 导出 PNG 按钮（`html-to-image` 或 Vue Flow 内置方案）
- 关系类型颜色配置常量文件

**验收标准：**

- 画布可正常渲染 20+ 人物节点不卡顿
- 在画布上编辑边的关系描述后，数据库同步更新
- 导出 PNG 图片包含完整画布内容

---

### P2-T4 · 提示词模板库 UI

**模块边界：** `frontend/src/views/TemplateLibrary.vue`

**类型：** frontend

**依赖：** P1-T5

**描述：**  
提示词模板的前端管理界面，支持创建/编辑/删除模板文件，含变量自动补全和预览功能。

**交付物：**

- `views/TemplateLibrary.vue`：
  - 左侧：模板列表（按任务类型分组，显示名称/任务类型/版本）
  - 右侧：模板编辑区（frontmatter 字段表单 + 正文 Markdown 编辑器）
  - 输入 `{{` 时弹出内置变量补全列表
  - 「预览」功能：弹窗中填入测试数据，实时渲染最终 prompt 文本
  - Token 数估算实时显示（调用后端 `estimate_tokens`）
- 默认模板保护：`is_default: true` 的模板不可删除，可另存为副本

**验收标准：**

- 创建新模板后磁盘 `data/templates/` 下对应 `.md` 文件存在
- 变量补全在输入 `{{` 后 200ms 内弹出
- 预览渲染结果与实际生成使用的 prompt 一致

---

### P2-T5 · 章节关联人物与设定注入

**模块边界：** `backend/routers/chapters.py`（扩展）、`backend/services/prompt_builder.py`（扩展）、`frontend/src/views/ChapterEditor.vue`（右栏扩展）

**类型：** fullstack

**依赖：** P2-T2、P1-T6

**描述：**  
在章节编辑器右栏新增「关联人物」多选，保存关联关系；生成时 `prompt_builder` 自动将关联人物设定注入 prompt。

**交付物：**

- `chapter_characters` 关联表接口（`PUT /api/v1/chapters/{id}/characters`、`GET /api/v1/chapters/{id}/characters`）
- `ChapterEditor.vue` 右栏：人物多选组件（可搜索下拉，显示已关联人物卡片）
- `prompt_builder.py` 扩展：`build_prompt` 从数据库读取关联人物，填充 `{{character_profiles}}` 变量
- 世界观注入量控制：按章节级别参数 `worldview_level`（high/medium/low）注入不同详细程度的世界观摘要

**验收标准：**

- 关联 2 名人物后触发生成，prompt 中包含这 2 人的设定文本
- 去关联人物后重新生成，prompt 中不再包含该人物设定
- 世界观注入量三档切换后，token 估算数值有明显差异

---

## Phase 3 — 高级功能

> 目标：完善地图、时间线、批量生成、日志、版本历史等进阶功能。

---

### P3-T1 · 地图编辑器（Canvas）

**模块边界：** `backend/routers/worldview.py`（扩展 map 接口）、`frontend/src/views/MapEditor.vue`、`data/map.json`

**类型：** fullstack

**依赖：** P2-T1

**描述：**  
基于 Vue Flow 实现世界地图节点编辑，地图数据以 Vue Flow 兼容 JSON 格式存储。

**交付物：**

- `GET /api/v1/map`、`PUT /api/v1/map`（读写 `data/map.json`）
- `data/map.json` 初始结构（包含示例节点和边）
- `views/MapEditor.vue`：
  - 节点类型：城市 / 村庄 / 建筑 / 自然地标 / 国家 / 地区（按类型着色）
  - 右侧属性面板：节点名称、描述、所属区域、重要程度；边关系类型
  - 左侧节点创建面板（按类型拖入画布）
  - 导出 PNG 按钮
- 节点类型图标与颜色配置常量

**验收标准：**

- 创建/移动节点后保存，刷新页面节点位置保持不变
- 不同节点类型用不同颜色区分
- 导出 PNG 可识别地图内容

---

### P3-T2 · 时间线与世界事件管理

**模块边界：** `backend/routers/events.py`、`backend/repositories/event_repo.py`、`frontend/src/views/Timeline.vue`

**类型：** fullstack

**依赖：** P2-T2、P1-T2

**描述：**  
世界事件 CRUD，横轴时间线可视化，支持多维过滤。

**交付物：**

- `repositories/event_repo.py`：封装事件相关 SQL
- `routers/events.py`：

| 方法   | 路径                               | 说明                 |
| ------ | ---------------------------------- | -------------------- |
| GET    | `/api/v1/events`                   | 事件列表（支持过滤） |
| POST   | `/api/v1/events`                   | 创建事件             |
| PUT    | `/api/v1/events/{id}`              | 更新事件             |
| DELETE | `/api/v1/events/{id}`              | 删除事件             |
| PUT    | `/api/v1/events/{id}/participants` | 更新参与人物         |

- `views/Timeline.vue`：
  - 横轴：世界内时间（字符串排序，支持自定义纪元格式）
  - 纵轴：事件类型分层（战争/政治/自然/人物事件）
  - 事件卡片：点击展开详情（描述、参与人物、影响、是否已揭示）
  - 过滤面板：按人物/地点/类型过滤

**验收标准：**

- 创建事件后在时间线正确位置显示
- 过滤「按人物」后只显示该人物参与的事件
- `is_hidden` 状态在时间线上有视觉区分（如灰色/虚线）

---

### P3-T3 · 批量生成队列

**模块边界：** `backend/services/generator.py`（扩展）、`backend/routers/generate.py`（扩展）、前端批量控制面板

**类型：** fullstack

**依赖：** P1-T6

**描述：**  
支持选定章节范围批量顺序生成，提供队列状态查询和暂停/继续/取消控制。

**交付物：**

- `services/generator.py` 扩展：
  - 内存中维护生成队列（`asyncio.Queue`）
  - 支持暂停/继续标志位
  - 单章失败记录错误，继续下一章
- `routers/generate.py` 扩展：

| 方法   | 路径                                 | 说明                                  |
| ------ | ------------------------------------ | ------------------------------------- |
| POST   | `/api/v1/generate/batch`             | 创建批量队列，返回 `queue_id`         |
| GET    | `/api/v1/generate/queue/{id}`        | 查询队列状态（总数/已完成/失败/当前） |
| PUT    | `/api/v1/generate/queue/{id}/pause`  | 暂停队列                              |
| PUT    | `/api/v1/generate/queue/{id}/resume` | 继续队列                              |
| DELETE | `/api/v1/generate/queue/{id}`        | 取消队列                              |

- 前端批量控制面板（嵌入大纲视图工具栏）：
  - 章节范围多选
  - 生成进度条（已完成/总数）
  - 当前正在生成的章节标题
  - 暂停/继续/取消按钮
  - 失败章节列表（含错误原因）

**验收标准：**

- 批量生成 5 章，全部顺序完成，数据库均有对应版本记录
- 暂停后当前章节生成完毕再停止（不强制中断），继续后从下一章开始
- 单章 API 超时失败后，队列继续处理后续章节，失败章节在 UI 中标红

---

### P3-T4 · 日志系统与实时查看器

**模块边界：** `backend/logger.py`、`backend/services/log_streamer.py`、`backend/routers/system.py`（日志接口）、`frontend/src/views/LogViewer.vue`

**类型：** fullstack

**依赖：** P1-T1

**描述：**  
配置 loguru 日志系统，在关键业务节点埋点，前端实时展示日志流，支持过滤和下载。

**交付物：**

- `logger.py`：
  - 文件日志：按天滚动，保留 30 天，DEBUG 级别，`logs/app_{date}.log`
  - 控制台：INFO 及以上，彩色输出
  - API Key 脱敏处理（正则替换 key 值为 `***`）
- 关键埋点（添加到 `generator.py`、`model_router.py`）：
  - 每次 API 调用：模型、输入 token、输出 token、耗时
  - 每次章节生成开始/完成：章节 ID、使用模板
  - 每次生成失败：错误类型、重试次数
- `services/log_streamer.py`：读取日志文件尾部并以 SSE 推送新行
- `routers/system.py` 日志接口：

| 方法 | 路径                    | 说明                                             |
| ---- | ----------------------- | ------------------------------------------------ |
| GET  | `/api/v1/logs`          | 日志列表（分页、级别过滤、关键词搜索、时间范围） |
| GET  | `/api/v1/logs/stream`   | 实时日志 SSE 流                                  |
| GET  | `/api/v1/logs/download` | 下载当日日志文件                                 |

- `views/LogViewer.vue`：
  - 级别过滤 Chip（DEBUG/INFO/WARNING/ERROR 多选）
  - 搜索框、时间范围选择器
  - 日志列表：时间 | 彩色级别标签 | 消息
  - 自动滚动开关
  - 最多展示最近 1000 条
  - 下载按钮

**验收标准：**

- 触发一次章节生成后，日志中可查到包含输入/输出 token 数的 INFO 记录
- 日志文件中不含任何明文 API Key
- SSE 流式接口连接后，后端新产生的日志在 2 秒内出现在前端

---

### P3-T5 · 章节版本历史与回滚

**模块边界：** `backend/routers/chapters.py`（扩展）、`frontend/src/components/chapter/VersionHistory.vue`

**类型：** fullstack

**依赖：** P1-T6

**描述：**  
生成时自动记录版本（含 prompt 快照），前端提供版本列表和回滚操作。

**交付物：**

- `routers/chapters.py` 扩展：

| 方法 | 路径                                        | 说明                             |
| ---- | ------------------------------------------- | -------------------------------- |
| GET  | `/api/v1/chapters/{id}/versions`            | 版本列表（时间、字数、使用模型） |
| POST | `/api/v1/chapters/{id}/revert/{version_id}` | 回滚到指定版本                   |

- `generator.py` 更新：生成完成后保存 `chapter_versions` 记录，含 `prompt_snapshot`（DEBUG 用，存完整 prompt）、`model_used`、`tokens_in`、`tokens_out`
- `components/chapter/VersionHistory.vue`：
  - 版本列表：时间 / 字数 / 使用模型
  - 点击版本查看该版本正文（只读预览）
  - 「回滚到此版本」按钮（二次确认弹窗）
- `ChapterEditor.vue` 底部 Tab 扩展：「当前版本」/「版本历史」

**验收标准：**

- 每次生成后版本数+1
- 手动编辑并保存后，新增一条 `manual_edit` 类型版本记录
- 回滚后章节正文和字数统计恢复为目标版本的值

---

## Phase 4 — 完善体验

> 目标：补全统计仪表板、剧情线、物品追踪、导出等收尾功能。

---

### P4-T1 · 仪表板与统计

**模块边界：** `backend/routers/system.py`（stats 接口）、`frontend/src/views/Dashboard.vue`

**类型：** fullstack

**依赖：** P1-T3

**描述：**  
首页仪表板展示小说整体进度、今日统计、最近编辑和快捷操作。

**交付物：**

- `GET /api/v1/system/stats`：返回：
  - 总字数 / 目标字数（120 万）/ 完成百分比
  - 各卷字数汇总
  - 已生成章节数 / 总章节数
  - 今日新增字数（基于 `chapter_versions.created_at`）
- `views/Dashboard.vue`：
  - 进度环形图（当前字数 / 120 万）
  - 各卷完成情况卡片（已完成章节数/总章节数 + 字数）
  - 最近编辑章节列表（5 条，点击跳转编辑器）
  - 今日生成字数大数字展示
  - 快捷操作：新建章节、继续上次编辑

**验收标准：**

- 仪表板数据与数据库实际数据一致（创建章节后刷新体现）
- 页面加载时间 < 500ms

---

### P4-T2 · 剧情线管理

**模块边界：** `backend/routers/`（扩展）、`story_lines` 表、`frontend/src/views/StoryLineView.vue`

**类型：** fullstack

**依赖：** P1-T3

**描述：**  
定义主线/支线/暗线，关联章节，可视化各剧情线的章节分布与进度。

**交付物：**

- 剧情线 CRUD 接口（`GET/POST/PUT/DELETE /api/v1/story-lines`）
- `PUT /api/v1/chapters/{id}/story-lines` — 关联/取消关联剧情线
- `views/StoryLineView.vue`：
  - 剧情线列表（名称/类型/颜色/关联章节数）
  - 章节分布甘特图（横轴章节序号，每条剧情线一行，彩色块表示涉及章节）
  - 点击章节块跳转到编辑器
- `ChapterEditor.vue` 右栏：关联剧情线多选

**验收标准：**

- 创建剧情线后，可在章节编辑器右栏关联
- 甘特图正确显示各剧情线覆盖的章节范围

---

### P4-T3 · 物品归属历史追踪

**模块边界：** `backend/routers/items.py`（新建）、`frontend/src/views/ItemManager.vue`

**类型：** fullstack

**依赖：** P2-T2

**描述：**  
物品 CRUD，记录物品在不同章节间的持有者变化，可追溯物品完整流转历史。

**交付物：**

- `routers/items.py`：

| 方法   | 路径                         | 说明                                     |
| ------ | ---------------------------- | ---------------------------------------- |
| GET    | `/api/v1/items`              | 物品列表                                 |
| POST   | `/api/v1/items`              | 创建物品                                 |
| PUT    | `/api/v1/items/{id}`         | 更新物品（含转移持有者，自动写 history） |
| DELETE | `/api/v1/items/{id}`         | 删除物品                                 |
| GET    | `/api/v1/items/{id}/history` | 归属历史                                 |

- `views/ItemManager.vue`：
  - 物品列表（名称/当前持有人/获得章节）
  - 物品详情抽屉：属性编辑 + 归属历史时间线（章节序号 + 持有者变更）
  - 人物持有物品侧边栏（从人物详情页跳转）

**验收标准：**

- 转移物品持有者后，`item_ownership_history` 新增一条记录，旧记录 `lost_at_chapter` 被填写
- 归属历史时间线按章节序号正确排序

---

### P4-T4 · 导出功能

**模块边界：** `backend/routers/system.py`（导出接口）

**类型：** backend

**依赖：** P1-T3

**描述：**  
将全书或指定章节范围的正文导出为 TXT / Markdown / EPUB 格式文件供下载。

**交付物：**

- `GET /api/v1/system/export`：查询参数 `format=txt|md|epub`，可选 `volume_id` 按卷导出
  - TXT：纯文本，章节间空行分隔，标题用 `=====` 包围
  - Markdown：`# 章节标题` + 正文
  - EPUB：使用 `ebooklib` 生成，含封面元数据（书名、作者从 `config.json` 读取）
- 前端「导出」下拉按钮（位于工作台/大纲页顶部工具栏）：选择格式后触发下载

**验收标准：**

- TXT 和 Markdown 导出包含所有已生成章节的完整正文
- EPUB 可用 Calibre 或 iBooks 正常打开，章节目录正确
- 导出文件名格式：`{小说标题}_{日期}.{格式}`

---

## 附录 A — 任务依赖图

```
P1-T1 (骨架)
  ├── P1-T2 (数据库)
  │     ├── P1-T3 (章节CRUD) ──── P2-T5, P3-T3, P4-T1, P4-T2, P4-T4
  │     ├── P1-T4 (路由配置) ──── P1-T5
  │     │     └── P1-T5 (模板引擎) ── P1-T6 ─── P3-T3, P3-T5
  │     │           └── P1-T6 (生成+编辑器)
  │     └── P2-T2 (人物CRUD) ─── P2-T3, P2-T5, P3-T2, P4-T3
  └── P2-T1 (世界观) ─────────── P3-T1
        └── P2-T4 (模板库UI)
              └── (依赖 P1-T5)
```

---

## 附录 B — 技术债务与约束提示

| 编号 | 位置  | 说明                                                         |
| ---- | ----- | ------------------------------------------------------------ |
| D-01 | P1-T4 | API Key 混淆为轻量保护，非生产级加密，后续可替换为系统密钥环 |
| D-02 | P1-T6 | SSE 连接未实现断点续传，网络中断需重新生成                   |
| D-03 | P3-T3 | 队列状态存于内存，重启后丢失（单用户本地可接受）             |
| D-04 | P3-T4 | 日志 SSE 为轮询尾部文件，高频生成时延迟约 1–2 秒             |
| D-05 | P4-T4 | EPUB 生成依赖 `ebooklib`，复杂格式（图片/表格）可能渲染异常  |

---

## 附录 C — 每阶段里程碑验收

| 阶段    | 里程碑             | 验收动作                                                     |
| ------- | ------------------ | ------------------------------------------------------------ |
| Phase 1 | 可从零完成一章生成 | 创建章节 → 写摘要 → 配置 API Key → 生成 → 看到流式输出 → 保存 |
| Phase 2 | 完整设定管理闭环   | 创建人物 → 设置世界观 → 关联到章节 → 生成包含人物设定的正文  |
| Phase 3 | 批量创作+可观测性  | 选 10 章批量生成 → 中途暂停继续 → 日志查看器看到每章 token 消耗 → 回滚某章到上一版本 |
| Phase 4 | 可交付完整产品     | 仪表板显示正确进度 → 导出 EPUB → Calibre 打开验证章节完整    |

---

*文档结束*