# AI_Novel 项目文档

**版本：** 见 `data/config.json`（当前 0.2.0）
**日期：** 2026-05-17
**性质：** 本地化人机协作长篇小说创作系统

---

## 1. 项目概述

### 1.1 背景与目标

AI_Novel 是一个运行在本地的、人机协作的长篇小说创作系统。作者负责顶层创意（大纲、细纲、章节摘要），AI 根据既定设定自动生成符合要求的正文内容。系统同时提供完善的世界观、人物、剧情管理功能，并支持灵活的大模型路由配置，以适应不同创作环节对模型能力的差异化需求。

**核心目标：** 在保持创作控制力的同时，利用 AI 极大提升长篇小说（目标 120 万字）的写作效率，并通过精细化管理工具确保长篇叙事的连贯性与一致性。

### 1.2 核心工作流

```
作者输入                    系统处理                      输出
─────────                  ─────────                    ─────
大纲 / 细纲               提示词组装器                  流式正文
章节摘要        →→→       (世界观 + 人物 + 摘要)  →→→  (~2000字/章)
世界观设定                大模型路由器
人物设定                  指定模型 API
```

### 1.3 规模预估

| 指标         | 数值                 |
| ------------ | -------------------- |
| 目标总字数   | 120 万字             |
| 单章目标字数 | 约 2000 字           |
| 预计章节数   | 约 600 章            |
| 部署环境     | 纯本地，单用户       |
| 并发需求     | 无（单用户本地工具） |

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────┐
│         Web 前端 (Vite + Vue 3)      │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ 编辑模块  │  │  Canvas 管理模块  │  │
│  └──────────┘  └──────────────────┘  │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ 生成控制台 │  │   设置 / 日志    │  │
│  └──────────┘  └──────────────────┘  │
└────────────────────┬────────────────┘
                     │ HTTP REST + SSE
┌────────────────────▼────────────────┐
│         FastAPI 后端 (Python)        │
│  ┌────────────┐  ┌────────────────┐  │
│  │  生成引擎   │  │   模型路由器   │  │
│  └────────────┘  └────────────────┘  │
│  ┌────────────┐  ┌────────────────┐  │
│  │ 提示词组装器 │  │   日志服务     │  │
│  └────────────┘  └────────────────┘  │
└──────────┬─────────────┬────────────┘
           │             │
    ┌──────▼──────┐  ┌───▼────────┐
    │   SQLite    │  │ JSON 文件  │
    │ (结构化数据)  │  │ (设定/配置) │
    └─────────────┘  └────────────┘
                           │
                    ┌──────▼──────┐
                    │  LLM APIs   │
                    │ (外部调用)   │
                    └─────────────┘
```

### 2.2 模块化开关设计

系统中每个功能模块均可在配置文件中独立启用/禁用，配置项存储于 `config.json`：

```json
{
  "modules": {
    "world_builder": true,
    "character_manager": true,
    "timeline_manager": true,
    "prompt_library": true,
    "model_router": true,
    "log_viewer": true
  }
}
```

后端在启动时读取此配置，动态注册对应路由；前端根据后端返回的模块列表，动态显示/隐藏导航项。

---

## 3. 技术选型

### 3.1 前端

| 技术         | 版本       | 用途          | 选型理由                    |
| ------------ | ---------- | ------------- | --------------------------- |
| Vite         | 5.x        | 构建工具      | 零配置，热更新快            |
| Vue 3        | 3.4+       | UI 框架       | 模板语法对 HTML 背景友好    |
| Vue Router 4 | 4.x        | 路由          | Vue 官方，无学习成本        |
| Pinia        | 2.x        | 全局状态      | Vue 官方，API 极简          |
| Naive UI     | 2.x        | 组件库        | 中文友好，组件齐全          |
| Vue Flow     | 1.x        | Canvas 节点图 | 人物关系/地图，拖拽开箱即用 |
| Tiptap       | 2.x        | 富文本编辑器  | 轻量，可扩展，Markdown 支持 |
| axios        | 1.x        | HTTP 客户端   | 标准选择                    |
| EventSource  | 浏览器原生 | SSE 流式接收  | 零依赖                      |

### 3.2 后端

| 技术          | 版本   | 用途         | 选型理由                          |
| ------------- | ------ | ------------ | --------------------------------- |
| Python        | 3.11+  | 运行环境     | —                                 |
| FastAPI       | 0.110+ | Web 框架     | 自带 OpenAPI 文档，async 支持 SSE |
| SQLAlchemy    | 2.x    | ORM          | 与 SQLite 配合，简单直接          |
| SQLite        | —      | 结构化数据库 | 无需部署，单文件                  |
| loguru        | —      | 日志         | 一行配置分级+文件输出             |
| python-dotenv | —      | 环境变量     | .env 文件读取                     |
| httpx         | —      | 调用 LLM API | 支持 async streaming              |
| Pydantic v2   | —      | 数据校验     | FastAPI 原生集成                  |

### 3.3 数据存储策略

| 数据类型             | 存储方式                     | 原因                                    |
| -------------------- | ---------------------------- | --------------------------------------- |
| 章节正文、大纲、摘要 | SQLite                       | 需要检索、排序、关联                    |
| 人物信息、关系       | SQLite                       | 结构化，需关联查询                      |
| 世界观设定           | JSON 文件                    | 自由格式，便于手工编辑                  |
| 地图数据             | JSON 文件                    | 节点/边结构，非关系型                   |
| 模型路由配置         | SQLite                       | 需要前端 CRUD                           |
| 提示词模板           | Markdown 文件                | 可直接手工编辑、版本管理，纳入 git 追踪 |
| API Key              | `.env` 文件 + SQLite（加密） | 双写，前端可覆盖                        |
| 系统配置             | `config.json`                | 启动读取，修改需重启                    |

---

## 4. 功能模块详细需求

### 4.1 大纲与章节管理

#### 4.1.1 大纲层级结构

系统支持三级层级：

```
小说
 └── 卷（Volume）          # 可选层级，按需创建
      └── 章节（Chapter）  # 核心单元
           └── 摘要         # 作者撰写，AI 生成依据
