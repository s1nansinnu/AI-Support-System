# AI Support Ticket Analytics & Anomaly Detection System

An end-to-end, production-grade AI system designed for the **DOTMappers AI Engineer Technical Assessment**. 

The system ingests customer support ticket data into a relational SQLite database, translates natural language inquiries into safe SQL queries using **Google Gemini**, synthesizes executive-level business answers, detects operational SLA breaches and statistical outliers, and exposes functionality through a decoupled **FastAPI REST API** and an interactive **Streamlit Dashboard**.

---

## 1. Architecture Overview

The system is architected with strict separation between backend business logic and frontend presentation:

```
                                  ┌────────────────────────┐
                                  │   Streamlit Web App    │
                                  │ (http://localhost:8501)│
                                  └───────────┬────────────┘
                                              │ HTTP Requests
                                              ▼
┌────────────────────────┐        ┌────────────────────────┐
│ support_tickets.csv    │───────▶│     FastAPI Backend    │
│ (Automated Ingestion)  │        │ (http://localhost:8000)│
└────────────────────────┘        └─────┬────────────┬─────┘
                                        │            │
             ┌──────────────────────────┘            └──────────────────────────┐
             ▼                                                                  ▼
┌────────────────────────┐                                          ┌────────────────────────┐
│   Gemini LLM Service   │                                          │ Anomaly Detector Engine│
│ 1. Text-to-SQL Prompt  │                                          │ 1. SLA Breach (>12/24h)│
│ 2. SQL Safety Gate     │                                          │ 2. Category IQR Delays │
│ 3. Answer Synthesis    │                                          │ 3. Response Lag Filter │
└────────────┬───────────┘                                          └───────────┬────────────┘
             │                                                                  │
             └──────────────────────────┐            ┌──────────────────────────┘
                                        ▼            ▼
                                  ┌────────────────────────┐
                                  │    SQLite Database     │
                                  │      (tickets.db)      │
                                  └────────────────────────┘
```

### Directory Layout

```
d:/end to end Ai system/
├── backend/                        # FastAPI REST API
│   ├── app/
│   │   ├── config.py               # Environment configuration & path resolver
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic request/response schemas
│   │   ├── database/
│   │   │   ├── connection.py       # SQLite connection, DDL, SQL safety gate
│   │   │   └── queries.py          # Schema context metadata for Gemini prompts
│   │   ├── services/
│   │   │   ├── ingestion.py        # CSV validation, type coercion, and DB load
│   │   │   ├── gemini.py           # Gemini Text-to-SQL & NL synthesis service
│   │   │   └── anomaly.py          # Hybrid rule-based & IQR anomaly detector
│   │   └── routers/
│   │       ├── health.py           # GET /health
│   │       ├── query.py            # POST /api/query
│   │       ├── anomalies.py        # GET /api/anomalies
│   │       └── ingest.py           # POST /api/ingest
│   ├── main.py                     # FastAPI application entry point & lifespan
│   ├── requirements.txt            # Backend dependencies
│   ├── .env                        # Local environment variables (git-ignored)
│   └── .env.example                # Template for environment variables
├── frontend/                       # Streamlit Web UI
│   ├── app/
│   │   ├── config.py               # Frontend settings & constants
│   │   ├── api_client.py           # Centralized backend HTTP client with caching
│   │   ├── pages/
│   │   │   ├── query_page.py       # 💬 Natural language query interface
│   │   │   ├── anomaly_page.py     # 🚨 Anomaly monitor & filters
│   │   │   └── overview_page.py    # 📊 Dataset overview & KPI dashboard
│   │   └── components/
│   │       ├── sidebar.py          # Status indicators & API links
│   │       └── charts.py           # Reusable data visualization components
│   ├── main.py                     # Streamlit application entry point
│   └── requirements.txt            # Frontend dependencies
├── data/
│   └── support_tickets.csv         # 500-row customer support ticket dataset
├── run.py                          # Unified launcher (FastAPI + Streamlit)
├── .gitignore                      # Git ignore file (excludes secrets, venv, db)
└── README.md                       # Complete documentation
```

### Architectural Highlights
- **Decoupled Architecture**: Backend and Frontend are isolated into standalone packages. Frontend communicates with Backend exclusively over REST via `api_client.py`.
- **Two-Stage Text-to-SQL Pipeline**: 
  1. **Translation**: The user's question is converted into read-only SQLite SQL based on strict schema metadata.
  2. **Execution & Synthesis**: The query is validated by an AST/regex safety filter, executed against SQLite, and results are passed back to Gemini for executive summarization.
