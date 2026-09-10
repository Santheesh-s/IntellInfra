# Campus Spatial Decision Support System — Setup Guide

## Project Structure
```
campus-dss/
├── requirements.txt
├── data/                       ← your 6 validated CSVs
│   ├── hardware_inventory.csv
│   ├── os_requirements.csv
│   ├── software_requirements.csv
│   ├── software_cache.csv
│   ├── campus_spatial_data.csv
│   └── nlp_query_dataset_10000.csv
├── backend/
│   ├── database.py             ← DB connection
│   ├── models.py                ← SQLAlchemy table definitions
│   ├── load_data.py            ← loads CSVs into PostgreSQL
│   └── main.py                  ← FastAPI app + endpoints
└── notebooks/                  ← for NLP/MCDM/XAI experimentation (Phase 4-7)
```

## Step 1 — Install PostgreSQL + PostGIS

**Windows/Mac:** install via [postgresql.org](https://www.postgresql.org/download/) — PostGIS is included as an optional component in the installer (Stack Builder).

**Linux (Ubuntu/Debian):**
```bash
sudo apt install postgresql postgresql-contrib postgis
```

Then create the database:
```bash
sudo -u postgres createdb campus_dss
```

## Step 2 — Set up Python environment

```bash
cd campus-dss
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3 — Configure database connection

Create a `.env` file in `backend/`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/campus_dss
```

## Step 4 — Load your datasets

```bash
cd backend
python load_data.py
```

You should see output confirming all 6 datasets loaded (36 locations, 500 assets, 66 OS requirements, 72 software requirements, 50 cache entries, 10,000 NLP queries).

## Step 5 — Run the API

```bash
uvicorn main:app --reload
```

Visit **http://localhost:8000/docs** — this gives you an interactive Swagger UI to test every endpoint without writing any frontend code yet.

## Try These Endpoints First

- `GET /locations` — see all 36 labs on the map data
- `GET /assets?block=Block C` — all machines in Block C
- `GET /assets/{asset_id}/os-compatibility?os_id=win11` — compatibility check for one machine
- `GET /software/{software_id}/compatible-assets` — which machines can run a given software (Tier 1/2)

## What's Next (Phase 4 onward)

1. **NLP intent classifier** — train on `nlp_queries` table (10,000 labeled rows is more than enough)
2. **MCDM/TOPSIS ranking** — replace the simple rule-based `/os-compatibility` check with full multi-OS ranking across all 66 OS entries
3. **SHAP explanations** — add feature-contribution breakdowns to every score
4. **Leaflet.js frontend** — visualize `/locations` and `/assets` on an actual campus map
