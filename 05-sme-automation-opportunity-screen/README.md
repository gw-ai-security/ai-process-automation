# 05 · SME Automation Opportunity Screener

**Portfolio-company context:** before building an AI workflow, a mid-market operator needs to identify which manual process to investigate, whether the economics are plausible, and what prevents safe implementation. This small Python tool converts *hypothetical inputs* into a transparent screening report for a human workshop.

This is **not an AI model, a deal valuation, a measured ROI claim or an implementation approval**. It is an opportunity discovery aid, deliberately separated from the technical implementation demos in Projects 01–04.

## Decision workflow

1. Meet the process owner and define one repeatable task (e.g. quote intake, invoice data entry).
2. Record current case volume, time per case, the automatable share, setup cost, and monthly operations cost **as assumptions**.
3. Flag sensitive data, missing systems access or missing process-owner approval. The tool does *not* override these gates even when modeled savings look high.
4. Generate a transparent business-case estimate, prioritize discovery interviews, and validate assumptions with observed time samples **before** any pilot.
5. If a pilot is approved separately, use [REST API Integration Hub](../01-rest-api-integration-hub/README.md), [AI Workflow Automation Engine](../02-ai-workflow-automation-engine/README.md), or [LLM Output Quality Gate](../03-llm-quality-gate/README.md) for relevant technical demonstrations.

## Calculation (deterministic)

- `hours_saved_per_month = cases_per_month × automatable_share × max(manual_minutes − automated_minutes, 0) / 60`
- `gross_savings_per_month_eur = hours_saved_per_month × loaded_hourly_cost_eur`
- `net_savings_per_month_eur = gross_savings_per_month_eur − monthly_running_cost_eur`
- `first_year_net_after_setup_eur = 12 × net_savings_per_month_eur − setup_cost_eur`
- `simple_payback_months = setup_cost_eur / net_savings_per_month_eur` if monthly net benefit > 0, otherwise `null`

No discount rate, risk adjustment, demand variation, opportunity-cost model or benefit realization is included. The modeled labor-time savings do not imply payroll savings or headcount reductions. Rounding is to 2 decimals for EUR and 1 decimal for hours/payback. Classification is a **triage recommendation**, not a deployment decision.

## Local demo

Python 3.12+, no external packages or secrets:

```bash
cd 05-sme-automation-opportunity-screen
python screener.py --input samples/synthetic_opportunities.csv
python -m unittest discover -s tests -v
```

The sample uses fictional firms, names, and assumptions. All data is synthetic. JSON output is human-reviewable and can be redirected to a local file. Nothing is transmitted to external systems.

### Result statuses

- `candidate_for_discovery`: positive first-year modeled contribution, positive monthly net estimate, and no listed access/sensitivity/owner gate. **Still requires human scoping and pilot approval.**
- `needs_human_review`: high data sensitivity, unverified system access, or no process-owner approval. **Never bypassed by attractive economics.**
- `weak_economics`: weak or negative modeled net economics under the current assumptions, absent hard gate triggers. Consider process redesign rather than automation.

Sorted with discovery candidates first, then review cases, then weak cases; within groups, highest estimated monthly net first. This is a *qualitative decision order* rather than a probabilistic scoring model.

## Evidence and limitations

- Source code, sample CSV, and unittest scenarios are included and reproducible.
- There is **no** autonomous LLM, real ERP/CRM integration, transaction analysis, production deployment, factual operational benchmark, financial valuation, or observed business outcome.
- No personal or commercial data should be supplied to the public example. Actual customer information needs data inventory, GDPR analysis, credentials, permissions, controls, and a separate production design.
- Validate the inputs with users and actual process timing before relying on outputs. The model deliberately refuses to infer unknown numbers.
- Results can be used to propose a *discovery* sequence, not as investment committee recommendations.
