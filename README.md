# Duplicate Prescription Detection Agent Prototype

## Problem Statement
This prototype runs before eRx transmission and identifies likely duplicate prescriptions using deterministic overlap logic. It supports clinician review and does not make final prescribing decisions.

## Why Rules-First
- Date math and overlap are deterministic and auditable.
- Candidate filtering is narrow and high-precision to minimize alert fatigue.
- Claude is optional and used only for ambiguous same-ingredient, different-strength overlap cases.

## Scope and Non-Goals
In scope:
- Same ingredient + same route + overlap.
- Same ingredient + different strength + overlap.
- Multi-pharmacy pattern as a risk amplifier, never standalone proof.
- Structured clinician-facing finding with evidence, limitations, and actions.

Non-goals:
- Clinical appropriateness decisions.
- Eligibility decisions.
- Adherence assumptions.
- Autonomous proceed or cancel decisions.

## Architecture Overview
Layer 1: Core engine (`src/`)
- Validation, normalization, deterministic windows and overlap.
- Rules-first candidate selection.
- Severity mapping and finding object generation.

Layer 2: Claude adapter (`src/llm.py`)
- Encapsulated Anthropic call path.
- Supports `USE_LLM`, `MOCK_LLM`, and safe fallback.
- JSON-only parsing and fallback behavior.

Layer 3: Presentation
- `app.py`: Streamlit web UI (primary).
- `notebook/duplicate_rx_agent_demo.ipynb`: notebook fallback using the same core engine.

## Repository Structure
```
project/
  README.md
  requirements.txt
  .env.example
  app.py
  notebook/
    duplicate_rx_agent_demo.ipynb
  data/
    pending_rx.json
    med_history.json
  src/
    models.py
    normalize.py
    overlap.py
    rules.py
    severity.py
    prompts.py
    llm.py
    finding.py
    runner.py
    logging_utils.py
  tests/
    test_overlap.py
    test_rules.py
    test_runner.py
    test_scenario_semaglutide.py
```

## Run Streamlit App
```powershell
cd C:\Users\ryans\OneDrive\Desktop\duplicate-rx-agent
python -m pip install -r requirements.txt
streamlit run app.py
```

## Run Notebook
Open `notebook/duplicate_rx_agent_demo.ipynb` in Jupyter, Colab, or Replit and run all cells.

## Enable Claude Mode
1. Copy `.env.example` values into your shell environment.
2. Set:
```powershell
$env:ANTHROPIC_API_KEY="<your_key>"
$env:USE_LLM="true"
$env:MOCK_LLM="false"
```
3. In Streamlit, enable `Use Claude for ambiguous cases`.

## Sample Expected Output
For the included semaglutide scenario:
- `pending_start_date = 2026-03-20`
- `pending_end_date = 2026-06-17`
- overlap with semaglutide 1mg fill = `11` days
- `duplicate_type = same_drug_same_strength`
- `severity = review_required`

## Known Limitations
- Medication history is an approximation, not ground truth.
- Normalization is simplified in v1.
- No real DoseSpot integration in prototype mode.
- No full RxNorm terminology service.
- No production auth or persistence.
- No real clinician action storage beyond prototype logging.

## Future Enhancements
- Real DoseSpot integration.
- RxCUI-driven normalization.
- Class-level duplicate detection.
- Better pharmacy switching heuristics.
- Additional medication families beyond semaglutide.
- Configurable thresholds by program.
- Analytics dashboard for false positives and overrides.
- Stronger audit storage.

## Verification Commands
```powershell
cd C:\Users\ryans\OneDrive\Desktop\duplicate-rx-agent
python -m pytest -q
python -m src.runner
```
