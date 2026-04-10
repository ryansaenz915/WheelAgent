# Duplicate Prescription Safety Review Prototype

## What This Prototype Is
A healthcare-oriented Streamlit prototype for pre-transmission duplicate-prescription and medication-safety review.

Key boundaries:
- Rules-first architecture for deterministic overlap and candidate filtering.
- Clinician remains final decision-maker.
- LLM support is optional and narrowly scoped to ambiguous same-ingredient, different-strength overlap cases.
- Evidence-first findings with clear limitations and auditable trace.
- UI severity wording uses `No Review Required` for internal `info` cases.
- Prompt-level LLM severity outputs are constrained to `review_required` and `no_review_required`.
- Drug class is now included in prompt context and surfaced in the UI.

## Product Workflow
1. Review Queue triage
2. Case detail review with patient context, evidence, and decision trace
3. Clinician adjudication capture and send gating
4. Optional post-send follow-up capture
5. 90-day metrics and assignment coverage reporting

## Updated Architecture
- `app.py`: thin page shell only
- `ui/`: Streamlit UI modules and component layer
- `src/`: business logic, validation, metrics, reporting, orchestration
- `data/`: seeded scenarios and mock persisted outcomes
- `notebook/duplicate_rx_agent_demo.ipynb`: notebook fallback remains supported

### UI Component Layer
- `ui/components/queue.py`
- `ui/components/finding_panel.py`
- `ui/components/decision_trace.py`
- `ui/components/review_form.py`
- `ui/components/reporting.py`
- `ui/theme.py`

### Core Logic Modules
- `src/review_cases.py`: centralized fixture loading with validation
- `src/review_outcomes.py`: review and follow-up persistence + validation boundary
- `src/derived_fields.py`: derived metrics fields
- `src/metrics.py`: segmented metric computation and QA metrics
- `src/reporting.py`: assignment coverage report and matrices
- `src/queue_ops.py`: queue filtering, sorting, summaries
- `src/llm.py` + `src/llm_schema.py`: bounded LLM routing and schema validation
- `src/config.py`: app defaults, feature flags, theme tokens

## Review Queue Improvements
- Queue-first triage layout instead of dropdown-first case selection
- Scan fields: review id, patient, issue, review type, severity, program, status, updated time
- Filtering: severity, review type, program, status, rules-only vs Claude-assisted, open/completed
- Sorting: severity, last updated, overlap days, unresolved first
- Summary cards: open reviews, review required, block count, completed today, 90d FPR, 90d action rate
- Demo shortcuts: flagship case, metrics page, assignment coverage page

## Detail Page Improvements
Stable 3-zone layout:
- Left: patient context and medication history evidence table
- Center: readable decision trace with routing summary
- Right: finding panel + clinician review capture

Enhancements:
- Structured severity/title/summary/chips in finding panel
- Clear triggered-rule and overlap-path visibility
- Raw JSON moved behind expanders
- Polypharmacy interaction panel treated as first-class content

## Clinical Review and Adjudication
- Grouped `st.form` capture for coherent submission
- Requiredness and gating rules for `review_required` and `block` severities
- Override reason enforcement when override is used
- Derived behavior-change field
- Workflow timeline strip (opened, reviewed, acknowledged, transmitted, follow-up)
- Post-send follow-up form with issue capture

## Metrics and Reporting
Core KPI set preserved:
- `false_positive_rate`
- `high_severity_precision`
- `clinician_action_rate`
- `median_added_workflow_time_seconds`
- `post_send_duplicate_friction_rate`

Added:
- Segmentation controls (window, severity, review type, program, duplicate type, LLM path)
- Segment distributions and QA views
- Methodology notes and caveats
- Exportable JSON metrics report
- Expanded assignment coverage and scenario matrix

## LLM Orchestration and Safety
- Explicit route decision logging: invoke vs skip with reason
- Strict classifier output schema validation
- Deterministic fallback on invalid/unavailable model output
- Prompt template separation and prompt version metadata
- Policy remains bounded to ambiguous transition-like cases only

## Run
```powershell
cd C:\Users\ryans\OneDrive\Desktop\duplicate-rx-agent
python -m pip install -r requirements.txt
streamlit run app.py
```

## OpenAI Key Handling
- API key loading is centralized in [services/openai_client.py](/Users/ryans/OneDrive/Desktop/duplicate-rx-agent/services/openai_client.py).
- Server-side code reads `OPENAI_API_KEY` from `st.secrets["OPENAI_API_KEY"]` with optional `OPENAI_API_KEY` env fallback.
- Model selection reads `st.secrets["OPENAI_MODEL"]` with safe default `gpt-5.4-mini`.
- LLM calls use the OpenAI Responses API in [src/llm.py](/Users/ryans/OneDrive/Desktop/duplicate-rx-agent/src/llm.py).
- Local secret file: `.streamlit/secrets.toml` (gitignored). Example starter file is `.streamlit/secrets.toml.example`.

### Local Development Setup
1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. Set your values:
```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-5.4-mini"
```
3. Run Streamlit normally:
```powershell
streamlit run app.py
```

### Streamlit Community Cloud Deployment
1. Open your app settings in Streamlit Community Cloud.
2. Go to Secrets.
3. Paste the same TOML key-value entries used locally.
4. Deploy. The app reads keys from `st.secrets` at runtime and does not require GitHub-stored secrets.

### Troubleshooting
- If LLM mode is enabled and no key is configured, the app shows:
  - `OpenAI API key is not configured. Add OPENAI_API_KEY to Streamlit secrets.`
- No API key, `st.secrets`, or environment dump is rendered in the UI.

## Tests
```powershell
cd C:\Users\ryans\OneDrive\Desktop\duplicate-rx-agent
python -m pytest -q
```

Current expected result:
- `45 passed`

## Verification Scope
Validated:
- Existing regression suite
- Added queue/filter/sort tests
- Added metrics segmentation tests
- Added LLM routing and fallback tests
- Added assignment-report enhancement tests

Not in scope:
- Real auth/user management
- Live DoseSpot integration
- Autonomous prescribing behavior
