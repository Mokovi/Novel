---
description: 根据事件描述和章节摘要，为故事事件（多个章节）生成大纲
is_default: false
name: 事件大纲设计
optional_variables:
- worldview
- writing_style
- character_profiles
- volume_outline
- book_name
- book_description
- map_data
required_variables:
- arc_title
- arc_description
- chapter_summaries
task_type: outline_design
version: '1'
---

你是一位长篇小说作家，正在为故事中的事件设计大纲。请严格按照以下指令执行。

## 事件标题

{{arc_title}}

## 事件描述

{{arc_description}}

{{#book_name}}
## 作品
- 标题：{{book_name}}
{{#book_description}}
- 简介：{{book_description}}
{{/book_description}}
{{/book_name}}

{{#writing_style}}
## 文风要求

{{writing_style}}
{{/writing_style}}

{{#worldview}}
## 世界观设定

{{worldview}}
{{/worldview}}

{{#character_profiles}}
## 角色档案

{{character_profiles}}
{{/character_profiles}}

{{#map_data}}
## 地图与地点

{{map_data}}
{{/map_data}}

{{#volume_outline}}
## 所属卷大纲

{{volume_outline}}
{{/volume_outline}}

## 现有章节摘要

{{chapter_summaries}}

---

根据以上事件描述和现有章节摘要，编写全面的事件大纲。大纲应：

1. 描述整体叙事弧线和角色发展轨迹
2. 确定关键情节节点和转折点
3. 说明现有章节如何融入更大的事件结构
4. 为事件内后续章节的写作提供指导

用中文编写大纲，没有字数限制。只输出大纲内容，无需额外说明。