- **SQL Safety Gate**: Strictly allows read-only `SELECT` / `WITH` statements. Prohibits mutations (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, semicolons).
- **Hybrid Anomaly Detection**: Combines operational business rules (unresolved High/Critical tickets exceeding SLA) with statistical outlier detection (Interquartile Range - IQR by category for resolution times, and team-wide for response times).
- **Graceful Error Handling**: If `GEMINI_API_KEY` is not provided, the system does not crash; it informs the caller with clear guidance on setting the key.

---

## 2. Models & Tools Used

| Category | Tool / Library | Version / Details | Purpose |
|---|---|---|---|
| **LLM Engine** | Google Gemini API | `gemini-2.5-flash` (or `gemini-1.5-flash`) | Natural language understanding, SQL query generation, and business answer synthesis |
| **LLM SDK** | `google-genai` / `google-generativeai` | `>=0.1.0` / `>=0.8.0` | Official client library connecting to Gemini API |
| **Backend Framework** | FastAPI | `>=0.110.0` | High-performance asynchronous REST API with auto-generated OpenAPI documentation |
| **ASGI Server** | Uvicorn | `>=0.28.0` | Lightning-fast ASGI production server |
| **Frontend Framework** | Streamlit | `>=1.32.0` | Modern, interactive analytical web interface |
| **Database** | SQLite3 | Built-in standard library | Zero-configuration, ACID-compliant relational analytical store |
| **Data Processing** | Pandas & NumPy | `>=2.2.0` / `>=1.26.0` | CSV ingestion, data type validation, statistical IQR anomaly calculation |
| **Data Validation** | Pydantic v2 | `>=2.6.0` | Schema validation and serialization for API contracts |

---

## 3. Setup Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Google Gemini API Key ([Get a free key here](https://aistudio.google.com/))

### Step 1: Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd "end to end Ai system"
```

### Step 2: Create & Activate Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell):
.venv\Scripts\activate
# If PowerShell script execution is restricted, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate on Linux/macOS:
# source .venv/bin/activate
```

### Step 3: Install Dependencies
Install dependencies for both backend and frontend:
```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### Step 4: Configure Environment Variables
Edit `backend/.env` (or copy from `backend/.env.example`) and add your Gemini API key:
```ini
GEMINI_API_KEY=AIzaSyYourActualApiKeyHere
GEMINI_MODEL=gemini-2.5-flash
DB_PATH=../tickets.db
CSV_PATH=../data/support_tickets.csv
API_HOST=127.0.0.1
API_PORT=8000
```

### Step 5: Start the System with a Single Command
From the project root directory, run:
```bash
python run.py
```
This single command automatically launches both services:
- **Streamlit Web UI**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

*(Optional: Running Services Individually)*
- **Backend only**:
  ```bash
  cd backend
  python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Frontend only**:
  ```bash
  cd frontend
  python -m streamlit run main.py --server.port 8501
  ```

---

## 4. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check, database status, ticket counts, and Gemini readiness. |
| `POST` | `/api/query` | Natural language question endpoint; translates to SQL, executes, and synthesizes answer. |
| `GET` | `/api/anomalies` | Detects SLA breaches and statistical resolution/response outliers. |
| `POST` | `/api/ingest` | Uploads a new CSV file and ingests it into SQLite. |

### Sample API Request:
```bash
curl -X POST "http://127.0.0.1:8000/api/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "How many tickets are currently open?"}'
```

### Sample API Response:
```json
{
  "question": "How many tickets are currently open?",
  "sql_query": "SELECT COUNT(*) AS open_tickets FROM support_tickets WHERE status = 'Open';",
  "columns": ["open_tickets"],
  "results": [{"open_tickets": 111}],
  "row_count": 1,
  "answer": "There are currently 111 tickets with an open status.",
  "status": "success"
}
```

---

## 5. Example Queries with Outputs

The system reliably handles all 5 assessment benchmark queries:

### Query 1: Open Ticket Count
- **User Question**: *"How many tickets are currently open?"*
- **Generated SQL**:
  ```sql
  SELECT COUNT(*) AS open_tickets 
  FROM support_tickets 
  WHERE status = 'Open';
  ```
- **Execution Result**: `[{"open_tickets": 111}]`
- **Gemini Synthesis**: 
  > *"There are currently 111 open tickets in the system awaiting resolution."*

---

### Query 2: Top Performing Agent
- **User Question**: *"Which agent resolved the most tickets this month?"*
- **Generated SQL**:
  ```sql
  SELECT agent_id, COUNT(*) AS resolved_count 
  FROM support_tickets 
  WHERE status = 'Resolved' 
  GROUP BY agent_id 
  ORDER BY resolved_count DESC 
  LIMIT 1;
  ```
