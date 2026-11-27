# CivicVerse AI — Multi-Agent Urban Crisis Simulation & Decision Intelligence Platform

CivicVerse AI is an interactive urban digital-twin simulation platform designed to model city-level crises, coordinate specialized deterministic AI agents, allocate constrained emergency resources, compare competing response strategies, and audit explainable trade-offs prior to real-world execution.

## 1. System Architecture
- **Frontend (`frontend/`, port `5174`)**: React 19, TypeScript, Vite, Three.js / React Three Fiber / Drei 3D city digital twin, Tailwind CSS, Recharts strategy comparison analytics.
- **Backend (`backend/`, port `8001`)**: FastAPI, Python 3.12, Pydantic v2, SQLAlchemy ORM, WebSockets, Pytest.
- **Persistence & Cache**: PostgreSQL 16 (port `5433`, with automatic SQLite fallback) & Redis 7 (port `6380`).

## 2. Core Algorithmic Design
- **Zone Risk & Demand Engine (`backend/app/simulation/risk_engine.py`)**: Evaluates 8 urban zones across Thermal Stress (32%), Socio-Economic Vulnerability (24%), Water Deficit (20%), Infrastructure Fragility (14%), and Medical Access Gap (10%).
- **Multi-Agent Council (`backend/app/agents/`)**:
  1. **Fire & Emergency Agent**: Assesses life-safety threats, heatstroke triage surges, and medical/shelter deficits.
  2. **Infrastructure Agent**: Evaluates water supply depletion, substation thermal degradation, and cooling load.
  3. **City Authority Coordinator Agent**: Consolidates specialist reports, ranks zones under the active strategy (`balanced_priority`, `risk_priority`, `vulnerability_priority`, `population_priority`), and records measurable reasoning plus rejected alternatives.
- **Constrained Resource Allocator (`backend/app/allocation/allocator.py`)**: 3-pass deterministic allocator guaranteeing a 15% safety floor for HIGH/CRITICAL zones while strictly respecting finite city inventory.
- **Evaluation Engine (`backend/app/evaluation/metrics.py`)**: Computes Risk Reduction %, Population Protected, Emergency Effectiveness, Resource Utilization, Unmet Demand %, Estimated Cost (INR Lakhs), and Jain's Fairness Index.

## 3. Running Locally (Isolated Ports)
1. **Start Backend (`http://localhost:8001`)**:
   `$env:PYTHONPATH = "backend"; .\backend\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8001 --reload`
2. **Start Frontend (`http://localhost:5174`)**:
   `cd frontend; npm run dev`
3. **Full-Stack Docker Compose**:
   `docker compose up --build -d`
