# Project context for Claude Code

## What this project is
FIU MSIS capstone, ISM 6429 Business AI Capstone (Dr. Hemang Subramanian). Team: Group 3, Strategic AI Partners.
Client: Ultrachem, a manufacturer and wholesaler of motor oils and other petroleum oils. Product lines include passenger and commercial vehicle oils, motorcycle, marine, and RV oils, transmission and gear oils, hydraulic fluids, rust and protective oils, industrial heat transfer fluids, and agricultural spray oils.
We chose the client's first proposed problem: AI-powered B2B customer acquisition. The goal is to identify, qualify, and prioritize high-value distributors, private label customers, and OEM opportunities in the U.S. and abroad.
The deliverable is a prototype, not a market-ready product.

## Product vision
For Ultrachem's sales team, a lead intelligence tool uses AI to find, score, and explain high-value distributor, private label, and OEM prospects so reps spend less time researching and more time in qualified conversations.
Outcome metric: share of the top 20 ranked leads that the client's sales contact rates as worth contacting.

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

## Open items
- The client call (CEO) happens the day after this file was written. The target segment, product lines, lead criteria, and any data will come from it. Update this file afterward.
- Unknown: whether the client wants an EV-related segment. Treat as a question for the client, not an assumption.

## First tasks for Claude Code
1. Check the environment: Python version, that `.venv` is active, and which packages are installed.
2. Create the folders above, a README, and a `.gitignore` that covers `.venv/`, `.env`, `__pycache__/`, and `.ipynb_checkpoints/`.
3. Create `data/sample_companies.csv` with about 15 to 20 realistic but clearly labeled sample companies across a few segments (distributors, fleet service, industrial maintenance, marine and RV, agricultural), with columns for name, type, region, website, product categories, and a data completeness field.
4. Write a rules-based scoring function in `src/score.py` that returns a score, the reasons, and a confidence level, and saves ranked results to `data/scored_leads.csv`.
5. Build a Streamlit app in `app/app.py` with a ranked list, a lead detail view showing reasons and sources, a low-confidence "needs review" state, and filters by segment and region.
