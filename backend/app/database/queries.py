"""Static SQL schema context injected into every Gemini prompt."""

TABLE_SCHEMA_CONTEXT = """
Table Name: support_tickets

Columns:
  ticket_id       TEXT   — Unique ticket identifier (e.g. 'TKT-001')
  created_at      TEXT   — Creation timestamp, format 'YYYY-MM-DD HH:MM'
  category        TEXT   — One of: 'Billing', 'Technical', 'General'
  priority        TEXT   — One of: 'Low', 'Medium', 'High', 'Critical'
  status          TEXT   — One of: 'Open', 'Resolved', 'Escalated'
  resp_time_hrs   REAL   — Hours from creation to first agent response
  resol_time_hrs  REAL   — Hours to resolution; NULL when ticket is unresolved
  agent_id        TEXT   — Assigned agent (e.g. 'AGT-04')
  cust_rating     INTEGER— Post-resolution rating 1–5; NULL when unresolved
  issue_summary   TEXT   — Short description of the reported problem

Domain Rules (always follow these when writing SQL):
  1. An *unresolved* ticket means status IN ('Open','Escalated')
     OR resol_time_hrs IS NULL.
  2. AVG() automatically ignores NULLs — no extra filtering needed for averages.
  3. For date/time extraction use SQLite functions:
       strftime('%Y-%m', created_at)  → year-month
       DATE(created_at)               → date part only
  4. Always alias aggregated columns with a meaningful name.
  5. Never return more than 1000 rows without a LIMIT clause.
"""
