# Amazon Growth Dashboard — SQL Edition (Streamlit + SQLite)

This version uses a **real SQL backend** (SQLite). One click to **seed** the DB with sample SKU data. Toggle between **SQLite DB** and **CSV upload** in the sidebar.

## 0) Install Python 3.11 (if missing)
- macOS: download the **Universal2** installer from python.org → install → reopen Terminal.

## 1) Create & activate virtual env
```bash
cd amazon_dashboard_sql
python3.11 -m venv .venv || python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

## 2) Install dependencies
```bash
pip install -r requirements.txt
```

## 3) Run the app
```bash
streamlit run app.py
```
- In the sidebar, leave **SQLite DB** mode selected (default path `amazon.db`).  
- Click **“Seed / Reseed DB with sample data”** once.  
- Explore filters, charts, breakdowns, and exports.

## 4) Switching to real company data
Replace seeding with your own table (same columns) or change the `SELECT` in `app.py` to your schema. For MySQL/Postgres, you can use SQLAlchemy/driver of choice and `pd.read_sql`.

### Expected columns
- `date` (YYYY-MM-DD), `sku_id`, `title`, `brand`, `category`
- `price`, `discount` (0–1), `sessions`, `clicks`, `add_to_cart`
- `units_ordered`, `units_returned`, `gmv`, `fulfillment`, `region`
- `take_rate` (0–1)

`gmv` and `take_rate` are optional (autocomputed / defaulted).

## 5) Deployment
- **Streamlit Community Cloud** or **Hugging Face Spaces**: Upload `app.py`, `requirements.txt`, and include `amazon.db` (or keep seeding enabled).

## Troubleshooting
- If NumPy import errors occur, ensure Python 3.11, then recreate the venv and reinstall requirements.
- If the DB is empty, click **Seed** again or check file path in the sidebar.
