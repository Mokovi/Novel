---
task_type: outline_design
name: Arc Outline Design
is_default: false
version: 1.0
description: Generate an outline for a story arc (multiple chapters) based on arc description and chapter summaries.
required_variables:
  - arc_title
  - arc_description
  - chapter_summaries
optional_variables:
  - worldview
  - writing_style
  - character_profiles
  - volume_outline
---

You are a novelist designing the outline for a story arc within a long-form novel. Follow the instructions below precisely.

## Arc Title

{{arc_title}}

## Arc Description

{{arc_description}}

{{#writing_style}}
## Writing Style

{{writing_style}}
{{/writing_style}}

{{#worldview}}
## World Setting

{{worldview}}
{{/worldview}}

{{#character_profiles}}
## Character Profiles

{{character_profiles}}
{{/character_profiles}}

{{#volume_outline}}
## Parent Volume Outline

{{volume_outline}}
{{/volume_outline}}

## Existing Chapter Summaries

{{chapter_summaries}}

---

Based on the arc description and existing chapter summaries above, write a comprehensive arc outline. The outline should:

1. Describe the overall narrative arc and character development trajectory
2. Identify key plot points and turning points
3. Suggest how the existing chapters fit into the larger arc structure
4. Provide guidance for writing future chapters in this arc

Write the outline in Chinese, targeting 500-1000 words. Only output the outline content, no additional explanation.
