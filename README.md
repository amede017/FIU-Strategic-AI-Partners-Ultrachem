# Ultrachem Lead Intelligence Prototype

FIU MSIS capstone, ISM 6429 Business AI Capstone. Group 3, Strategic AI Partners.

This is a prototype, not a market-ready product. It helps Ultrachem's sales team find, score, and explain B2B prospects: distributors, private label customers, and OEMs.

## Status

Sprint 1. The data is made-up sample data, and the scoring is rules-based. No real AI model runs yet. Any AI output in this repo is mocked, and the code and UI say so. Scoring criteria are our assumptions until the client confirms them.

## How it works (planned)

1. **Collect** candidate companies from public sources. (`src/collect.py`)
2. **Enrich** each company with an LLM that reads its website and tags what it sells and which Ultrachem products it could buy. (`src/enrich.py`)
3. **Score** each company for fit with weighted rules. (`src/score.py`)
4. **Show** a ranked list with the reasons for each score and a draft outreach message. (`app/app.py`)

Each script does one step and saves its output to a file for the next step.

## Repo layout

```
data/          sample and processed files
notebooks/     exploration notebooks
src/           pipeline scripts: collect, enrich, score
app/           Streamlit interface
tests/         test set of companies for QA
requirements.txt
```

## Setup

You need Python 3.12. Do not use Python 3.15, because some packages fail to build on it.

```powershell
# Create the virtual environment (first time only)
py -3.12 -m venv .venv

# Activate it
.venv\Scripts\activate

# Install packages
python -m pip install -r requirements.txt
```

If you install a new package, update the file:

```powershell
python -m pip freeze > requirements.txt
```

## Run

Run both commands from the repo root with `.venv` active.

```powershell
# 1. Score the sample companies. Writes data/scored_leads.csv.
python src/score.py

# 2. Start the app. It opens in your browser at http://localhost:8501
python -m streamlit run app/app.py
```

To run the scoring tests: `python -m pytest`

Run step 1 again any time you change `data/sample_companies.csv` or the scoring settings at the top of `src/score.py`. Then refresh the app.

What the app does:

- Shows the ranked leads with filters by segment and region.
- Shows each lead's relative fit score, the reasons, a point breakdown, and the data sources.
- Marks leads with thin data as "needs review" and says what is missing.
- Has a "Flag wrong data" button. Flags last only for the browser session and are not saved.

The app reads only `data/scored_leads.csv` and makes no external calls. The theme settings, like font size and colors, are in `.streamlit/config.toml`.

## Team rules

- Never commit secrets. API keys go in `.env`, which git ignores.
- Do not commit client confidential data unless the team confirms it is allowed.
- Clear notebook outputs before you commit.
- Keep code simple and commented.
- Every team member commits code to this repo.

## Team

- Andrew Mederos: Scrum Master and team leader
- Joel Mangal: Product Owner Liaison
- Neville Abraham: Technical Lead
- Bryan Martinez: Software and Analyst Lead
- Edgar Aguilar: Quality Assurance Lead
