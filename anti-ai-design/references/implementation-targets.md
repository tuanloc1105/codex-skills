# Implementation Targets

Resolve the host implementation target before generating screens.

## Modes
- `html_bundle` — plain multi-file HTML/CSS/JS output
- `sveltekit` — output should respect SvelteKit route and component structure expectations
- `shadcn_ui` — output should preserve shadcn/ui + Radix primitive semantics
- `antd` — output should preserve Ant Design workflow, density, and data-heavy patterns
- `tailwind_css` — Tailwind utility-first output; design tokens live in `tailwind.config`; minimize custom CSS
- `custom_app` — custom React or framework app without a specific component library contract

## Detection rules
1. If the user explicitly asks for HTML bundle or pure prototype output, use `html_bundle`.
2. If the repo, prompt, or docs mention SvelteKit or `.svelte` routes, use `sveltekit`.
3. If the repo or user references shadcn, Radix, or `ui/` primitives matching shadcn conventions, use `shadcn_ui`.
4. If the repo or user references Ant Design, `antd`, or enterprise table/form workflows built around it, use `antd`.
5. If the repo or user references Tailwind CSS utilities, `tailwind.config`, or `tw-` class conventions without a specific component library, use `tailwind_css`.
6. Otherwise use `custom_app`.

## Cross-target rule
Preserve host-stack ergonomics. Customize hierarchy, tokens, layout emphasis, copy, and motion before inventing a new component anatomy.

## Internal output
```yaml
implementation_target: html_bundle
host_constraints:
  - preserve bundle contract
  - custom layout primitives allowed
```
