# Duplicate Rx Agent - Refreshed Export

Generated: 2026-04-04T16:40:00-07:00

## Current Product State
- App title: `Duplicate Prescription Agent`
- Primary workflow: Review Queue -> case selection -> Run Safety Check Simulation -> Clinical Review actions
- Rules-first duplicate and safety detection remains core behavior
- LLM mode labels: `Hard Coded Functionality` and `LLM Assisted`
- LLM path is bounded to ambiguous transition-like cases with deterministic fallback
- Metrics dashboard is active and driven by persisted review outcomes

## Current UI Behavior
### Review Queue
- Queue card metrics now show:
  - `Pending Review`
  - `Completed`
  - `False-positive rate 90d`
  - `Clinician action rate 90d`
- `Select review case` shows only cases that do not have a selected action yet in the active cycle
- After all cases are completed, queue auto-cycles for demo continuity

### Review Detail
- Top row:
  - `Patient and Pending Rx`
  - `Medication History`
- Medication History uses rounded white cards with black text and pill-like metadata labels
- Scenario chip format: `Scenario Type: <Title Case>`
- Clinical section label: `Clinical Review`
- Interaction risk panel removed
- Action notes field appears below recommended action buttons

### Recommended Actions
- Current action set:
  - `Approve Prescription`
  - `Start after 2026-03-30 if continuing existing supply`
  - `Cancel - Duplicate Prescription`
- `Deny Prescription` removed
- `Confirm last injection date and remaining supply` removed
- `Confirm pharmacy details` removed
- `Proceed with documented reason if clinically appropriate` removed
- For `info` severity: only `Proceed to Next Case`, with auto-advance to next review-required case and wrap-around behavior

## Metrics Logic (Current)
- Core KPIs:
  - false_positive_rate
  - high_severity_precision
  - clinician_action_rate
  - median_added_workflow_time_seconds
  - post_send_duplicate_friction_rate
- `Approve Prescription` records adjudication as `false_positive`
- `clinician_action_rate` only counts non-info severities (review_required class)
- Filters are data-driven: only values present in outcomes are shown
- Dashboard title: `Metrics Dashboard`

## Severity Policy (Current)
- Active severities in flow: `info`, `review_required`
- `block` is normalized into `review_required` in active experience

## LLM Comparison Spec File
- `C:\Users\ryans\OneDrive\Desktop\duplicate-rx-agent\LLM_MODEL_COMPARISON_SPEC.md`
- Contains prompt contracts, expected JSON schemas, runtime mode behavior, and fallback rules

## Key Module Map (Current)
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
- Latest result: `45 passed`

## Notes
- This refreshed export replaces stale historical snapshots and reflects current runtime behavior.
- For model comparison and prompt benchmarking, use `LLM_MODEL_COMPARISON_SPEC.md` as the canonical LLM I/O reference.
