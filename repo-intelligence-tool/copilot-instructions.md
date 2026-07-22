# Copilot Instructions: Repo Intelligence Tool

## Mission
Build and maintain an internal repository intelligence system that:
- Indexes all repositories in the target GitHub organization.
- Extracts technology and implementation signals from source code and configs.
- Aggregates findings into queryable datasets.
- Powers an AI assistant that can answer portfolio-level engineering questions with evidence.

Example questions this project must answer:
- How many projects contain custom Esri WebMap widgets?
- How many projects use React?
- Which projects match, and which files implement those patterns?

## Scope
This project is for internal development and tracking.
Primary output is structured machine-readable data plus concise human-readable summaries.

## Core Principles
- Evidence first: every claim should be tied to matched files and pattern reasons.
- Reproducible scans: same inputs should produce stable results.
- Safe defaults: never expose secrets in logs or outputs.
- Incremental updates: avoid full re-scan if only a subset changed.
- Explainability: include enough detail that a developer can verify findings quickly.

## Existing Baseline
Current implementation already:
- Authenticates to GitHub API.
- Lists organization repositories.
- Optionally clones repositories.
- Computes basic tree, config, and source metrics.

Build future work on top of this baseline rather than replacing it.

## Required Data Model (Target)
Maintain an aggregated output (JSON and optionally CSV/SQLite) with at least:
- scan metadata:
  - generated_at
  - organization
  - repo_count
  - scan options
- repository metadata:
  - name, full_name, visibility, language, default_branch
- technology flags:
  - uses_react
  - uses_typescript
  - uses_esri_js_api
  - has_custom_esri_webmap_widgets
- evidence arrays for each flag:
  - file path
  - matched rule id
  - matched snippet or reason
- summary rollups:
  - count of repos by technology flag
  - top frameworks/libs by occurrence

## Detection Rules (Initial)
Implement rules as composable detectors with ids and rationales.

### React usage detectors
Treat repo as React-enabled when any of these are true:
- package.json dependencies or devDependencies contain react/react-dom.
- Source imports match:
  - import React from 'react'
  - from 'react'
- JSX/TSX files present with React component patterns.

### Esri usage detectors
Treat repo as Esri-enabled when any of these are true:
- package.json includes @arcgis/core or esri-loader.
- Source imports from @arcgis/core, esri/*, or arcgis namespaces.

### Custom Esri WebMap widget detectors
Treat as true when both conditions are met:
- Esri usage detected.
- Evidence of custom widget/component implementation near map/ui integration, such as:
  - classes/functions/components with names containing widget, mapWidget, legend, layerControl, basemapToggle, popup, or toolpanel.
  - files under likely widget paths (widgets/, components/map/, map/widgets/).
  - wiring code that attaches custom UI to a map view/container.

For each positive match, capture file-level evidence.

## Agent Behavior
When the user asks a portfolio question, the AI agent should:
1. Use aggregated index first (fast path).
2. If confidence is low or data is stale, selectively re-scan relevant repos.
3. Return:
   - total count
   - repository list
   - key evidence files per repository
   - optional code excerpts summary
4. Distinguish known vs unknown:
   - known: backed by index evidence
   - unknown: missing scan or ambiguous matches

## Response Format for Analytical Queries
Return answers in this order:
1. Direct answer (count + short statement).
2. Matching repositories.
3. Evidence examples (file paths and detector ids).
4. Caveats or confidence notes.
5. Suggested next scan action if needed.

## Engineering Guidance
- Keep detectors in separate modules with unit tests.
- Use explicit schemas for aggregated output to prevent drift.
- Favor deterministic regex/parsing heuristics before introducing heavier analysis.
- Keep clone and scan operations optional and configurable by CLI flags.
- Add caching keyed by repo + commit SHA where possible.

## Security and Privacy
- Never print tokens or credential values.
- Do not store secrets in output artifacts.
- Redact sensitive strings from captured snippets.

## Definition of Done for New Detection Features
A detection feature is complete when:
- Detector rule ids and rationale are documented.
- Unit tests cover positive and negative examples.
- Aggregated output includes count, per-repo flag, and evidence files.
- Agent responses can cite matching repos and files for that feature.

## Near-Term Milestones
1. Add detector framework and rule registry.
2. Extend current scanner to produce technology flags + evidence arrays.
3. Build aggregated summary outputs for portfolio queries.
4. Add query interface used by the AI agent.
5. Add tests for React and custom Esri WebMap widget detection.
