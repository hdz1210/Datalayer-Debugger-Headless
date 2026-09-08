# Datalayer Debugger Headless

> **Autonomous DataLayer Audit Agent (ADAA)** — A 100% headless, zero-UI AI Agent designed to autonomously audit Google Analytics 4 (GA4) and Google Tag Manager (GTM) DataLayer implementations across websites and export structured Excel reports.

---

## 🌟 Key Features

- **Zero-UI & Headless Execution**: Runs entirely in the background via Playwright with no graphical interface, optimized for autonomous AI Agents, CI/CD pipelines, and automated QA.
- **Non-Intrusive DataLayer Interception**: Injects a proxy before page initialization (`page.add_init_script`), capturing both `window.dataLayer.push(...)` calls and direct array assignments without interfering with website tracking scripts.
- **Accurate Event Diff Tracking**: Isolates events triggered exclusively by each specific action or click, preventing duplicates across multi-step funnels.
- **Interactive User Onboarding**: Automatically prompts the user when launched without arguments to determine target URLs, audit modes, keyword filters, and output preferences.
- **Zero Hardcoding**: Accepts dynamic URLs, selectors, keywords, and flow parameters via CLI flags or interactive prompts.
- **Standardized Excel Export (.xlsx)**: Generates formatted workbooks featuring:
  - `Index`: Sequential counter of trigger steps.
  - `Link Trigger`: Exact URL where the action occurred.
  - `Button Name`: Display label, button text, or CSS selector of the triggered element.
  - `GA4 Event`: Associated event name (`page_view`, `view_item`, `add_to_cart`, etc.).
  - `DataLayer Payload`: Full, unshortened JSON payload with 2-space indentation and text wrapping.
  - `Status / Audit Notes`: Automated evaluation tags (`PASS`, `WARNING`, `FAIL`).

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│               AI Agent Controller / CLI                │
│  - User Onboarding Wizard                              │
│  - Dynamic DOM Exploration & Trigger Decision Logic   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Headless Browser Engine (Playwright)       │
│  - Stateful context with add_init_script proxy         │
│  - Non-intrusive DataLayer interception                │
│  - Event Diff Tracker per interaction                  │
└──────────────────────────┬─────────────────────────────┘
                           │ (Recorded Trigger Events)
                           ▼
┌────────────────────────────────────────────────────────┐
│             Excel Output Engine (openpyxl)             │
│  - Generates single standardized Excel workbook        │
│  - Formatted columns, wrapping & code styling          │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

Ensure Python 3.9+ is installed:

```bash
git clone https://github.com/hdz1210/Datalayer-Debugger-Headless.git
cd Datalayer-Debugger-Headless
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 💻 Usage & Execution Modes

You can run the audit tool in three seamless ways:

### Mode 1: Configuration-Driven (Fastest & Recommended for AI Agents)

Edit the [`audit_config.json`](audit_config.json) file directly with your target URL and preferences:

```json
{
  "target_url": "https://example.com/booking",
  "mode": "flow",
  "keywords": ["cart", "buy", "checkout", "add"],
  "max_triggers": 10,
  "output_filename": "My_Booking_Audit.xlsx",
  "headless": true
}
```

Then simply execute:
```bash
python agent_runner.py
# Or tell your AI Agent: "Run audit using config"
```
The agent reads `audit_config.json` immediately and completes the audit in seconds without guessing or running exploratory mock tests.

---

### Mode 2: Interactive Onboarding Wizard

If `target_url` in `audit_config.json` is left blank (`""`) and no CLI flags are passed, running:

```bash
python agent_runner.py
```
will automatically launch an interactive terminal wizard prompting for:
1. Target website URL(s)
2. Trigger Mode (`[1] Auto-Discovery`, `[2] Flow Keywords`, `[3] Passive Page Load`)
3. Target trigger keywords (if Flow mode)
4. Max buttons to trigger
5. Output Excel filename

*Note: Your answers will automatically be saved to `audit_config.json` for future runs.*

---

### Mode 3: Non-Interactive CLI Arguments (For CI/CD & Automation)

```bash
# Full auto-discovery audit
python agent_runner.py --url https://example.com/product/1 --mode auto --max-triggers 10

# Flow / Keyword-based audit
python agent_runner.py --url https://example.com/booking --mode flow --keywords "cart, buy, checkout" --max-triggers 5

# Passive page load audit across product pages
python agent_runner.py --url https://example.com/item/123 --mode passive --output Product_Audit.xlsx
```

#### CLI Options Reference

| Argument | Type | Default | Description |
|---|---|---|---|
| `--url` | string | *None* | Target website URL to audit |
| `--mode` | string | `auto` | Audit mode: `auto`, `flow`, or `passive` |
| `--keywords` | string | `""` | Comma-separated button keywords for `flow` mode |
| `--max-triggers` | int | `0` | Max button triggers per page (**0 for UNLIMITED - audits ALL buttons**) |
| `--output` | string | `audit_result.xlsx` | Output filename for Excel report (auto-appends `.xlsx`) |
| `--headless` | flag | `True` | Runs Chromium in headless mode |

---

## 📊 Excel Output Structure (.xlsx)

The generated Excel workbook includes the following standardized English headers:

| Column | Header Name | Alignment | Details |
|:---:|---|:---:|---|
| **A** | **Index** | Center | Sequential step number |
| **B** | **Link Trigger** | Left | The active URL at the time the action/event was triggered |
| **C** | **Button Name** | Left | Target element text, label, or selector (e.g., `Add to Cart`) |
| **D** | **GA4 Event** | Center | Triggered event name (e.g., `view_item`, `add_to_cart`) |
| **E** | **DataLayer Payload** | Left | Complete formatted JSON object captured from `dataLayer.push` |
| **F** | **Status / Audit Notes** | Left | Automated evaluation note (`PASS`, `WARNING`, etc.) |

---

## 📁 Repository Structure

```
├── agent_runner.py         # Main AI Agent orchestrator with interactive onboarding
├── browser_engine.py       # Headless Playwright engine with non-intrusive DataLayer hook
├── excel_exporter.py       # Professional openpyxl exporter with pure English schema
├── requirements.txt        # Python dependency manifest
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

---

## 📄 License

MIT License. Designed for automated Analytics QA and DataLayer validation.
