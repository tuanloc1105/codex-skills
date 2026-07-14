# Discovery Checklist

Use this checklist to discover the project comprehensively before updating agent docs. Do not paste this checklist verbatim into `AGENTS.md`; convert findings into routing guidance.

## Repository Shape

- Detect repo root, monorepo workspaces, package roots, app roots, library roots, and generated/vendor directories to avoid.
- Read top-level docs: `README*`, `CONTRIBUTING*`, `CLAUDE.md`, existing `AGENTS.md`, `docs/`, `.github/`, and project-specific planning docs.
- Identify language ecosystems from manifests: `package.json`, `pnpm-workspace.yaml`, `yarn.lock`, `Cargo.toml`, `pyproject.toml`, `requirements*.txt`, `go.mod`, `pom.xml`, `build.gradle`, `Gemfile`, `composer.json`.
- Identify the source-of-truth files agents should read for dependency, framework, runtime, and toolchain versions; do not copy those version numbers into agent docs.
- Identify package boundaries and ownership conventions.

## AI Tooling Docs To Migrate

- Check for agent/tool instructions: `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`, `.claude/skills/`, `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `.devin/rules/`, `.windsurf/rules/`, `.windsurfrules`, `.clinerules`, `GEMINI.md`, `.gemini/`, `.codex/`, and `AGENTS.md`.
- Treat these files as evidence, not authority. Migrate durable repo guidance, commands, paths, conventions, and gotchas; skip tool-specific syntax that does not apply to Codex.
- Do not copy personal-only preferences, machine-local paths, secrets, or private account details into shared `AGENTS.md`.
- If an existing tool config conflicts with the live repo, trust verified repo files and record uncertainty only when it helps future agents.

## Entrypoints And Runtime

- Find app entrypoints, CLIs, workers, scheduled jobs, serverless functions, background consumers, route definitions, and bootstrapping files.
- Find environment loading and config validation: `.env.example`, config modules, secrets references, feature flags, and runtime defaults.
- Find external service integrations: databases, queues, caches, object storage, auth providers, payment providers, email/SMS, analytics, AI providers, and internal APIs.

## Source Map

- Map each major source directory to its purpose.
- For each package/module, identify the first files an agent should read for changes in that area.
- Identify shared utilities, core domain models, dependency injection, state management, API clients, and cross-cutting middleware.
- Mark generated code and files that should not be edited directly.

## Frontend And Product Surface

- Identify frameworks, route files, layouts, design system, component library, state/data fetching, forms, validation, auth gates, and test utilities.
- Map user-facing flows to route/component folders.
- Note visual asset locations and styling conventions.

## Backend, API, And Data

- Identify API route/controller structure, service layer, domain layer, data access layer, schemas, migrations, seeds, background jobs, and authorization checks.
- Map public API contracts and internal API clients.
- Note where to read for database models, validation schemas, and permission logic.

## Build, Test, And Quality

- Record package-manager commands for install, dev, build, lint, format, typecheck, unit tests, integration tests, e2e tests, and focused test execution.
- Identify test locations, fixture factories, mocks, snapshots, and test-data conventions.
- Identify CI workflows and which local checks correspond to CI.

## Infrastructure And Operations

- Find Dockerfiles, compose files, deployment configs, Terraform/Pulumi/CDK, Kubernetes manifests, CI/CD workflows, release scripts, and observability config.
- Note deployment environments and commands only when visible in repo docs/config.
- Record operational runbooks or migration/release procedures.

## Existing Docs Gap Review

- Compare discovered areas with existing `AGENTS.md`.
- Classify gaps as missing routing, stale path, stale-prone dependency/framework version claim, bloated generic advice, duplicated guidance, unclear source of truth, or docs that belong under `docs/agent/`.
- Add missing routing for undocumented modules, packages, workflows, tests, configs, and operational surfaces.
- Remove or correct stale paths only after verifying the current repo state.
- Replace recorded library, dependency, framework, runtime, or toolchain versions with routing to the manifest, lockfile, toolchain file, Dockerfile, or CI config that owns the current value.
- Preserve user-authored guidance unless it is demonstrably stale or conflicts with current repo structure.
- Ask the user only for gaps the repository cannot answer, such as branch policy, review etiquette, required local services, or team-specific test expectations.
