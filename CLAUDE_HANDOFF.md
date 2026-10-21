# Handoff: catch up a new Claude Code session

Read CLAUDE.md first for the project background, team, rules, scope update, and how to work with me. This file covers what has happened since, the current state, and what is left. My earlier Claude Code conversations live on other computers, so treat this file as the record.

## Current state of the repo
Commits on origin/main, newest first:
- b534a43 Phase 1: distributor-focused scoring, disqualifiers, top 10 view
- e7de789 Update project scope after client call
- fe04e7b Polish prototype UI, lock light theme, add scoring tests
- 9be93ee Add Streamlit prototype, update sample data and scoring tie-breaker
- 34fc386 Add rules-based lead scoring and scored sample output
- 3e90bdb Add fictional sample companies for prototype scoring
- 109a989 Add README and project folder structure
- 19d2853 Add starter notebook, gitignore, requirements, and project context

The tag sprint1-v1-before-scope-change marks fe04e7b, the last version before the scope change. That version scored distributors, private label, and OEM prospects across U.S. and international regions.

Run git pull, git log --oneline, and git status before changing anything.

## What is built (phase 1, after the scope change)
- data/sample_companies.csv: 20 fictional distributors, 19 in Florida and 1 in Georgia. Every company name uses an invented word and ends in "(Sample)". No name uses a real business, venue, or place name. Every website uses the .example domain, and data_source is "sample" on every row. Columns include distributor type, city, state, locations, product lines, fluid brands carried, and an aviation-only flag. All brand names are fictional. In fluid_brands_carried, "none" means the company carries no other fluid brands and a blank means unknown. The file has 3 thin-data rows (should be flagged needs review) and 5 rows built to hit each disqualifier.
- src/score.py: rules-based scoring out of 100. Product fit is 45 points, size from number of locations 20, other fluid brands carried 20, and distributor type 15. The size and brand weights are assumptions pending the on-site visit. All weights, product lines, disqualifiers, and next-step templates sit in one settings block at the top. The script never reads the notes column. It writes data/scored_leads.csv.
  - Target state: Florida, a placeholder until sales confirms.
  - Scored product lines: motorcycle, passenger vehicle, commercial vehicle, marine, power generation (an unconfirmed reading of "electrical power"), locomotive, transmission, and gear oils, plus coolant, antifreeze, and refrigeration fluid.
  - Older lines (hydraulic, rust protective, heat transfer, agricultural spray) are in a zero-weight list labeled "unconfirmed, ask sales". Aviation fluid never counts as a match.
  - Disqualifier rules: aviation only, outside the target state, not a distributor, already an Ultrachem customer (an assumption pending the on-site visit), and no in-scope product line. A disqualified lead is never ranked, whatever its score. The score stays in the CSV for transparency. A blank field never disqualifies a lead. Unknown data sends it to needs review instead.
  - Each ranked lead gets "why commercially attractive" text and a recommended next step. Both come from fixed templates, not AI.
  - Ranking: disqualified leads last and unranked, then score, then matched product lines, then data completeness, then name.
- app/app.py: Streamlit app that reads only data/scored_leads.csv and makes no outside calls.
  - The default view is the top 10 recommended distributors. A toggle shows all leads, including disqualified ones, which show "Not ranked" in the score column.
  - Filters by distributor type and city. Empty means all.
  - A "click a row" hint sits above the table. Clicking a row opens that lead.
  - The detail view shows why the lead is commercially attractive, the recommended next step, a "Why this score" list, a point breakdown, and data sources. Disqualified leads show the reason and what they would have scored.
  - A needs-review state with a plain-language message, and a "flag wrong data" button kept only for the session.
  - A banner says the data is sample, the scoring is rules-based, not AI, and Florida is a placeholder. The score is labeled a relative fit score, not a probability.
- .streamlit/config.toml: light theme locked, toolbar minimal, usage stats off.
- tests/test_score.py: 17 pytest checks, all passing. Run with python -m pytest.
- Streamlit is pinned at 1.66.0 in requirements.txt. Do not upgrade it, because the sidebar fixes use CSS aimed at its internal elements.

## On hold: phase 2
Do not build phase 2 until I bring notes from the on-site visit. Phase 2 is:
- Approve, Reject, and Edit in the app, each with a required reason. Reviewers are "Rep 1", "Rep 2", or a free-text name. Edit lets the rep rewrite the next step.
- Decisions saved to data/rep_decisions.csv, which must be git-ignored. Tests must use a temp file, not the real one.
- src/export.py: reads scored_leads.csv and the rep decisions and writes structured data, likely JSON, that another agent can consume. The format depends on the agent framework, which is still unknown.
- Phase 2 replaces the "flag wrong data" button.

## Honest framing (keep this in code, UI, and slides)
- The data is made up and the scoring is rules-based. The ranking shows the logic works as designed. It does not show the tool finds real good customers.
- The real validation is Ultrachem's sales reps saying which of the top 10 recommended distributors they would contact.
- An automated audit checked about 127 text and color pairs with no failures, but the table header and selected-row colors were estimated. Describe accessibility as "contrast checked with an automated audit", not as fully compliant.

## Context that came up since CLAUDE.md was first written
- The scope update after the client call is in CLAUDE.md. The questions for the on-site visit are in its Open items.
- Open question for the client: whether they want an EV-related segment. Treat it as a question, not an assumption.
- When I share the visit notes, update the Open items in CLAUDE.md, change the settings block in src/score.py, rerun score.py, rerun the tests, and regenerate scored_leads.csv.

## Sprint 1 context
- One-week sprint. Materials are due Friday, October 23, 2026 and the live presentation is Saturday, October 24.
- The brief requires a prototype showing one AI moment (the ranked list), one failure or low-confidence state (needs review), and one trust moment (reasons and sources). All three exist in the app.
- Team roles this sprint: Andrew Mederos is Scrum Master, Joel Mangal is Product Owner Liaison, Neville Abraham is Technical Lead, I am Software and Analyst Lead, and Edgar Aguilar is QA Lead. Every member must commit code.
- Still needed for the deck: user test notes from 3 to 5 people, clean screenshots of the three moments, and a backup demo recording.

## Environment notes
- Python 3.12 only. Python 3.15 breaks package installs.
- Desktop PC: .venv works normally and activates.
- Laptop: Windows blocks script activation and pip.exe through an Application Control policy. Do not use activate, pip, or streamlit launchers. Call the venv Python directly:
  - .venv\Scripts\python.exe -m pip install -r requirements.txt
  - .venv\Scripts\python.exe -m pytest
  - .venv\Scripts\python.exe -m streamlit run app/app.py
- The laptop repo path is inside OneDrive, which can lock files. If odd file errors appear, clone to a short folder outside OneDrive, such as C:\capstone.
- Never commit secrets. If an API key is added later, put it in .env and also add .streamlit/secrets.toml to .gitignore.

## Suggested next tasks
1. Confirm the environment works on this machine and the 17 tests pass.
2. After I share the on-site visit notes, update CLAUDE.md Open items and the scoring settings, then rerun everything.
3. Then build phase 2, as described above.
4. Optional app polish: make the lead detail easier to reach after a row click, and fit the Distributor type column without sideways scrolling.
5. Show me changes and wait for approval before committing.
