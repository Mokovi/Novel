---
task_type: chapter_writing
name: Chapter Writing Default
is_default: true
version: 1.0
description: Default template for generating chapter prose based on summary, world setting, and writing style.
required_variables:
  - chapter_title
  - chapter_summary
  - writing_style
  - worldview
optional_variables:
  - character_profiles
  - chapter_outline
  - previous_chapter_summary
  - map_data
  - current_chapter_content
---

You are a novelist writing a chapter of a long-form novel. Follow the instructions below precisely.

## Chapter Title

{{chapter_title}}

## Chapter Summary

{{chapter_summary}}

{{#current_chapter_content}}
## Current Chapter Content

{{current_chapter_content}}
{{/current_chapter_content}}

{{#chapter_outline}}
## Chapter Outline

{{chapter_outline}}
{{/chapter_outline}}

{{#previous_chapter_summary}}
## Previous Chapter Recap

{{previous_chapter_summary}}
{{/previous_chapter_summary}}

## Writing Style

{{writing_style}}

## World Setting

{{worldview}}

{{#map_data}}
## Map & Locations

{{map_data}}
{{/map_data}}

{{#character_profiles}}
## Character Profiles

{{character_profiles}}
{{/character_profiles}}

---

Write the chapter content below. Aim for approximately 2000 words of compelling narrative prose that follows the summary and respects the established world setting and writing style. If no chapter title is provided, generate an appropriate title based on the content and output it as the first line prefixed with `# `.
