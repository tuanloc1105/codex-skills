# Working Brief Synthesis

Normalize all inputs into one internal brief before generation starts.

## Required internal brief
```yaml
project_name:
project_type:
source_of_truth:
input_mode:
execution_mode:
implementation_target:
change_mode:
output_intent:
platforms: []
requested_root_launcher: false
index_mode: navigation_hub
explicit_screen_list: []
screens: []
style_direction:
style_selection_mode:
color_direction:
color_selection_mode:
auto_selection_notes: []
brand_specificity_mode:
user_roles: []
primary_flows: []
business_rules: []
constraints: []
frozen_system:
  preserve_tokens: true
  preserve_shared_primitives: true
```

## Rules
- This internal brief must exist before screen generation begins.
- Fill fields in this order:
  1. docs
  2. existing artifacts
  3. one concise user question round
  4. safe defaults
- Generate from the brief, not directly from a messy transcript.
- In no-docs mode, synthesize a brief from the user's short prompt rather than blocking.
- In update mode, preserve existing frozen system fields unless explicitly changed.
- Default `index_mode` to `navigation_hub` when a root `index.html` exists only to help the user open screens quickly.
- Upgrade `index_mode` to `review_canvas` only when the user explicitly asks to see multiple screens or states together on one review surface.
- If docs expose only one broad tool screen but the documented flow materially separates preparation from post-generation handling, record that decomposition in `inferred_screen_split` and let `screens` reflect the operational bundle output.
