# Genealogy Intelligence Platform

A local-first genealogy research workstation built as a set of focused Python CLI workflows.

## Current Direction

This repository now implements **Phase 1** of a broader genealogy intelligence platform roadmap:

- GEDCOM ingestion and structured tree extraction
- deterministic chronology and relationship checking
- AI-assisted lineage narrative generation
- research hint generation based on tree gaps and localities
- public archival search through NARA and Chronicling America
- broader public web recon through Tavily and DuckDuckGo
- document transcription with local Ollama vision models
- evidence indexing and proof-summary draft assembly
- Phase 2-ready local JSON exports for structured reuse
- a combined case bundle JSON for downstream local tooling
- artifact and evidence metadata inside the case bundle

The project remains intentionally **local-only and CLI-first**. It does not yet implement collaboration, hosted accounts, subscriptions, or DNA workflows.

## Core Workflows

Launch the console from:

- `bot.py`

The operations console includes grouped workflows for:

- **Tree Intake**
  - import / parse GEDCOM
  - build `Tree_Structure_Report.txt`
  - export `Tree_Data.json`
- **Tree Analysis**
  - run `Consistency_Report.txt`
  - export `Consistency_Data.json`
  - generate `Research_Hints_Report.txt`
  - export `Research_Hints_Data.json`
- **Research Assistance**
  - run `External_Recon_Report.txt`
  - run `Broad_Web_Recon_Report.txt`
- **Document Intelligence**
  - generate `Transcription_Report.txt`
- **Case Assembly**
  - generate `Proof_Summary_Draft.txt`
  - build `Evidence_Index.txt`
  - maintain `Case_Bundle.json`

## New Phase 1 Modules

- `genealogy_models.py` — shared dataclasses for persons, families, events, sources, hints, and consistency issues
- `gedcom_parser.py` — reusable GEDCOM parsing and scope resolution
- `consistency_checker.py` — deterministic chronology and relationship validation
- `hint_engine.py` — research hint generation from missing facts and family structure
- `json_export.py` — lightweight structured JSON export helpers for local reuse, bundle assembly, and artifact metadata
- `report_utils.py` — shared plain-text report formatting helpers
- `ARCHITECTURE.md` — phased roadmap and future-ready boundaries

## Default Output Reports and Structured Caches

Text outputs:

- `Tree_Structure_Report.txt`
- `Consistency_Report.txt`
- `Research_Hints_Report.txt`
- `External_Recon_Report.txt`
- `Broad_Web_Recon_Report.txt`
- `Transcription_Report.txt`
- `Evidence_Index.txt`
- `Proof_Summary_Draft.txt`

Structured JSON outputs:

- `Tree_Data.json`
- `Consistency_Data.json`
- `Research_Hints_Data.json`
- `Case_Bundle.json`

`Case_Bundle.json` is the combined local package that merges the active scope’s tree, consistency, and hint sections into one reusable artifact.

It now also carries an **artifact/evidence section** with metadata for local files such as:

- generated reports
- structured JSON exports
- GEDCOM inputs
- transcription and document files
- evidence index artifacts

It also now includes a **person-centered artifact mapping** so each scoped person can be linked to:

- shared case artifacts relevant to the active bundle
- directly matched person-targeted artifacts
- related consistency issues
- related research hints

## Technology Stack

- `langchain-ollama` with `ChatOllama` for local LLM and vision tasks
- `langchain-core` for prompt construction and output parsing
- `langchain-tavily` for structured web search
- `duckduckgo-search` for supplemental public web discovery
- `requests` for archival API access
- `python-dotenv` for local environment loading

## Phase Boundaries

Implemented now:

- local GEDCOM workflows
- local report generation
- local JSON export for structured reuse
- combined case bundle JSON for downstream local tooling
- artifact and evidence metadata in the case bundle
- AI-assisted but evidence-aware research support
- CLI-first orchestration through `bot.py`

Explicitly deferred to later phases:

- local web UI / desktop interface
- cloud sync and multi-user collaboration
- subscriptions and billing
- partner API integrations that require approval
- DNA ingestion, normalization, matching, and health reporting

See `ARCHITECTURE.md` for the fuller roadmap.
