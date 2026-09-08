# Datalayer-debugger-Headless-

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
│  - Generates DataLayer_Audit_[Domain]_[Timestamp].xlsx │
│  - Standardized Columns & Monospace Code Formatting    │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

Ensure Python 3.9+ is installed:

```bash
git clone https://github.com/hdz1210/Datalayer-debugger-Headless-.git
cd Datalayer-debugger-Headless-
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 💻 Usage

### Mode A: Interactive Onboarding (Recommended)

Simply execute the script without any parameters. The agent will launch an interactive wizard:

```bash
python agent_runner.py
```

**Interactive Prompts:**
1. **Target URL(s)**: Enter single URL or comma-separated URLs.
2. **Audit Trigger Mode**:
   - `[1] Full Auto-Discovery Mode`: Automatically finds and clicks all discoverable interactable buttons.
   - `[2] Targeted / Flow Trigger Mode`: Filters and clicks buttons matching specific keywords (e.g., `add to cart`, `buy`, `checkout`).
   - `[3] Passive Page Load Audit Only`: Audits `page_view`, `view_item`, and initial tags without clicking.
3. **Maximum Triggers**: Maximum buttons to click per page.
4. **Excel Output Filename**: Custom filename or press Enter for default timestamped naming.

---

### Mode B: Non-Interactive CLI Flags

Ideal for scripting, scheduled jobs, or automated CI/CD:

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
| `--max-triggers` | int | `10` | Maximum button triggers per page |
| `--output` | string | *Auto* | Custom filename for Excel report |
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
