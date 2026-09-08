# AI AGENT EXECUTION GUIDELINES (ADAA)

This document contains mandatory behavioral instructions for any AI Agent (Antigravity, Claude Code, Cursor, Copilot, etc.) interacting with this repository.

---

## ⛔ CRITICAL RULES FOR AI AGENTS

1. **DO NOT CREATE DUMMY TEST PAGES OR MOCK SCRIPTS**:
   - Never create local HTML mock pages (e.g. `test_page.html`) or dummy test scripts (e.g. `verify_test.py`).
   - This repository is designed to audit **live production / staging websites**, not mock pages.

2. **CHECK `audit_config.json` FIRST**:
   - Before doing anything, inspect `audit_config.json`.
   - If `target_url` contains a valid URL, execute directly using:
     ```bash
     python agent_runner.py --config audit_config.json
     ```

3. **PROMPT THE USER IMMEDIATELY IF NO TARGET IS SPECIFIED**:
   - If `audit_config.json` has an empty `target_url` (`""`) AND the user's prompt did not supply a website URL, **DO NOT explore the codebase or write exploratory tests**.
   - **STOP IMMEDIATELY AND ASK THE USER**:
     1. **Target URL**: Which website URL do you want to audit?
     2. **Audit Mode**:
        - `auto`: Crawl and click all discoverable buttons.
        - `flow`: Click buttons matching specific keywords (e.g., `cart, buy, checkout`).
        - `passive`: Only audit passive load events (`page_view`, `view_item`) across URLs.
     3. **Specific Keywords / Triggers**: (If flow mode is selected).
   - Once the user responds, update `audit_config.json` or run `agent_runner.py` with the corresponding CLI flags.

---

## 🛠️ CLI EXECUTION CHEATSHEET

```bash
# Run with config file
python agent_runner.py --config audit_config.json

# Run directly with CLI arguments
python agent_runner.py --url "https://example.com" --mode auto --max-triggers 10

# Run specific flow mode
python agent_runner.py --url "https://example.com/booking" --mode flow --keywords "cart, buy, checkout"

# Run passive page load audit
python agent_runner.py --url "https://example.com/product/1" --mode passive
```

---

## 📊 OUTPUT SPECIFICATION

All audit runs automatically export to a standardized Excel file (`.xlsx`) containing:
- `Index`
- `Link Trigger` (URL where action occurred)
- `Button Name` (Element label or selector)
- `GA4 Event`
- `DataLayer Payload` (Full 2-space indented JSON)
- `Status / Audit Notes`
