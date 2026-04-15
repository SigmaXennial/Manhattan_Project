# Genealogy Intelligence Platform Architecture

## Product Framing

This repository is now organized around a **local-first genealogy intelligence core**.

The long-term vision remains a broader genealogy platform with family tree management, research workflows, collaboration, subscriptions, and future DNA modules. The current implementation intentionally stops short of that end-state and focuses on the strongest near-term fit for the existing repository:

- standalone Python workflows
- launched from `bot.py`
- local LLM and vision support through Ollama
- public archive and web research connectors
- plain-text report outputs
- lightweight JSON exports for future local reuse
- a combined case bundle artifact for downstream local tooling

## Phased Roadmap

### Phase 1 — Local-only genealogy core (implemented foundation)

Current repository scope:

- GEDCOM intake and parsing
- shared in-memory genealogy data model
- structured tree reporting
- deterministic consistency checking
- research hint generation
- public archival recon
- broad public web recon
- document transcription
- evidence indexing
- proof-summary drafting
- structured JSON exports for tree, consistency, and hint data
- combined `Case_Bundle.json` assembly for the active research scope

Phase 1 outputs are intentionally plain-text and researcher review is required before any tree change is accepted.

### Phase 2 — Local knowledge layer and reusable case data

Reserved next-step direction:

- JSON or similar local caches for parsed trees and evidence
- reusable person/family records across workflows
- stronger evidence linking and source tracking
- better workflow chaining and operator shortcuts

The current JSON exports are meant to reduce migration friction into this phase, and `Case_Bundle.json` is the first combined package meant for future UI or local knowledge-layer consumption.

### Phase 3 — Local UI / desktop-style experience

Reserved boundary:

- tree browsing
- person detail views
- hint review queue
- transcription and document review panels

### Phase 4+ — Cloud, collaboration, subscriptions, DNA

Explicitly deferred:

- authentication and hosted multi-user access
- shared research workspaces and comments
- subscriptions and billing
- partner integrations with approval-gated APIs
- DNA upload, normalization, kit abstraction, matching, and reporting

## Current Runtime Architecture

### 1. Input Layer

- GEDCOM files
- local image files for document transcription
- researcher-entered person and locality targets

### 2. Parsing / Structuring Layer

- `genealogy_models.py`
- `gedcom_parser.py`
- `json_export.py`

This layer standardizes:

- `Person`
- `Family`
- `Event`
- `SourceReference`
- `Hint`
- `ConsistencyIssue`
- JSON payloads for local caches and later UI consumption
- a combined case bundle that keeps the active scope’s tree, issues, and hints together

### 3. Analysis Layer

- `analyze_tree.py` for structured tree reports and AI narrative
- `consistency_checker.py` for deterministic chronology and relationship rules
- `hint_engine.py` for missing-fact and locality-driven research hints
- `external_recon.py` for archival API lookups
- `master_investigator.py` for broader public web recon

### 4. Output Layer

Plain-text outputs:

- `Tree_Structure_Report.txt`
- `Consistency_Report.txt`
- `Research_Hints_Report.txt`
- `External_Recon_Report.txt`
- `Broad_Web_Recon_Report.txt`
- `Transcription_Report.txt`
- `Evidence_Index.txt`
- `Proof_Summary_Draft.txt`

Structured local cache outputs:

- `Tree_Data.json`
- `Consistency_Data.json`
- `Research_Hints_Data.json`
- `Case_Bundle.json`

`Case_Bundle.json` is the preferred Phase 2-ready handoff artifact because it centralizes the active scope’s structured tree data, deterministic issues, and generated hints into one file.

## Domain Boundaries for the End State

### Genealogy Core Domain

Future durable entities should include:

- trees
- persons
- families
- events
- sources
- media
- hints
- research tasks

### Research Intelligence Domain

Future extensions may include:

- reusable search connectors
- archival clients
- OCR/transcription post-processing
- evidence extraction and summarization pipelines

### DNA Domain

Reserved only — not implemented here:

- raw upload intake
- normalization pipeline
- kit/profile abstraction
- match engine
- ethnicity and segment reporting

This domain should remain isolated from identity data and from the current Phase 1 genealogy logic.

### Collaboration / Product Domain

Reserved only — not implemented here:

- invitations
- permissions
- comments
- subscriptions
- audit trails

## Storage Strategy

### Near-term

- filesystem for GEDCOM files, document images, reports, and JSON caches
- no database requirement in the current implementation

### Mid-term

- relational storage for users, trees, persons, families, and sources
- object storage for media and uploaded files

### Long-term DNA direction

- object storage for raw DNA uploads
- analytical storage for normalized marker workloads
- relational metadata and permissions storage
- background workers for preprocessing and match calculations

## Research Integrity Rules

The system should assist the genealogist without silently rewriting the tree.

That means the Phase 1 workflows are designed to produce:

- deterministic findings where possible
- AI summaries clearly separated from extracted data
- hints framed as suggestions, not facts
- reviewable plain-text outputs suitable for archival workflows
- structured JSON exports that mirror the reviewed local data without claiming additional certainty
- a combined case bundle that aggregates outputs but does not convert hypotheses into facts
