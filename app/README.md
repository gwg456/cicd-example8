# LeanPlan (Vue3 + Flask SPA)

A minimal single-page weight-loss planner with an OpenAI-like UI.

## Features
- Vue 3 SPA (CDN script, no build tooling)
- Flask backend serves SPA and /api/plan endpoint
- Calculates BMR, TDEE, target calories, macros, daily/weekly plan

## Run locally

```bash
# From repository root
python3 -m venv .venv
./.venv/bin/pip install -U pip
./.venv/bin/pip install -r app/requirements.txt

# (Optional) If you need repo-level deps too
./.venv/bin/pip install -r requirements.txt || true

# Run server
./.venv/bin/python app/app.py
```

Then open http://localhost:5000

## Project layout
- app/app.py Flask app + API
- app/templates/index.html SPA entry (Vue 3)
- app/static/{main.js, style.css} UI logic and styles
- app/requirements.txt Python deps for this app

Note: For remote/WSL/containers, configure your proxy in the same environment if required.