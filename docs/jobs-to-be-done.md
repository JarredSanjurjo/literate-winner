# Jobs To Be Done: v1 Classification and Reporting System

## Document Status

- Status: Draft v1
- Purpose: Translate the system design into discrete v1 jobs and implementation tasks
- Audience: Project owner, future contributors, reviewers
- Related documents:
  - `docs/system-design.md`
  - `docs/AI_Capability_Build_Spec_Pack.md`
  - `docs/AI_Capability_Case_Study_Pack.md`
  - `docs/design-reference.md`

## 1. Purpose

This document breaks v1 into concrete Jobs To Be Done and converts those jobs into discrete implementation tasks. It is intended to answer a practical question:

What must be built, in what order, and to what standard, for v1 to work end to end?

The system goal remains the same across the source documents:

- ingest messy business data from multiple source types
- classify and structure that data consistently
- validate the output
- persist traceable records
- surface results through reporting and review views

## 2. Main Job Statement

When an operations user receives messy business requests from different sources, they want the system to ingest, classify, validate, store, and report those requests, so that they can reduce manual triage effort, improve consistency, and maintain an audit trail.

## 3. Primary Users

- operations teams
- workflow coordinators
- implementation analysts
- customer service managers
- business owners reviewing requests

## 4. v1 Outcome

v1 is successful when a user can submit at least three source types through one pipeline and receive:

- a classified request
- a structured summary
- extracted entities
- risk flags
- a recommended next action
- a validated status or review-required status
- a persisted record available in reporting

## 5. v1 Job Map

The v1 job map is:

1. Capture input from a supported source.
2. Normalize the input into a canonical format.
3. Classify and extract meaningful fields.
4. Validate the output and apply business controls.
5. Store inputs, outputs, and run history.
6. Route uncertain or failed cases for review.
7. Report on processed and flagged work.

## 6. Core JTBD Statements

### Job 1: Capture Multi-Source Inputs

When a user has a request in text, csv, json, or pasted free text, they want the system to accept it without manual reshaping, so they can start processing quickly.

Desired outcomes:

- supported source types can be submitted through a consistent entry path
- unsupported input types fail clearly
- raw input is preserved

### Job 2: Normalize Inputs into One Shared Contract

When the system receives different source formats, it wants to convert them into one canonical structure, so downstream services do not need source-specific logic.

Desired outcomes:

- all adapters return the same intake schema
- metadata is attached consistently
- request IDs are generated once and reused everywhere

### Job 3: Classify and Extract Structured Meaning

When a request is ready for processing, the system wants to classify it and extract structured fields, so users receive actionable outputs rather than raw text.

Desired outcomes:

- request type is assigned from a fixed taxonomy
- summary is generated
- entities are extracted
- priority is assigned
- risk flags and next actions are produced

### Job 4: Validate and Control the Output

When model output is returned, the system wants to validate and control it before acceptance, so unreliable outputs do not silently enter reporting.

Desired outcomes:

- schema validation is enforced
- invalid enums and missing fields are detected
- low-confidence or unclear outputs are routed to review

### Job 5: Persist Traceable Records

When a request is processed, the system wants to save both source and result data, so the workflow is auditable and reportable.

Desired outcomes:

- raw input is stored
- structured outputs are stored
- prompt version and timestamps are stored
- run logs are queryable

### Job 6: Surface Review-Required Work

When a result is invalid or uncertain, the system wants to queue it for review, so operations users can resolve exceptions without losing the record.

Desired outcomes:

- review queue receives flagged items
- reasons for review are explicit
- review state is queryable in the UI

### Job 7: Produce Reporting Outputs

When users need to understand workload and outcomes, they want reporting views and exports, so they can review processed requests, flagged items, and aggregate trends.

Desired outcomes:

- processed records are visible in the app
- flagged items are visible in the app
- CSV export works
- dashboard metrics summarize system activity

## 7. Job-to-Component Mapping

| Job | Main Components |
|---|---|
| Capture Multi-Source Inputs | `src/adapters/*`, `src/main.py` |
| Normalize Inputs | `src/models/schemas.py`, `src/services/preprocessing.py`, `src/utils/ids.py` |
| Classify and Extract | `src/prompts/*`, `src/services/prompt_manager.py`, `src/services/classifier.py` |
| Validate and Control | `src/services/validator.py`, `src/services/business_rules.py` |
| Persist Traceable Records | `src/models/db_models.py`, `src/services/storage.py` |
| Surface Review-Required Work | `src/services/review.py`, `app/streamlit_app.py` |
| Produce Reporting Outputs | `src/services/reporting.py`, `app/streamlit_app.py` |

