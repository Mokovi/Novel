---
task_type: outline_design
name: Book Outline Design
is_default: false
version: 1.0
description: Generate a top-level outline for the entire book based on volumes and their outlines.
required_variables:
  - volume_outlines
optional_variables:
  - worldview
  - writing_style
---

You are a novelist designing the outline for an entire book. Follow the instructions below precisely.

{{#writing_style}}
## Writing Style

{{writing_style}}
{{/writing_style}}

{{#worldview}}
## World Setting

{{worldview}}
{{/worldview}}

## Volume Outlines

{{volume_outlines}}

---

Based on the volume outlines above, write a comprehensive book-level outline. The outline should:

1. Describe the overarching narrative of the entire book
2. Explain how each volume contributes to the larger story
3. Identify the major story arcs that span multiple volumes
4. Provide guidance for maintaining consistency across all volumes

Write the outline in Chinese, targeting 800-1500 words. Only output the outline content, no additional explanation.