```

#### 4.1.2 章节列表视图

- 展示所有章节，显示：章节序号、标题、字数、生成状态（未生成 / 生成中 / 已生成 / 已修改）
- 支持拖拽排序
- 支持批量操作：批量生成、批量导出
- 右键菜单：编辑摘要、重新生成、查看历史版本、删除

#### 4.1.3 章节编辑器

- 左栏：章节元信息（标题、摘要、关联人物、关联地点、关联事件）
- 右栏：正文编辑区（Tiptap 富文本，支持 Markdown 快捷键）
- 底部：字数统计、生成状态、操作按钮（生成 / 重新生成 / 保存）
- 支持手动编辑 AI 生成内容
- 历史版本记录（每次生成保存为一个版本，可回滚）

#### 4.1.4 大纲视图

- 树形展示全部卷/章结构
- 支持折叠/展开
- 点击章节跳转到编辑器
- 显示各卷总字数进度

### 4.2 AI 内容生成引擎

#### 4.2.1 单章生成流程

```
1. 用户在章节编辑器点击"生成"
2. 前端向后端发送生成请求（包含 chapter_id）
3. 后端提示词组装器执行：
   a. 读取章节摘要（作者编写）
   b. 读取全局世界观设定（可配置注入量）
   c. 读取关联人物设定
   d. 读取前 N 章摘要作为上下文（N 可配置，默认 3）
   e. 读取对应提示词模板
   f. 拼装最终 prompt
4. 模型路由器根据任务类型选择配置的模型
5. 调用 LLM API，SSE 流式返回
6. 前端实时展示生成内容
7. 生成完成后自动保存，记录版本
```

#### 4.2.2 批量生成

- 支持选定章节范围批量生成（顺序执行，非并发）
- 生成队列展示，显示当前进度
- 支持暂停/继续队列
- 单章生成失败不中断队列，记录失败原因

#### 4.2.3 生成参数（可在章节级别覆盖）

| 参数             | 说明                   | 默认值          |
| ---------------- | ---------------------- | --------------- |
| target_words     | 目标字数               | 2000            |
| context_chapters | 引入前几章摘要         | 3               |
| worldview_level  | 世界观注入详细程度     | medium          |
| temperature      | 模型温度               | 0.8             |
| model_task       | 使用哪个路由任务的模型 | chapter_writing |

### 4.3 世界观管理系统

#### 4.3.1 世界观数据结构

世界观以 JSON 文件存储，结构如下：

```json
{
  "world_name": "...",
  "background": "...",          // 背景设定（自由文本）
  "geography": "...",           // 地理设定
  "history": "...",             // 历史设定
  "magic_system": "...",        // 体系设定（力量/魔法/科技等）
  "social_structure": "...",    // 社会结构
  "factions": [],               // 势力列表
  "rules": [],                  // 世界规则（不可打破的设定）
  "glossary": {}                // 术语表 {term: definition}
}
```

#### 4.3.2 世界观编辑器

- 分区块编辑各类设定，每个区块独立保存
- 支持 Markdown 格式
- 提供"注入预览"功能：显示当前设定被注入 prompt 时的实际内容和 token 估算
- 术语表支持表格形式编辑

#### 4.3.3 地图管理（Canvas）

- 基于 Vue Flow 实现地图节点编辑
- 节点类型：地点（城市/村庄/建筑/自然地标）、区域（国家/地区）
- 节点属性：名称、描述、所属区域、重要程度
- 边属性：关系类型（属于/相邻/距离）
- 支持自定义节点样式（按类型着色）
- 导出为 PNG

### 4.4 人物管理系统

#### 4.4.1 人物数据模型

```
Character:
  - id, name, alias[]       # 姓名与别名
  - role                    # 主角/配角/反派/路人
  - appearance              # 外貌描述
  - personality             # 性格描述
  - background              # 背景故事
  - abilities[]             # 能力/技能
  - items[]                 # 持有物品（关联 Item 表）
  - status                  # 当前状态（生存/死亡/失踪）
  - first_appearance        # 首次出现章节
  - notes                   # 备注（自由文本）