## 8. v1 Discrete Task Plan

This section translates the jobs into build tasks that can be completed sequentially.

### Phase 1: Foundation and Shared Contracts

#### Task 1.1 Create configuration loader

Goal:

- centralize environment and runtime settings

Deliverable:

- `src/config/settings.py`

Definition of done:

- settings load from environment variables
- prompt version, database URL, model name, and threshold are configurable

#### Task 1.2 Create shared enums

Goal:

- define fixed allowed values for source types, request types, priorities, statuses, and review states

Deliverable:

- `src/models/enums.py`

Definition of done:

- taxonomy is locked in code for v1
- validators and prompts can import the same enums

#### Task 1.3 Create Pydantic schemas

Goal:

- define canonical intake and output contracts

Deliverable:

- `src/models/schemas.py`

Definition of done:

- `CanonicalIntake` exists
- `ClassificationOutput` exists
- validation result and review decision models exist

#### Task 1.4 Create database models

Goal:

- define persistent tables for requests, outputs, logs, and review queue

Deliverable:

- `src/models/db_models.py`

Definition of done:

- SQLAlchemy models match the v1 schema
- tables can be initialized locally

### Phase 2: Input Capture and Normalization

#### Task 2.1 Create adapter base interface

Goal:

- create a consistent interface for all input adapters

Deliverable:

- `src/adapters/base.py`

Definition of done:

- base adapter interface exists
- adapters must implement the same load contract

#### Task 2.2 Implement text adapter

Goal:

- support `.txt` files and pasted text

Deliverable:

- `src/adapters/text_adapter.py`

Definition of done:

- reads raw text safely
- outputs canonical intake object

#### Task 2.3 Implement csv adapter

Goal:

- support CSV rows as separate requests

Deliverable:

- `src/adapters/csv_adapter.py`

Definition of done:

- each row maps to one request
- row data is transformed into normalized content plus metadata

#### Task 2.4 Implement json adapter

Goal:

- support semi-structured json source records

Deliverable:

- `src/adapters/json_adapter.py`

Definition of done:

- minimal expected keys are handled
- useful fields are flattened into normalized content

#### Task 2.5 Implement request ID and timestamp utilities

Goal:

- generate stable identifiers and timestamps consistently

Deliverable:

- `src/utils/ids.py`
- `src/utils/timestamps.py`

Definition of done:

- request IDs are unique and readable
- timestamp formatting is consistent across modules

#### Task 2.6 Implement preprocessing service

Goal:

- normalize content before prompting

Deliverable:

- `src/services/preprocessing.py`

Definition of done:

- whitespace and formatting are normalized
- important content is preserved
- preprocessing returns updated canonical intake

### Phase 3: Classification Pipeline

#### Task 3.1 Create prompt asset

Goal:

- store the first prompt version as a reusable asset

Deliverable:

- `src/prompts/classification_v1.md`

Definition of done:

- prompt includes taxonomy
- prompt includes JSON output schema
- prompt explicitly prohibits invented fields

#### Task 3.2 Implement prompt manager

Goal:

- load prompt files and prepare model messages

Deliverable:

- `src/services/prompt_manager.py`

Definition of done:

- prompt can be loaded by version
- message payload can be built from canonical intake plus prompt

#### Task 3.3 Implement classifier service

Goal:

- call the model and parse structured output

Deliverable:

- `src/services/classifier.py`

Definition of done:

- model call is wrapped in one service
- strict JSON is requested
- parsed output maps into `ClassificationOutput`

#### Task 3.4 Implement validator service

Goal:

- reject malformed or incomplete outputs

Deliverable:

- `src/services/validator.py`

Definition of done:

- schema validation runs after classification
- missing required fields are reported
- invalid enum values are reported

#### Task 3.5 Implement business rules service

Goal:

- apply deterministic post-processing controls

Deliverable:

- `src/services/business_rules.py`

Definition of done:

- unknown request types route to review
- low confidence can route to review
- unclear summaries can route to review

### Phase 4: Persistence and Review Workflow

#### Task 4.1 Implement storage service

Goal:

- isolate all database writes and reads

Deliverable:

- `src/services/storage.py`

Definition of done:

- requests can be saved
- outputs can be saved
- run logs can be saved
- review items can be saved

#### Task 4.2 Implement review service

Goal:

