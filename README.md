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

The scoring script and the app are not built yet. When they are, run them from the repo root:

```powershell
python src/score.py
streamlit run app/app.py
```

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
