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


def init():
    with conn() as c:
        c.executescript(SCHEMA)
