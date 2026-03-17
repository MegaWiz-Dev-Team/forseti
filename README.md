# ⚖️ Forseti — LLM-Powered E2E Testing Service

> **Forseti** (ฟอร์เซที) — Norse god of justice. An automated E2E testing service for Cloud Super Hero, built with Google ADK multi-agent architecture.

[![Tests](https://img.shields.io/badge/unit_tests-71%2F71-brightgreen)]()
[![E2E](https://img.shields.io/badge/E2E-26%2F26_(100%25)-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![ISO](https://img.shields.io/badge/ISO-29110-orange)]()

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone
git clone https://github.com/MegaWiz-Dev-Team/forseti.git
cd forseti

# Create virtualenv
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Run Unit Tests

```bash
python -m pytest tests/ -v
# ✅ 71/71 passed
```

### 3. Run E2E Tests (requires CSH dev server)

```bash
# Terminal 1: Start Cloud Super Hero dev server
cd /path/to/cloud-super-hero
GCP_PROJECT=cloud-super-hero-dev python server.py

# Terminal 2: Run Forseti E2E
cd /path/to/forseti
python run_e2e.py
```

**Output:**
```
⚖️ Forseti — Starting E2E Test Run
   Loaded 26 scenarios from YAML
   Authenticating as paripol@megawiz.co...
   ✅ Admin authenticated
   [1/26] TC_E2E_01 — Student Email Check (Existing)...
   ✅ pass (144ms)
   ...
   ✅ 26/26 passed (100%) | ❌ 0 failed | ⏱️ 9418ms
```

---

## 📁 Project Structure

```
forseti/
├── src/forseti/
│   ├── agents/
│   │   ├── api_agent.py          # ADK API test agent (7 tools)
│   │   ├── reporter_agent.py     # Report generation (DB + ISO + GitHub)
│   │   └── orchestrator.py       # Main E2E pipeline
│   ├── tools/
│   │   ├── http_tools.py         # async HTTP (GET/POST/PUT)
│   │   ├── assert_tools.py       # Status + JSON assertions
│   │   └── auth_tools.py         # Admin login + OTP dev mode
│   ├── db/
│   │   └── results_db.py         # SQLite storage
│   ├── reporter/
│   │   └── iso_report.py         # ISO SI-04 report generator
│   ├── models.py                 # Pydantic data models
│   ├── parser.py                 # YAML script parser
│   └── config.py                 # Settings
├── tests/                        # 71 TDD tests
├── examples/test_scripts/
│   └── cloud_super_hero_e2e.yaml # 26 API test scenarios
├── docs/iso29110/                # ISO 29110 documentation
├── reports/                      # Auto-generated ISO reports
├── forseti_results.db            # SQLite test results
└── run_e2e.py                    # E2E runner script
```

---

## ⚙️ Architecture

```
ForsetiOrchestrator.run_all(yaml_path)
  │
  ├── 1. Load YAML → 26 structured scenarios
  ├── 2. Admin Login → OTP dev-mode auto-verify
  ├── 3. Run scenarios (sequential HTTP)
  │     ├── GET/POST/PUT with auth headers
  │     └── Compare status code vs expected
  │
  └── 4. ReporterAgent.report()
        ├── save_to_db()       → forseti_results.db (SQLite)
        ├── generate_iso()     → reports/SI-04_SIT_*.md
        ├── generate_summary() → console output
        └── build_github_issue() → only if failures

Model: gemini-3.1-flash-lite-preview (ADK)
```

---

## 📊 Test Results

### Unit Tests: 71/71 PASS

| Sprint | Module | Tests |
|--------|--------|:-----:|
| SP1 | models, parser, config, collector | 34 |
| SP2 | http_tools, assert_tools, auth_tools, api_agent, iso_report, results_db | 27 |
| SP3 | reporter_agent, orchestrator | 10 |

### E2E Tests: 26/26 PASS (Run #5)

| Category | Tests | Pass Rate |
|----------|:-----:|:---------:|
| Student API | 8 | 100% |
| Admin Batch | 3 | 100% |
| Program API | 3 | 100% |
| Email Dry Run | 4 | 100% |
| Grading | 1 | 100% |
| Quiz | 1 | 100% |
| Feedback | 2 | 100% |
| Public Registration | 1 | 100% |
| Security (negative) | 2 | 100% |
| Email Reset | 1 | 100% |

---

## 📝 YAML Test Script Format

```yaml
scenarios:
  - name: "TC_E2E_01 — Student Email Check"
    method: POST
    path: "/api/student/check-email"
    body:
      email: "test@example.com"
    expected_status: 200
    needs_auth: false
    tags: [registration, student]
```

---

## 🗄️ SQLite Database

Results are stored in `forseti_results.db`:

```sql
-- View all runs
SELECT * FROM runs ORDER BY id DESC;

-- View trend
SELECT id, pass_rate, total, passed, failed FROM runs ORDER BY id DESC;

-- View failed scenarios for a run
SELECT * FROM scenarios WHERE run_id = 5 AND status = 'fail';
```

---

## 📋 ISO 29110 Documentation

| Document | Description |
|----------|-------------|
| `PM-01_Project_Plan.md` | Project plan with sprint overview |
| `PM-02_SP0X_Status.md` | Sprint status reports |
| `SI-01_Requirements.md` | Software requirements (SR-01 to SR-17) |
| `SI-04_SP0X_TestScript.md` | TDD test scripts per sprint |
| `TRD_Technical_Design.md` | Technical reference design |

---

## 🔒 Safety

- **⛔ Production blocked**: Refuses to run against `cloud-super-hero` (production)
- **Dev only**: Targets `cloud-super-hero-dev` exclusively
- **Dry run**: Email tests use `dryRun: true` — no real emails sent
- **Safe emails**: Mock students use `@test.invalid` domain

---

## 📅 Sprint Roadmap

| Sprint | Status | Focus |
|--------|:------:|-------|
| SP1 | ✅ | Foundation (models, parser, CLI) |
| SP2 | ✅ | ADK multi-agent + API tools + SQLite |
| SP3 | ✅ | Reporter + Orchestrator + E2E 100% |
| SP4 | 📋 | UI Automation (Playwright) |

---

*Built with ❤️ by MegaWiz Dev Team*
