---
description: 根据摘要、世界观和文风生成章节正文的默认模板
is_default: true
name: 章节写作
optional_variables:
- character_profiles
- chapter_outline
- previous_chapter_summary
- map_data
- current_chapter_content
required_variables:
- writing_style
- worldview
task_type: chapter_writing
version: '1'
---

你是一位长篇小说作家，请严格按照以下指令创作章节内容。

## 章节标题

{{chapter_title}}

## 章节摘要

{{chapter_summary}}

{{#current_chapter_content}}
## 当前章节内容

{{current_chapter_content}}
{{/current_chapter_content}}

{{#chapter_outline}}
## 章节大纲

{{chapter_outline}}
{{/chapter_outline}}

{{#previous_chapter_summary}}
## 前文回顾

{{previous_chapter_summary}}
{{/previous_chapter_summary}}

## 文风要求

{{writing_style}}

## 世界观设定

{{worldview}}

{{#map_data}}
## 地图与地点

{{map_data}}
{{/map_data}}

{{#character_profiles}}
## 角色档案

{{character_profiles}}
{{/character_profiles}}

---

请写出约 2000 字的叙事正文，遵循摘要内容，贴合世界观和文风设定。如果没有提供章节标题，请根据正文内容生成一个合适的标题，并以 `# 标题` 格式输出为内容第一行。