```

#### 4.4.2 人物关系图（Canvas）

- 基于 Vue Flow 实现人物关系图
- 节点 = 人物卡片（显示头像占位符 + 姓名 + 角色）
- 边 = 人物关系（友好/敌对/中立/血缘/师徒/爱情等）
- 边可标注关系描述
- 支持过滤：只显示指定人物的关系
- 支持按角色类型过滤显示

#### 4.4.3 人物物品管理

```
Item:
  - id, name
  - description
  - owner_id (FK → Character)
  - obtained_at_chapter     # 在哪章获得
  - lost_at_chapter         # 在哪章失去（可空）
  - properties              # 特殊属性（JSON）
```

物品历史：记录物品在不同章节的持有者变化，可追溯。

### 4.5 剧情线与时间线管理

#### 4.5.1 世界事件（Event）

```
Event:
  - id, name, description
  - event_type              # 战争/政治/自然/人物事件等
  - world_time              # 世界内时间（自定义格式，如"第三纪元第100年"）
  - real_chapter            # 发生/揭示于哪章
  - participants[]          # 参与人物
  - location_id             # 发生地点
  - impact                  # 影响描述
  - is_hidden               # 是否已在正文中揭示
```

#### 4.5.2 时间线视图

- 横轴：世界内时间
- 纵轴：事件类型分层
- 每个事件显示为卡片，可点击查看详情
- 可按人物/地点/类型过滤

#### 4.5.3 剧情线管理

- 支持定义多条剧情线（主线/支线/暗线）
- 每条剧情线关联若干章节
- 可视化展示各剧情线的章节分布和进度

### 4.6 提示词模板库

#### 4.6.1 模板文件结构

每个模板是一个独立的 Markdown 文件，以 YAML frontmatter 存储元信息，正文部分为模板内容。文件存放于 `data/templates/` 目录。

```markdown
---
name: 章节生成默认模板
description: 用于章节正文生成的默认模板
task_type: chapter_writing
variables:
  - name: chapter_summary
    description: 当前章节摘要
    required: true
  - name: previous_summaries
    description: 前 N 章摘要
    required: true
  - name: world_background
    description: 世界观背景
    required: true
  - name: character_profiles
    description: 关联人物设定
    required: true
is_default: true
version: 1
---

你是一位专业的 {{genre}} 小说作家。请严格根据以下设定创作章节正文。

## 章节信息
- 标题：{{chapter_title}}
- 本章摘要：{{chapter_summary}}

## 前文回顾
{{previous_summaries}}

## 世界观背景
{{world_background}}

## 人物设定
{{character_profiles}}

