# Update and Expansion Mode

Use this reference when the user wants to extend or modify an existing design system or screen set.

## Change Modes
- `create_new`
- `add_screens`
- `update_existing_screens`
- `expand_platforms`
- `restyle_existing`

## Detection
- "thêm màn" / "add screens" => `add_screens`
- "sửa màn" / "update screen" / "add feature" => `update_existing_screens`
- "thêm desktop/tablet/mobile" => `expand_platforms`
- "đổi style / restyle" => `restyle_existing`
- otherwise => `create_new`

## Rules
- Preserve frozen foundation tokens unless the user explicitly changes them.
- Preserve shared primitives and naming unless a real refactor is required.
- In `add_screens`, generate only new screens and shared primitives they need.
- In `update_existing_screens`, touch only the affected screens and shared assets they depend on.
- In `expand_platforms`, add only the requested platform files.
- In `restyle_existing`, keep IA and screen responsibilities unless the user asks for structural changes.

## Output
```yaml
change_mode: add_screens
targets:
  - mobile-history
  - desktop-history
preserve:
  - foundation.css
  - shared.css
```
