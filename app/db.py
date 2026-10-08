import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("FARMER_DB", "farmer.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS plots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop TEXT NOT NULL, area_acre REAL NOT NULL CHECK (area_acre > 0),
    sowing_date TEXT, note TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL, crop TEXT NOT NULL, category TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0), note TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL, crop TEXT NOT NULL,
    qty_quintal REAL NOT NULL CHECK (qty_quintal > 0),
    price_per_quintal REAL NOT NULL CHECK (price_per_quintal > 0),
    market TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS price_history (
    date TEXT NOT NULL, crop TEXT NOT NULL, state TEXT NOT NULL DEFAULT '',
    market TEXT NOT NULL, variety TEXT NOT NULL DEFAULT '',
    min_price REAL, max_price REAL, modal_price REAL NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (date, crop, state, market, variety, source)
);
CREATE TABLE IF NOT EXISTS farm (
    id INTEGER PRIMARY KEY CHECK (id = 1), district TEXT NOT NULL DEFAULT '',
    lat REAL, lon REAL, onboarded INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS farmers (
    id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, email TEXT, google_sub TEXT UNIQUE, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS otps (
    id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT NOT NULL, code_hash TEXT NOT NULL, channel TEXT NOT NULL,
    ip TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, expires INTEGER NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0, consumed INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_otp_phone ON otps (phone, created);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY, farmer_id INTEGER NOT NULL, created INTEGER NOT NULL, expires INTEGER NOT NULL, last_used INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS farmer_farm (
    farmer_id INTEGER PRIMARY KEY, district TEXT NOT NULL DEFAULT '', lat REAL, lon REAL, onboarded INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, crop TEXT NOT NULL, plot_id INTEGER,
    kind TEXT NOT NULL, task_key TEXT NOT NULL DEFAULT '', qty REAL, unit TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_act_crop ON activities (crop, date);
CREATE INDEX IF NOT EXISTS ix_price_crop_date ON price_history (crop, date);
CREATE INDEX IF NOT EXISTS ix_exp_crop ON expenses (crop, date);
CREATE INDEX IF NOT EXISTS ix_sales_crop ON sales (crop, date);
"""


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


# plots.sowing_date is the PLANTING date (sowing, or transplanting for transplanted crops)
PLOT_COLUMNS = {
    "season": "TEXT NOT NULL DEFAULT ''", "irrigation": "TEXT NOT NULL DEFAULT 'borewell'",
    "status": "TEXT NOT NULL DEFAULT 'active'", "harvested_on": "TEXT", "created_on": "TEXT",
    "soil_n": "REAL", "soil_p": "REAL", "soil_k": "REAL", "ph": "REAL",
}


OWNED_TABLES = ("plots", "expenses", "sales", "activities")  # rows that belong to one farmer


def init():
    with conn() as c:
        c.executescript(SCHEMA)
        for t in OWNED_TABLES:  # per-farmer data: older databases get the column, legacy rows stay NULL until claimed
            if "farmer_id" not in {r["name"] for r in c.execute(f"PRAGMA table_info({t})")}:
                c.execute(f"ALTER TABLE {t} ADD COLUMN farmer_id INTEGER")
            c.execute(f"CREATE INDEX IF NOT EXISTS ix_{t}_farmer ON {t} (farmer_id)")
        if "google_sub" not in {r["name"] for r in c.execute("PRAGMA table_info(farmers)")}:
            # phone-only table from v0.3: rebuild so phone may be empty (Google accounts) and email / google_sub exist
            c.executescript("""
                BEGIN;
                ALTER TABLE farmers RENAME TO farmers_old;
                CREATE TABLE farmers (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE, email TEXT, google_sub TEXT UNIQUE, created_at INTEGER NOT NULL);
                INSERT INTO farmers (id, phone, created_at) SELECT id, phone, created_at FROM farmers_old;
                DROP TABLE farmers_old;
                COMMIT;""")
        have = {r["name"] for r in c.execute("PRAGMA table_info(plots)")}
        for col, ddl in PLOT_COLUMNS.items():  # upgrade databases created by earlier versions
            if col not in have:
                c.execute(f"ALTER TABLE plots ADD COLUMN {col} {ddl}")
