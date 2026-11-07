"""SQLite schema and connection helpers used by the ingestion pipeline."""
import sqlite3
from pathlib import Path
DDL='''CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY,started_at TEXT NOT NULL,ended_at TEXT,status TEXT,pages INTEGER,received INTEGER,loaded INTEGER,rejected INTEGER,duplicates INTEGER,error TEXT);
CREATE TABLE IF NOT EXISTS raw_responses(id INTEGER PRIMARY KEY,run_id TEXT,page INTEGER,fetched_at TEXT,status INTEGER,body TEXT);
CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY,customer_id TEXT,amount REAL,amount_minor INTEGER,currency TEXT,status TEXT,event_time TEXT,updated_at TEXT,source_file TEXT,run_id TEXT,ingested_at TEXT);
CREATE TABLE IF NOT EXISTS rejects(id INTEGER PRIMARY KEY,run_id TEXT,source_file TEXT,event_id TEXT,reason TEXT,raw_record TEXT,rejected_at TEXT);
CREATE TABLE IF NOT EXISTS checkpoints(source TEXT PRIMARY KEY,last_updated_at TEXT);
CREATE INDEX IF NOT EXISTS idx_events_customer ON events(customer_id);'''
def connect(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path);conn.row_factory=sqlite3.Row;conn.executescript(DDL)
    return conn
