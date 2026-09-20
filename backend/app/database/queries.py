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
  resol_time_hrs  REAL   — Hours to resolution; NULL when ticket is unresolved (Open or Escalated)
  agent_id        TEXT   — Assigned agent (e.g. 'AGT-04')
  cust_rating     INTEGER— Post-resolution rating 1–5; NULL when unresolved
  issue_summary   TEXT   — Short description of the reported problem

Dataset Temporal Boundary:
  The dataset spans from January 2024 to March 2024 (latest ticket date: 2024-03-30).
  CRITICAL: When the user refers to "this month", "current month", or "latest month", use '2024-03' (e.g. strftime('%Y-%m', created_at) = '2024-03').
  Do NOT use DATE('now') or strftime('%Y-%m', 'now') because 'now' will evaluate to the current real-world year which has no tickets.

Domain Rules (always follow these when writing SQL):
  1. An *unresolved* ticket means status IN ('Open', 'Escalated') OR resol_time_hrs IS NULL.
  2. AVG(resol_time_hrs) and AVG(cust_rating) automatically ignore NULL values in SQLite.
  3. For date/time extraction use SQLite functions:
       strftime('%Y-%m', created_at)  → year-month (e.g. '2024-02')
       DATE(created_at)               → date part only (e.g. '2024-02-13')
  4. Always alias aggregated columns with a meaningful name (e.g. COUNT(*) AS total_open).
  5. Add LIMIT 500 unless the user explicitly asks for all records.

Few-Shot Query Examples:
  Q: "How many tickets are currently open?"
  SQL: SELECT COUNT(*) AS open_tickets FROM support_tickets WHERE status = 'Open';

  Q: "Which agent resolved the most tickets this month?"
  SQL: SELECT agent_id, COUNT(*) AS resolved_count FROM support_tickets WHERE status = 'Resolved' AND strftime('%Y-%m', created_at) = '2024-03' GROUP BY agent_id ORDER BY resolved_count DESC LIMIT 1;

  Q: "Show me all Critical tickets not resolved within 12 hours."
  SQL: SELECT ticket_id, category, priority, status, resp_time_hrs, resol_time_hrs, agent_id FROM support_tickets WHERE priority = 'Critical' AND (resol_time_hrs > 12.0 OR status != 'Resolved') LIMIT 500;

  Q: "What is the average customer rating for Technical category tickets?"
  SQL: SELECT ROUND(AVG(cust_rating), 2) AS avg_customer_rating FROM support_tickets WHERE category = 'Technical' AND cust_rating IS NOT NULL;
"""