## 写作要求
- 字数：约 {{target_words}} 字
- 风格：{{writing_style}}
- 请确保情节连贯，对话自然，描写生动。
```

#### 4.6.2 模板文件元信息字段

| 字段          | 说明                                                       |
| ------------- | ---------------------------------------------------------- |
| `name`        | 模板名称                                                   |
| `description` | 用途描述                                                   |
| `task_type`   | 适用的任务类型（见 4.7.2）                                 |
| `variables`   | 变量声明列表，每个变量有 `name`、`description`、`required` |
| `is_default`  | 是否作为该任务类型的默认模板                               |
| `version`     | 版本号（手动递增）                                         |

文件名命名规范：`{task_type}_{name_short}.md`，例如 `chapter_writing_default.md`。

#### 4.6.3 模板变量系统

模板内使用 `{{variable_name}}` 占位符，支持的内置变量：

| 变量                     | 内容         |
| ------------------------ | ------------ |
| `{{chapter_summary}}`    | 当前章节摘要 |
| `{{previous_summaries}}` | 前 N 章摘要  |
| `{{world_background}}`   | 世界观背景   |
| `{{character_profiles}}` | 关联人物设定 |
| `{{writing_style}}`      | 写作风格指令 |
| `{{target_words}}`       | 目标字数     |
| `{{chapter_title}}`      | 章节标题     |

#### 4.6.4 模板编辑器

- 支持创建/编辑/删除模板（操作对应 `data/templates/` 下的 .md 文件）
- 提供变量提示（输入 `{{` 自动补全）
- 预览功能：填入测试数据渲染最终 prompt
- Token 数估算显示

### 4.7 大模型路由配置

系统采用三层路由架构：**API 配置 → 计划 → 任务绑定**，实现模型配置的灵活组合与复用。

#### 4.7.1 架构概览

```
Task (任务类型)  ──绑定──▶  Plan (API 计划)  ──包含──▶  ModelApi (API 配置)
                                                          ├── ModelApi (API 配置)
                                                          └── ...
```

- **ModelApi**：单个 LLM API 的配置（provider、model、api_key、base_url、参数）
- **ApiPlan**：一组 API 配置的集合，支持 Round-Robin 轮询负载
- **TaskPlanBinding**：将任务类型绑定到某个 Plan

一个 Plan 可以包含多个 API，支持轮询分流；一个 Task 绑定一个 Plan，切换 Plan 即可更换模型策略。

#### 4.7.2 任务类型定义

| 任务 key           | 使用场景          |
| ------------------ | ----------------- |
| `outline_design`   | 辅助生成/扩展大纲 |
| `chapter_writing`  | 章节正文生成      |
| `character_design` | 辅助设计人物      |
| `worldbuilding`    | 辅助扩展世界观    |
| `revision`         | 章节润色/修改     |

#### 4.7.3 设置界面功能

- **API 配置管理**：增删改查各个 LLM API 配置，支持测试连接
- **Plan 管理**：创建/编辑 API 计划，添加/移除/排序 API 成员
- **任务绑定**：为每个任务类型选择使用的 Plan
- API Key 在前端显示为掩码，点击可显示
- 支持兼容 OpenAI 协议的任意服务

#### 4.7.4 API Key 存储规则

- 优先级：前端配置（SQLite）> `.env` 文件
- `.env` 文件作为兜底默认值，不在界面强制要求
- 数据库中存储时做简单加密（base64 + 本地 salt，非生产级，仅防止明文存储）

### 4.8 日志系统

#### 4.8.1 日志级别

| 级别    | 用途                                     |
| ------- | ---------------------------------------- |
| DEBUG   | 详细调试信息，prompt 内容，API 请求/响应 |
| INFO    | 正常操作记录，生成开始/完成，配置变更    |
| WARNING | 非致命问题，重试，token 接近上限         |
| ERROR   | 操作失败，API 错误，数据库错误           |

#### 4.8.2 日志配置（loguru）

```python
# 文件日志：按天滚动，保留 30 天
logger.add("logs/app_{time:YYYY-MM-DD}.log", 
           rotation="00:00", retention="30 days", 
           level="DEBUG", encoding="utf-8")

# 控制台日志：INFO 及以上
logger.add(sys.stderr, level="INFO", colorize=True)
```

#### 4.8.3 必须记录的关键事件

- 每次 API 调用：请求时间、使用模型、输入 token 数、输出 token 数、耗时
- 每次章节生成：章节 ID、使用模板 ID、最终 prompt（DEBUG 级别）
- 每次生成失败：错误类型、错误信息、重试次数
- 配置变更：哪个配置被谁改为了什么值

#### 4.8.4 前端日志查看器

- 实时展示后端日志（通过 SSE 推送，或轮询接口）
- 支持按级别过滤
- 支持关键词搜索
- 支持时间范围筛选
- 最多展示最近 1000 条
- 提供下载完整日志文件的按钮

### 4.9 设置与配置中心

#### 4.9.1 全局写作风格设置

```json
{
  "writing_style": {
    "narrative_perspective": "third_person_limited",  // 叙事视角
    "writing_tone": "...",                            // 文风描述
    "genre": "fantasy",                               // 类型
    "avoid_words": [],                                // 禁用词
    "style_examples": ""                              // 参考文段（注入 prompt）
  }
}
```

#### 4.9.2 系统参数设置

| 参数                      | 说明                 | 默认值 |
| ------------------------- | -------------------- | ------ |
| `default_target_words`    | 默认章节字数         | 2000   |
| `context_window_chapters` | 上下文引入前几章     | 3      |
| `max_retry_on_failure`    | 生成失败最大重试次数 | 2      |
| `stream_output`           | 是否使用流式输出     | true   |
| `auto_save_interval`      | 自动保存间隔（秒）   | 30     |

---

## 5. 数据模型

### 5.1 SQLite 表结构

```sql
-- 卷
CREATE TABLE volumes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    sort_order INTEGER,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 章节
CREATE TABLE chapters (
    id INTEGER PRIMARY KEY,
    volume_id INTEGER REFERENCES volumes(id),
    title TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    summary TEXT,                    -- 作者撰写的摘要
    content TEXT,                    -- 最新正文
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',   -- pending/generating/done/modified
    target_words INTEGER DEFAULT 2000,
    model_task TEXT DEFAULT 'chapter_writing',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 章节版本历史
CREATE TABLE chapter_versions (
    id INTEGER PRIMARY KEY,
    chapter_id INTEGER REFERENCES chapters(id),
    content TEXT NOT NULL,
    word_count INTEGER,
    prompt_snapshot TEXT,            -- 生成时使用的完整 prompt（DEBUG用）
    model_used TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 人物
CREATE TABLE characters (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    alias TEXT,                      -- JSON 数组
    role TEXT,                       -- protagonist/antagonist/supporting/minor
    appearance TEXT,
    personality TEXT,
    background TEXT,
    abilities TEXT,                  -- JSON 数组
    status TEXT DEFAULT 'alive',     -- alive/dead/missing
    first_chapter_id INTEGER REFERENCES chapters(id),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 人物关系
CREATE TABLE character_relations (
    id INTEGER PRIMARY KEY,
    character_a_id INTEGER REFERENCES characters(id),
    character_b_id INTEGER REFERENCES characters(id),
    relation_type TEXT,              -- friend/enemy/neutral/family/mentor/lover
    description TEXT,
    since_chapter_id INTEGER REFERENCES chapters(id)
);

-- 物品
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    properties TEXT,                 -- JSON
    current_owner_id INTEGER REFERENCES characters(id)
);

-- 物品归属历史
CREATE TABLE item_ownership_history (
    id INTEGER PRIMARY KEY,
    item_id INTEGER REFERENCES items(id),
    owner_id INTEGER REFERENCES characters(id),
    obtained_at_chapter INTEGER REFERENCES chapters(id),
    lost_at_chapter INTEGER REFERENCES chapters(id)
);

-- 世界事件
CREATE TABLE world_events (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    event_type TEXT,
    world_time TEXT,
    real_chapter_id INTEGER REFERENCES chapters(id),
    location_id TEXT,                -- 关联地图节点 ID（JSON文件中的ID）
    impact TEXT,
    is_hidden INTEGER DEFAULT 0
);

-- 事件参与人物（多对多）
CREATE TABLE event_participants (
    event_id INTEGER REFERENCES world_events(id),
    character_id INTEGER REFERENCES characters(id),
    PRIMARY KEY (event_id, character_id)
);

-- 提示词模板（以 Markdown 文件存储在 data/templates/ 中，无需数据库表）

-- API 配置（单个 LLM 接口）
CREATE TABLE model_apis (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    api_key_encrypted TEXT,
    api_base_url TEXT,
    enabled INTEGER DEFAULT 1,
    max_tokens INTEGER,
    temperature REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- API 计划（多个 API 编组，支持轮询）
CREATE TABLE api_plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    round_robin_index INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 计划-API 关联
CREATE TABLE plan_apis (
    id INTEGER PRIMARY KEY,
    plan_id INTEGER REFERENCES api_plans(id) ON DELETE CASCADE,
    api_id INTEGER REFERENCES model_apis(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0
);

-- 任务-计划绑定
CREATE TABLE task_plan_bindings (
    id INTEGER PRIMARY KEY,
    task_key TEXT UNIQUE NOT NULL,
    plan_id INTEGER REFERENCES api_plans(id) ON DELETE SET NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 剧情线
CREATE TABLE story_lines (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    line_type TEXT,                  -- main/sub/hidden
    description TEXT,
    color TEXT                       -- 前端展示颜色
);

-- 章节与剧情线关联
CREATE TABLE chapter_story_lines (
    chapter_id INTEGER REFERENCES chapters(id),
    story_line_id INTEGER REFERENCES story_lines(id),
    PRIMARY KEY (chapter_id, story_line_id)
);

-- 章节关联人物
CREATE TABLE chapter_characters (
    chapter_id INTEGER REFERENCES chapters(id),
    character_id INTEGER REFERENCES characters(id),
    PRIMARY KEY (chapter_id, character_id)
);
```

### 5.2 JSON 文件结构

**`data/worldview.json`** — 世界观设定  
**`data/map.json`** — 地图节点和边（Vue Flow 格式）  
**`data/config.json`** — 模块开关和系统配置  
**`data/writing_style.json`** — 全局写作风格  
**`data/templates/*.md`** — 提示词模板（每文件一个模板，YAML frontmatter + Markdown 正文）

---

## 6. 接口规范

### 6.1 通用规范

- Base URL: `http://localhost:8000/api/v1`
- 请求/响应格式：`application/json`
- 流式接口：`text/event-stream`（SSE）
- 错误格式：`{"code": "ERROR_CODE", "message": "...", "detail": {}}`

### 6.2 核心接口列表

#### 章节相关

| 方法   | 路径                                 | 说明                    |
| ------ | ------------------------------------ | ----------------------- |
| GET    | `/chapters`                          | 获取章节列表            |
| POST   | `/chapters`                          | 创建章节                |
| GET    | `/chapters/{id}`                     | 获取章节详情            |
| PUT    | `/chapters/{id}`                     | 更新章节                |
| DELETE | `/chapters/{id}`                     | 删除章节                |
| POST   | `/chapters/{id}/generate`            | 触发生成（返回 SSE 流） |
| GET    | `/chapters/{id}/versions`            | 获取版本历史            |
| POST   | `/chapters/{id}/revert/{version_id}` | 回滚到指定版本          |
| PUT    | `/chapters/reorder`                  | 批量更新排序            |

#### 生成引擎

| 方法   | 路径                         | 说明                  |
| ------ | ---------------------------- | --------------------- |
| POST   | `/generate/chapter/{id}`     | 单章生成（SSE）       |
| POST   | `/generate/batch`            | 批量生成，返回队列 ID |
| GET    | `/generate/queue/{queue_id}` | 查询队列状态          |
| DELETE | `/generate/queue/{queue_id}` | 取消队列              |

#### 人物相关

| 方法   | 路径                         | 说明                   |
| ------ | ---------------------------- | ---------------------- |
| GET    | `/characters`                | 获取人物列表           |
| POST   | `/characters`                | 创建人物               |
| PUT    | `/characters/{id}`           | 更新人物               |
| DELETE | `/characters/{id}`           | 删除人物               |
| GET    | `/characters/relations`      | 获取所有关系（图数据） |
| POST   | `/characters/relations`      | 创建关系               |
| PUT    | `/characters/relations/{id}` | 更新关系               |
| DELETE | `/characters/relations/{id}` | 删除关系               |

#### 世界观 / 地图

| 方法 | 路径         | 说明                          |
| ---- | ------------ | ----------------------------- |
| GET  | `/worldview` | 获取世界观                    |
| PUT  | `/worldview` | 更新世界观（整体或分区块）    |
| GET  | `/map`       | 获取地图数据                  |
| PUT  | `/map`       | 保存地图数据（Vue Flow 格式） |

#### 模型路由配置

| 方法   | 路径                            | 说明             |
| ------ | ------------------------------- | ---------------- |
| GET    | `/model-apis`                   | API 配置列表     |
| POST   | `/model-apis`                   | 创建 API 配置    |
| PUT    | `/model-apis/{id}`              | 更新 API 配置    |
| DELETE | `/model-apis/{id}`              | 删除 API 配置    |
| POST   | `/model-apis/{id}/test`         | 测试连接         |
| GET    | `/api-plans`                    | Plan 列表        |
| POST   | `/api-plans`                    | 创建 Plan        |
| PUT    | `/api-plans/{id}`               | 更新 Plan        |
| DELETE | `/api-plans/{id}`               | 删除 Plan        |
| GET    | `/task-bindings`                | 任务绑定列表     |
| PUT    | `/task-bindings/{task_key}`     | 设置任务绑定     |

#### 日志

| 方法 | 路径             | 说明                      |
| ---- | ---------------- | ------------------------- |
| GET  | `/logs`          | 获取日志列表（分页+过滤） |
| GET  | `/logs/stream`   | 实时日志推送（SSE）       |
| GET  | `/logs/download` | 下载日志文件              |

#### 系统

| 方法 | 路径             | 说明                         |
| ---- | ---------------- | ---------------------------- |
| GET  | `/system/config` | 获取系统配置（含模块开关）   |
| PUT  | `/system/config` | 更新系统配置                 |
| GET  | `/system/stats`  | 统计信息（总字数、章节数等） |

---

## 7. 前端页面规划

### 7.1 导航结构

```
侧边导航（左侧固定，可折叠）
├── 📖 工作台（首页/仪表板）
├── 📝 大纲管理
│   ├── 大纲树视图
│   └── 章节编辑器
├── 🌍 世界观
│   ├── 设定编辑器
│   └── 地图编辑器（Canvas）
├── 👥 人物管理
│   ├── 人物列表
│   ├── 人物详情
│   ├── 关系图（Canvas）
│   └── 物品管理
├── 📅 时间线 & 事件
├── 💬 提示词模板
├── ⚙️ 设置
│   ├── 模型路由配置
│   ├── 写作风格
│   └── 系统参数
└── 📋 日志查看器
```

### 7.2 各页面核心 UI 元素

**工作台（仪表板）**

- 小说整体进度（当前字数 / 目标字数，进度条）
- 各卷完成情况
- 最近编辑的章节列表
- 今日生成字数统计
- 快速操作按钮

**大纲树视图**

- 左栏：可折叠的卷/章树形列表（拖拽排序）
- 右栏：选中章节的摘要预览和快速编辑
- 顶部工具栏：新建卷、新建章节、批量生成

**章节编辑器**

- 三列布局：
  - 左：章节列表导航
  - 中：正文编辑区（Tiptap）+ 生成控制按钮
  - 右：章节元信息（摘要、关联设定、生成参数覆盖）
- 顶部：章节标题、字数、状态标签
- 生成时右栏实时滚动显示流式内容
- 底部 tab：当前版本 / 版本历史

**人物关系图（Canvas）**

- 全屏 Vue Flow 画布
- 左侧面板：人物列表（可拖入画布）
- 右侧面板：选中节点/边的属性编辑
- 工具栏：过滤器、缩放、导出

**模型路由配置页**

- 每个任务类型一张卡片
- 卡片内：Provider 下拉、Model 输入、API Key 输入（掩码）、Base URL、参数滑块
- 右侧：测试连接按钮和结果反馈
- 顶部：全局默认 API Key 设置（从 .env 读取显示）

**日志查看器**

- 顶部工具栏：级别过滤（多选 chip）、搜索框、时间范围
- 日志列表：时间 | 级别（彩色标签）| 消息内容
- 底部：自动滚动开关、下载按钮

---

## 8. 非功能性需求

### 8.1 可维护性

- 每个功能模块对应独立的文件组：`views/`、`stores/`、`api/`（前端），`routers/`、`services/`、`models/`（后端）
- 所有硬编码字符串提取为常量
- 所有数据库操作通过 Repository 模式封装，不在路由层直接写 SQL
- 每个函数不超过 50 行，超过则拆分

### 8.2 可扩展性

- 模型路由支持添加任意新任务类型，不需要修改核心代码
- 提示词模板系统与生成引擎解耦，模板变化不影响引擎
- 新增世界观字段只需修改 JSON Schema，不需要数据库迁移
- 前端模块通过配置开关，无需修改组件代码

### 8.3 简单性原则

- 不写推测性代码（不为"将来可能需要"的功能提前抽象）
- 不引入未在需求中明确要求的依赖库
- 优先使用语言/框架标准库解决问题
- 每个接口只做一件事

### 8.4 性能基准（本地单用户，宽松要求）

| 操作                     | 可接受响应时间      |
| ------------------------ | ------------------- |
| 页面切换                 | < 200ms             |
| 章节列表加载             | < 500ms             |
| 章节内容保存             | < 300ms             |
| 首次生成响应（SSE 开始） | < 3s（受 API 影响） |

### 8.5 数据安全（本地范围）

- API Key 不以明文存入数据库（简单混淆，非强加密）
- 不向任何第三方发送用户数据（仅直接调用 LLM API）
- 日志中对 API Key 全部脱敏处理

---

## 9. 目录结构

```
AI_Novel/
├── backend/
│   ├── main.py                   # FastAPI 入口，加载路由
│   ├── config.py                 # 配置读取（.env + config.json）
│   ├── database.py               # SQLAlchemy 引擎和 Session
│   ├── logger.py                 # loguru 配置
│   ├── init_db.py                # 数据库初始化脚本
│   ├── routers/
│   │   ├── chapters.py           # 章节 & 卷 CRUD + 排序/版本
│   │   ├── generate.py           # 单章/批量生成（SSE）
│   │   ├── model_apis.py         # LLM API 配置 CRUD + 测试连接
│   │   ├── api_plans.py          # API 计划管理（多 API 编组）
│   │   ├── task_bindings.py      # 任务类型 → Plan 绑定
│   │   ├── templates.py          # 提示词模板文件 CRUD
│   │   ├── characters.py         # 人物 & 关系 CRUD（待实现）
│   │   ├── worldview.py          # 世界观设定读写（待实现）
│   │   ├── events.py             # 世界事件 CRUD（待实现）
│   │   └── system.py             # 系统设置/统计/导出（待实现）
│   ├── services/
│   │   ├── generator.py          # 生成引擎核心
│   │   ├── prompt_builder.py     # 提示词组装（模板 + 变量）
│   │   ├── model_router.py       # 模型路由：Task → Plan → API 解析
│   │   └── log_streamer.py       # 日志 SSE 推送（待实现）
│   ├── models/
│   │   ├── chapter.py            # Volume, Chapter, ChapterVersion
│   │   ├── character.py          # Character, CharacterRelation
│   │   ├── item.py               # Item, ItemOwnershipHistory
│   │   ├── event.py              # WorldEvent, EventParticipant
│   │   ├── model_api.py          # ModelApi（单个 LLM API 配置）
│   │   ├── api_plan.py           # ApiPlan, PlanApi, TaskPlanBinding
│   │   └── story_line.py         # StoryLine, ChapterStoryLine, ChapterCharacter
│   ├── repositories/             # 数据库操作封装
│   │   ├── chapter_repo.py       # 章节操作（已实现）
│   │   ├── character_repo.py     # 人物操作（待实现）
│   │   └── event_repo.py         # 事件操作（待实现）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── stores/
│   │   │   └── chapters.js       # 章节列表状态
│   │   ├── api/
│   │   │   ├── chapters.js       # 章节 API 封装
│   │   │   ├── generate.js       # 生成（SSE EventSource）
│   │   │   ├── model-apis.js     # API 配置接口
│   │   │   ├── plans.js          # Plan 管理接口
│   │   │   ├── task-bindings.js  # 任务绑定接口
│   │   │   ├── settings.js       # 系统设置接口
│   │   │   ├── characters.js     # 人物接口（待实现）
│   │   │   └── worldview.js      # 世界观接口（待实现）
│   │   ├── views/
│   │   │   ├── Dashboard.vue     # 工作台（仪表板骨架）
│   │   │   ├── OutlineView.vue   # 大纲树形视图
│   │   │   ├── ChapterEditor.vue # 章节编辑器（三列布局 + SSE 生成）
│   │   │   └── ModelRouteSettings.vue  # API/Plan/Task 配置页
│   │   └── components/
│   │       ├── layout/           # 布局组件（待填充）
│   │       ├── chapter/          # 章节子组件（待填充）
│   │       └── common/
│   │           └── StreamOutput.vue  # SSE 流式文本显示
│   ├── vite.config.js
│   └── package.json
├── data/
│   ├── worldview.json            # 世界观设定
│   ├── config.json               # 系统配置 + 版本号
│   ├── writing_style.json        # 全局写作风格
│   └── templates/                # 提示词模板（.md 文件）
├── logs/                         # 自动生成
├── novel.db                      # SQLite 数据库
├── .env                          # API Keys（不提交 git）
├── .env.example
└── README.md
```

---

## 10. 开发优先级

### Phase 1 — 核心可用（MVP）

1. 后端基础：FastAPI 项目骨架、SQLite 初始化、日志配置
2. 章节 CRUD 接口 + 前端章节列表和编辑器
3. 模型路由配置（至少支持 OpenAI 协议）
4. 基础提示词模板 + 提示词组装器
5. 单章流式生成（SSE）
6. 基础设置页（API Key 配置）

### Phase 2 — 世界观管理

1. 世界观设定编辑器
2. 人物 CRUD + 人物关系图（Vue Flow）
3. 提示词模板库（CRUD + 变量系统）
4. 章节关联人物/地点

### Phase 3 — 高级功能

1. 地图编辑器（Vue Flow）
2. 时间线 / 世界事件管理
3. 批量生成队列
4. 日志查看器（SSE 实时）
5. 章节版本历史与回滚

### Phase 4 — 完善体验

1. 仪表板统计
2. 剧情线管理
3. 物品归属历史追踪
4. 导出功能（TXT / EPUB / Markdown）
5. 全文搜索

---

*文档结束*