- **Execution Result**: `[{"agent_id": "AGT-04", "resolved_count": 31}]`
- **Gemini Synthesis**: 
  > *"Agent AGT-04 resolved the highest number of tickets, completing 31 resolutions."*

---

### Query 3: Critical SLA Violations (>12h)
- **User Question**: *"Show me all Critical tickets not resolved within 12 hours."*
- **Generated SQL**:
  ```sql
  SELECT ticket_id, category, priority, status, resp_time_hrs, resol_time_hrs, agent_id 
  FROM support_tickets 
  WHERE priority = 'Critical' 
    AND (resol_time_hrs > 12 OR status != 'Resolved') 
  LIMIT 500;
  ```
- **Execution Result**: 31 records violating the threshold.
- **Gemini Synthesis**: 
  > *"Found 31 Critical tickets that either took longer than 12 hours to resolve or remain unresolved beyond the 12-hour SLA window."*

---

### Query 4: Average Customer Rating by Category
- **User Question**: *"What is the average customer rating for Technical category tickets?"*
- **Generated SQL**:
  ```sql
  SELECT ROUND(AVG(cust_rating), 2) AS avg_rating 
  FROM support_tickets 
  WHERE category = 'Technical' 
    AND cust_rating IS NOT NULL;
  ```
- **Execution Result**: `[{"avg_rating": 3.78}]`
- **Gemini Synthesis**: 
  > *"The average customer satisfaction rating for Technical category tickets is 3.78 out of 5."*

---

### Query 5: Resolution Anomalies
- **User Question**: *"Are there any anomalies in resolution times this week?"*
- **Generated SQL / Anomaly Engine**:
  ```sql
  SELECT ticket_id, category, resol_time_hrs, agent_id 
  FROM support_tickets 
  WHERE status = 'Resolved' AND resol_time_hrs > 30.0 
  ORDER BY resol_time_hrs DESC 
  LIMIT 10;
  ```
- **Anomaly Detection Output**: 
  > *"Detected 102 anomalies across the dataset: 31 Critical SLA breaches (unresolved >12h/24h) and 71 High-severity resolution outliers exceeding statistical IQR thresholds."*

---

## 6. Anomaly Detection Pipeline

The anomaly detector (`backend/app/services/anomaly.py`) executes a hybrid detection methodology:

1. **Operational SLA Breaches**:
   - **Critical Tickets**: Tickets with `priority = 'Critical'` and `status != 'Resolved'` with age $> 12\text{ hours}$ (Flagged as **`CRITICAL`** severity).
   - **High/Critical Tickets**: Tickets with `priority IN ('High', 'Critical')` and `status != 'Resolved'` with age $> 24\text{ hours}$ (Flagged as **`CRITICAL`** or **`HIGH`** severity).
   - *Reference Date*: Calculated relative to the maximum ticket creation timestamp in the dataset to guarantee deterministic evaluations on historical records.
2. **Statistical Resolution Delays (IQR Method)**:
   - For resolved tickets, resolution times are grouped by `category`.
   - Interquartile Range is calculated: $\text{IQR} = Q_3 - Q_1$.
   - Any ticket with $\text{resol\_time\_hrs} > Q_3 + 1.5 \times \text{IQR}$ is flagged as **`HIGH`** severity.
3. **First-Response Time Lag**:
   - Computes global $Q_3 + 1.5 \times \text{IQR}$ across all tickets for `resp_time_hrs`.
   - Any ticket exceeding this threshold is flagged as **`MEDIUM`** severity.

---

## 7. Known Limitations & Scaling Strategy

- **Single-Turn Natural Language Context**: The current query engine is optimized for single-turn analytical questions. Multi-turn dialogue context ("...now filter those by Billing") can be supported by passing chat session memory in the request body.
- **SQLite Concurrency for High Write Volumes**: SQLite is ideal for read-heavy analytical queries on embedded datasets up to several gigabytes. For high-concurrency production deployments with thousands of concurrent ticket ingestions per second, the database layer can be pointed to PostgreSQL, Amazon Aurora, or Snowflake by updating the connection provider in `backend/app/database/connection.py`.
- **LLM Rate Limits & Quotas**: Free-tier Gemini API keys are subject to requests-per-minute (RPM) limits. For enterprise throughput, query caching (Redis) or batching should be placed in front of repetitive analytical requests.
- **Fixed SLA Thresholds**: Current SLA rules use 12h and 24h baselines as specified in the assessment. In enterprise use, SLA thresholds should be dynamically loaded from a client SLA configuration table based on customer tiers.