- centralize review queue creation and review reason handling

Deliverable:

- `src/services/review.py`

Definition of done:

- review records can be created from validation or rule failures
- review reasons are explicit and queryable

#### Task 4.3 Implement processing orchestrator

Goal:

- connect adapters, preprocessing, classification, validation, storage, and review flow into one executable path

Deliverable:

- `src/main.py`

Definition of done:

- one input can be processed end to end
- one batch can be processed end to end
- failure paths are logged

### Phase 5: Reporting and Output Layer

#### Task 5.1 Implement reporting service

Goal:

- provide reusable reporting queries for UI and export

Deliverable:

- `src/services/reporting.py`

Definition of done:

- processed records can be listed
- review queue can be listed
- aggregate metrics can be calculated

#### Task 5.2 Implement Streamlit UI

Goal:

- provide business-readable reporting and review views

Deliverable:

- `app/streamlit_app.py`

Definition of done:

- dashboard screen exists
- processed records table exists
- review queue table exists
- request detail view exists

#### Task 5.3 Implement CSV export

Goal:

- allow validated records to be exported for downstream use

Deliverable:

- export function in reporting service and UI hook

Definition of done:

- validated records can be downloaded as CSV

### Phase 6: Testing, Data, and Hardening

#### Task 6.1 Create synthetic datasets

Goal:

- provide realistic, noisy test inputs

Deliverable:

- files under `data/synthetic/`

Definition of done:

- at least architecture and hospitality examples exist
- examples include ambiguity and incomplete fields

#### Task 6.2 Add unit tests

Goal:

- verify the critical contracts and logic in isolation

Deliverable:

- `tests/test_adapters.py`
- `tests/test_schemas.py`
- `tests/test_validator.py`
- `tests/test_business_rules.py`
- `tests/test_storage.py`

Definition of done:

- adapters, schema rules, validator logic, and storage paths are tested

#### Task 6.3 Add smoke test

Goal:

- prove the end-to-end path works for v1

Deliverable:

- `tests/test_pipeline_smoke.py`

Definition of done:

- at least one realistic example processes end to end

#### Task 6.4 Add documentation support files

Goal:

- make the repo runnable and reviewable without explanation

Deliverable:

- `.env.example`
- updated `README.md`
- `.gitignore`

Definition of done:

- setup instructions are documented
- required environment variables are listed
- local artifacts are excluded from git

## 9. Acceptance Criteria by Job

### Capture Multi-Source Inputs

- text input works
- txt input works
- csv input works
- unsupported files fail clearly

### Normalize Inputs

- all adapters output the same schema
- request IDs are generated automatically
- metadata is stored consistently

### Classify and Extract

- output request type comes from a fixed taxonomy
- summary, priority, and next action are returned
- entities and risk flags are present when relevant

### Validate and Control

- malformed output is not accepted silently
- invalid enums are rejected
- low-confidence or unknown outputs route to review

### Persist Traceable Records

- requests and processed outputs are stored
- prompt version and timestamps are stored
- run logs can be queried

### Surface Review-Required Work

- flagged records appear in the review queue
- review reason is visible

### Produce Reporting Outputs

- dashboard metrics are visible
- processed requests are visible
- CSV export works

## 10. Priority Order

Not every task has equal value for proving the system. The priority order for implementation should be:

1. Canonical schemas and enums
2. Input adapters
3. Preprocessing
4. Prompt asset and classifier service
5. Validation and business rules
6. Persistence
7. End-to-end orchestrator
8. Reporting
9. Review queue UI
10. Test hardening and documentation polish

## 11. v1 Exit Criteria

v1 is complete when all of the following are true:

- at least one architecture example and one hospitality example run successfully
- at least three source types are supported
- the taxonomy is fixed and implemented
- validation and review routing are working
- all four core persistence tables are in use
- Streamlit can display processed and flagged records
- CSV export works
- the repo is runnable from the README

## 12. Recommended First Slice

The smallest useful first slice is:

- pasted text input
- txt input
- fixed taxonomy
- one classification prompt
- schema validation
- SQLite persistence
- one Streamlit table of processed records

That slice should be built first, then expanded to csv, review queue, metrics, and export.

## 13. Build Cadence

To keep progress visible and grounded, each work session should end with one of:

- a working module
- a passing test
- a documented design decision
- a sample input added
- a UI view added
- a commit that advances one discrete task

This keeps the project aligned with the goal of shipping a credible v1 rather than collecting disconnected ideas.
