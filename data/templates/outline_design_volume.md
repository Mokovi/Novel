---
description: 根据卷的描述及其构成事件的大纲，为整卷生成大纲
is_default: false
name: 卷大纲设计
optional_variables:
- worldview
- writing_style
- character_profiles
- book_outline
- book_name
- book_description
- map_data
required_variables:
- volume_title
- volume_description
- arc_outlines
task_type: outline_design
version: '1'
---

你是一位长篇小说作家，正在为其中一卷设计大纲。请严格按照以下指令执行。

## 卷标题

{{volume_title}}

## 卷描述

{{volume_description}}

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

{{#book_outline}}
## 全书大纲

{{book_outline}}
{{/book_outline}}

## 事件大纲

{{arc_outlines}}

---

根据以上卷描述和其构成事件的大纲，编写全面的卷大纲。大纲应：

1. 描述整卷的整体叙事结构
2. 说明各事件如何衔接和相互推进
3. 确定主要主题元素和角色发展
4. 为整体节奏和进展提供指导

用中文编写大纲，没有字数限制。只输出大纲内容，无需额外说明。
