# Project context for Claude Code

## What this project is
FIU MSIS capstone, ISM 6429 Business AI Capstone (Dr. Hemang Subramanian). Team: Group 3, Strategic AI Partners.
Client: Ultrachem, a manufacturer and wholesaler of motor oils and other petroleum oils. Product lines include passenger and commercial vehicle oils, motorcycle, marine, and RV oils, transmission and gear oils, hydraulic fluids, rust and protective oils, industrial heat transfer fluids, and agricultural spray oils.
We chose the client's first proposed problem: AI-powered B2B customer acquisition. The goal is to identify, qualify, and prioritize high-value distributors, private label customers, and OEM opportunities. After the on-site visit, the target region is Georgia, North Carolina, South Carolina, and Virginia, and overseas is out of scope. See the scope updates below.
The deliverable is a prototype, not a market-ready product.

## Product vision
For Ultrachem's sales team, a lead intelligence tool uses AI to find, score, and explain high-value distributor, private label, and OEM prospects so reps spend less time researching and more time in qualified conversations.
Outcome metric: share of the top 10 ranked leads that the client's sales contact rates as worth contacting.

## How it works (planned)
1. Collect candidate companies from public sources (company websites, directories, trade data).
2. Enrich each company with an LLM step that reads its website and tags what it sells, who it serves, and which Ultrachem product categories it could buy.
3. Score each company for fit with weighted, rules-based criteria. Criteria are assumptions until the client confirms them.
4. Show a ranked list with the reasons for each score and a draft outreach message.

## Current stage: Sprint 1 (one week)
Sprint 1 deliverable is a clickable or runnable prototype plus the Scrum evidence. A mocked or rules-based AI is acceptable if we say so.
The prototype must show:
- One AI moment: a ranked lead list the user acts on.
- One failure or low-confidence state: a lead with thin data is flagged "needs review".
- One trust moment: each score shows its reasons and data sources.
Use made-up or small sample data (15 to 20 companies) until the client confirms the target segment and criteria.
Sprint review is Saturday, October 24, 2026. Materials are due Friday, October 23.

## My role (the user, Bryan)
Software and Analyst Lead. Tasks: organize the repo, choose the stack, build a basic interface mockup showing leads and rankings, coordinate coding practices, and prepare a small demo. Deliverable: UI mockup or prototype scaffold committed to GitHub.

## Team
- Andrew Mederos: Scrum Master and team leader
- Joel Mangal: Product Owner Liaison, leads client interview
- Neville Abraham: Technical Lead, data sources and architecture
- Bryan Martinez: Software and Analyst Lead
- Edgar Aguilar: Quality Assurance Lead
Every member must commit code to this repo.

## Environment
- Windows 11, PowerShell, VS Code
- Python 3.12 in a virtual environment at `.venv` (do not use Python 3.15, packages fail to build)
- Activate with `.venv\Scripts\activate`
- Dependencies are in `requirements.txt`. Update it after installing packages.
- Planned stack: Python, pandas, Jupyter notebooks for exploration, Streamlit for the interface

## Repo layout
```
data/          sample and processed files
notebooks/     01_lead_scoring_prototype.ipynb
src/           collect.py, enrich.py, score.py (to create)
app/           app.py for Streamlit (to create)
tests/         test set of companies for QA (to create)
requirements.txt
README.md
```

## Rules
- Never commit secrets. API keys go in `.env`, which is git-ignored.
- Do not commit client confidential data. Keep client files out of the repo unless the team confirms it is allowed.
- Clear notebook outputs before committing.
- Keep each script to one step, saving its output to a file for the next step.
- Keep code simple and commented. Teammates will read and run it.
- Say plainly in the code and UI when AI output is mocked.

## How to work with me
- Plain, concise explanations with simple sentence structure. No em dashes. Use few parentheses.
- Give me finished code I can run, not partial drafts that need heavy rework.
- When code goes into a notebook, tell me exactly which cell it belongs in.
- Be honest about limits. Do not present assumptions or mock results as validated.
- Make small, incremental changes when I ask for revisions instead of rewriting everything.

## First tasks for Claude Code
1. Check the environment: Python version, that `.venv` is active, and which packages are installed.
2. Create the folders above, a README, and a `.gitignore` that covers `.venv/`, `.env`, `__pycache__/`, and `.ipynb_checkpoints/`.
3. Create `data/sample_companies.csv` with about 15 to 20 realistic but clearly labeled sample companies across a few segments (distributors, fleet service, industrial maintenance, marine and RV, agricultural), with columns for name, type, region, website, product categories, and a data completeness field.
4. Write a rules-based scoring function in `src/score.py` that returns a score, the reasons, and a confidence level, and saves ranked results to `data/scored_leads.csv`.
5. Build a Streamlit app in `app/app.py` with a ranked list, a lead detail view showing reasons and sources, a low-confidence "needs review" state, and filters by segment and region.

## Scope update after client call
- Focus: distributors only. Private label and OEM moved to backlog.
- Geography: Georgia, North Carolina, South Carolina, and Virginia, confirmed at the on-site visit.
- Output: a short curated list. For each lead: who to pursue, why it is commercially attractive, and the recommended next step.
- Human in the loop: sales reps approve, reject, or edit recommendations with a reason.
- Delivery: an agent that connects to Ultrachem's existing agent network. The ranking must be saved as structured data another agent can consume.
- Products: transportation (motorcycles, vehicles, boats, electrical power, locomotive) and water-based (coolants, antifreeze, refrigeration). No aviation fluids.
- Outcome metric: share of the top 10 recommended distributors the reps say they would contact.
- Top risk: the agent surfaces leads that are not real opportunities.
- Still unknown after this call: disqualifying factors, sales cycle, agent framework. The on-site visit settled the target region and what counts as a distributor. See below.

## Scope update after the on-site visit
- Target region: Georgia, North Carolina, South Carolina, and Virginia. Overseas is out of scope. Florida was only a placeholder.
- A distributor has a physical warehouse that receives truckloads, its own sales team, and resells to businesses such as shops and retail chains. A company that only wants distributor pricing, without the infrastructure, does not qualify.
- Any distributor type is fine if the product fits. A distributor does not need to sell lubricants today. The company's example was a battery distributor that added Ultra1Plus and sold well.
- Two fit tests from the company: category gap, and pricing gap (the distributor makes money and the deal works for both sides). Pricing gap cannot come from public data, so show it as "verify with sales".
- The company already has agents in Texas that find leads, scrape pages, and send emails. Our value is the ranking and the explanations. Referrals from clients matter to them.
- Excluding existing customers is our assumption, not their rule. They have little presence in these four states.
- Tooling: Python. The agent is added to their agent stack later.
- Next focus: the ranking system, and how an agent finds distributors itself instead of being given a list.

## Open items
- Dataset: the AI lead said he may provide one. SBDC may supply a list of businesses. Contents, format, and terms are unknown. Keep any real data out of the repo and do not use it with AI tools without approval.
- The company's checklist of good and bad distributors has not been received.
- Whether referrals or warm introductions should affect the ranking.
- How the Texas agent works and what it outputs.
- The agent framework and data format.
- Whether a distributor carrying a competing brand helps or hurts it as a lead. The prototype assumes it helps.
- What "electrical power" covers. The prototype reads it as power generation oil, which is unconfirmed.
- The detailed sales cycle, from first call to first order, was not captured at the visit.
- No follow-up meeting is scheduled. We can contact the people we met.
