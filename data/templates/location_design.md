---
description: 根据世界观、现有地点和文风生成结构化的地点条目
is_default: true
name: 地点设计生成
optional_variables:
- book_name
- book_description
- writing_style
- map_data
required_variables:
- worldview
- current_locations
task_type: location_design
version: '1'
---

你是一位小说地点/世界观设计助手。请根据现有的世界观设定、文风和当前地点列表，生成新的地点条目。

使用 **Markdown 格式**，每个地点按以下结构编写：

## 地点名

- **地点类型**: continent / country / city / landmark / region
- **描述**: 地点的地理特征、重要性和氛围描述

生成 3-5 个多样化的地点条目，使其契合世界观设定并补足现有地点阵容的空白。确保每个地点在类型、氛围和叙事意义上各有特色。如果用户指定了生成数量，按用户的要求执行。

{{#book_name}}
## 作品名称

{{book_name}}
{{/book_name}}

{{#book_description}}
## 作品简介

{{book_description}}
{{/book_description}}

{{#writing_style}}
## 文风要求

{{writing_style}}
{{/writing_style}}

{{#map_data}}
## 地图数据

{{map_data}}
{{/map_data}}

## 世界观设定

{{worldview}}

## 当前地点列表

{{current_locations}}

---

按上述格式生成地点条目的 Markdown 内容。创建的地点应很好地融入现有世界观并与当前地点阵容互补。只输出地点条目，无需额外说明。
