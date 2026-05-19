---
task_type: outline_design
name: Volume Outline Design
is_default: false
version: 1.0
description: Generate an outline for a volume based on its description and the outlines of its constituent arcs.
required_variables:
  - volume_title
  - volume_description
  - arc_outlines
optional_variables:
  - worldview
  - writing_style
  - book_outline
  - book_name
  - book_description
---

You are a novelist designing the outline for a volume of a long-form novel. Follow the instructions below precisely.

## Volume Title

{{volume_title}}

## Volume Description

{{volume_description}}

{{#book_name}}
## Book
- Title: {{book_name}}
{{#book_description}}
- Description: {{book_description}}
{{/book_description}}
{{/book_name}}

{{#writing_style}}
## Writing Style

{{writing_style}}
{{/writing_style}}

{{#worldview}}
## World Setting

{{worldview}}
{{/worldview}}

{{#book_outline}}
## Book Outline

{{book_outline}}
{{/book_outline}}

## Arc Outlines

{{arc_outlines}}

---

Based on the volume description and the outlines of its arcs above, write a comprehensive volume outline. The outline should:

1. Describe the overall narrative structure of the volume
2. Explain how the arcs connect and flow into each other
3. Identify major thematic elements and character developments
4. Provide guidance for the overall pacing and progression

Write the outline in Chinese, targeting 500-1000 words. Only output the outline content, no additional explanation.
