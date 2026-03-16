# ⚖️ Forseti — LLM-Powered E2E Testing Service

> **Forseti** (ฟอร์เซตี) — เทพแห่งความยุติธรรมในตำนานนอร์ส ผู้ตัดสินข้อพิพาทและชี้ถูก-ผิด

**Forseti** is a self-hosted E2E testing service that uses LLM (Gemini / self-hosted) to interpret natural language test scripts and execute them via Playwright browser automation.

## ✨ Features

- 📝 **Natural Language Test Scripts** — Write tests in YAML using Thai or English
- 🤖 **LLM-Powered Execution** — Gemini translates test steps to browser actions
- 🌐 **Playwright Browser Engine** — Reliable cross-browser automation
- 📊 **Rich Reporting** — HTML reports with pass/fail %, SIT/UAT tracking
- 🐙 **GitHub Integration** — Auto-create issues on test failures
- 📸 **Screenshot Capture** — Evidence for every test step

## 🚀 Quick Start

```bash
# Install
pip install -e ".[dev]"
playwright install chromium

# Run tests
forseti run examples/test_scripts/login_test.yaml

# Validate script syntax
forseti validate examples/test_scripts/login_test.yaml

# Generate report from results
forseti report results/latest.json
```

## 📝 Test Script Format (YAML)

```yaml
name: "Login Test Suite"
base_url: "https://myapp.example.com"
phase: "SIT"  # SIT or UAT

scenarios:
  - name: "Successful Login"
    steps:
      - action: "เปิดหน้า login"
      - action: "กรอก username ว่า admin"
      - action: "กรอก password ว่า pass123"
      - action: "กดปุ่ม Login"
    expected: "เห็นหน้า Dashboard พร้อมข้อความ Welcome"

  - name: "Invalid Password"
    steps:
      - action: "เปิดหน้า login"
      - action: "กรอก username ว่า admin"
      - action: "กรอก password ว่า wrongpass"
      - action: "กดปุ่ม Login"
    expected: "เห็นข้อความ error 'Invalid credentials'"
```

## ⚙️ Configuration

Set environment variables or use `forseti.yaml`:

```bash
export GEMINI_API_KEY="your-api-key"
export GITHUB_TOKEN="your-github-token"
export GITHUB_REPO="owner/repo"
```

## 📁 Project Structure

```
forseti/
├── src/forseti/
│   ├── cli.py          # CLI entry point
│   ├── config.py       # Configuration
│   ├── models.py       # Data models
│   ├── parser.py       # YAML test script parser
│   ├── agent/
│   │   ├── llm.py      # LLM client (Gemini + self-hosted)
│   │   └── executor.py # NL → Playwright action translator
│   ├── browser/
│   │   └── engine.py   # Playwright browser engine
│   └── reporter/
│       ├── collector.py    # Result aggregation
│       ├── html_report.py  # HTML report generator
│       └── github_issue.py # GitHub issue integration
├── examples/
│   └── test_scripts/
├── templates/
│   └── report.html
└── tests/
```

## 📜 License

MIT
