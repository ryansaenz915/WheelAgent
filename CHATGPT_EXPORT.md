# Duplicate Rx Agent - Refreshed Export

Generated: 2026-04-05T00:00:00-07:00

## Current Product State
- App title: `Duplicate Prescription Agent`
- Primary workflow: Review Queue -> case selection -> Run Safety Check Simulation -> Clinical Review actions
- Rules-first duplicate and medication safety logic remains primary decision engine
- LLM mode labels: `LLM Assisted` and `Hard Coded Functionality` (LLM Assisted is default)
- LLM path is tightly bounded to ambiguous same-ingredient, different-strength transition cases
- Ambiguous LLM path now uses a **single OpenAI API call** that returns both classifier + structured finding payload
- Metrics dashboard is driven by persisted review outcomes and post-send follow-up data

## Current UI Behavior
### Global UI
- Light theme first paint enforced via `.streamlit/config.toml`
- Header, nav, and body spacing adjusted for cleaner visual hierarchy
- Buttons: white background + black text, selected state uses light gray

### Review Queue
- Queue is dropdown-based case selection (all seeded cases visible)
- Pending/completed inline header counters removed per current UX direction
- Selecting a case opens detail immediately below queue

### Review Detail
- Layout order:
  - Run Safety Check Simulation
  - Clinical Review panel + recommended actions
  - Patient and Pending Rx (left)
  - Medication History (right)
- Medication History:
  - White card rows with black text
  - `Ingredient` and `Strength` pills removed
  - Pill order now shows `Supply End Date` before `Days Supply`
- Scenario chip format: `Scenario Type: <Title Case>`
- Clinical section label: `Clinical Review`

### Recommended Actions
- Current action set:
  - `Approve Prescription`
  - `Start after <date> if continuing existing supply`
  - `Cancel - Duplicate Prescription`
- `Action Notes (optional)` appears below actions
- Auto-advance to next case occurs on:
  - `Approve Prescription`
  - `Start after <date>...`
  - `Cancel - Duplicate Prescription`
- For internal `info` severity, user-facing label displays as `No Review Required`

## Metrics Logic (Current)
- Core KPIs:
  - `false_positive_rate`
  - `high_severity_precision`
  - `clinician_action_rate`
  - `median_added_workflow_time_seconds`
  - `post_send_duplicate_friction_rate`
- `Approve Prescription` maps to adjudication `false_positive`
- `clinician_action_rate` counts actionable non-info severities
- Filters are data-driven and only show values present in outcomes
- Dashboard title: `Metrics Dashboard`

## Workflow Timing Instrumentation
- Case timer now starts when case is selected/opened on screen
- Outcome save computes `opened_at -> resolved_at` duration
- Metrics cache is cleared on every saved action so median time updates immediately

## Severity Policy (Current)
- Internal severity values: `info`, `review_required`
- User-facing label mapping: `info` -> `No Review Required`
- `block` is normalized into `review_required` in active UX

## LLM Path (Current)
- OpenAI client is centralized in `services/openai_client.py`
- Secrets source:
  - `st.secrets["OPENAI_API_KEY"]` (primary)
  - `OPENAI_API_KEY` env fallback
- Model source:
  - `st.secrets["OPENAI_MODEL"]` with default `gpt-5.4-mini`
- Responses API used in server-side code only
- Deterministic fallback occurs if:
  - LLM mode disabled
  - key/client unavailable
  - API/schema parsing fails

## Security and Secret Handling
- `.streamlit/secrets.toml` is gitignored and not committed
- `.env` and `.env.*` are gitignored
- App shows concise admin-safe error if key missing
- No secret dictionary or API key is rendered in UI

## Key Module Map
### App shell and UI
- `app.py`
- `ui/app_shell.py`
- `ui/state.py`
- `ui/theme.py`
- `ui/formatting.py`
- `ui/pages/review_queue_page.py`
- `ui/pages/review_detail_page.py`
- `ui/pages/metrics_page.py`
- `ui/components/queue.py`
- `ui/components/finding_panel.py`
- `ui/components/reporting.py`
- `ui/components/review_form.py`

### Core logic
- `services/openai_client.py`
- `src/finding.py`
- `src/llm.py`
- `src/prompts.py`
- `src/llm_schema.py`
- `src/runner.py`
- `src/transmission_service.py`
- `src/severity.py`
- `src/metrics.py`
- `src/review_cases.py`
- `src/review_outcomes.py`
- `src/derived_fields.py`
- `src/validation.py`
- `src/queue_ops.py`
- `src/storage.py`
- `src/config.py`

### Data and scenarios
- `data/review_queue.json`
- `data/mock_review_outcomes.json`
- `data/mock_post_send_outcomes.json`
- `data/cases/case_01_exact_duplicate.json`
- `data/cases/case_02_transition_no_overlap.json`
- `data/cases/case_03_transition_overlap.json`
- `data/cases/case_04_early_refill.json`
- `data/cases/case_05_same_class_anticoagulant.json`
- `data/cases/case_06_polypharmacy_qt_risk.json`

## Current Validation State
- Baseline command: `python -m pytest -q`
- Latest result: `48 passed`

## Presentation Notes
- Prompt/model comparison reference:
  - `LLM_MODEL_COMPARISON_SPEC.md`
- This export is intended to feed external model/code-review tools for architecture and workflow feedback.
