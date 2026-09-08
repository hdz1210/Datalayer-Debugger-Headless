"""
Autonomous DataLayer Audit Agent Runner (ADAA Runner).
Operates 100% headless with zero GUI.
Features configuration-driven execution (audit_config.json), interactive user onboarding,
and dynamic trigger execution without hardcoding.
Pure English codebase and reporting.
"""

import sys
import os
import json
import argparse
import urllib.parse
from typing import List, Dict, Any, Optional
from excel_exporter import DataLayerExcelExporter
from browser_engine import HeadlessDataLayerEngine


class AutonomousDataLayerAgent:
    """Orchestrates headless navigation, autonomous trigger discovery, and Excel export."""

    def __init__(self, target_domain: str = "Website", headless: bool = True):
        self.target_domain = target_domain
        self.headless = headless
        self.exporter = DataLayerExcelExporter(target_domain=target_domain)
        self.engine = HeadlessDataLayerEngine(headless=headless)

    def audit_passive(self, url: str, wait_buffer_sec: float = 3.0) -> None:
        """Audit passive events generated upon page loading (page_view, view_item, gtm.js)."""
        print(f"\n[*] Navigating to: {url}")
        session_info = self.engine.navigate(url, wait_buffer_sec=wait_buffer_sec)
        current_url = session_info.get("current_url", url)

        new_events = session_info.get("new_events", []) or session_info.get("initial_events", [])
        if new_events:
            for evt in new_events:
                payload = evt.get("payload", {})
                evt_name = payload.get("event", "initial_render")
                print(f"    [Captured] Event: '{evt_name}'")
                self.exporter.add_record(
                    link_trigger=current_url,
                    button_name="[PAGE_LOAD / INITIAL_RENDER]",
                    datalayer_payload=payload,
                    ga4_event=evt_name,
                    status="PASS - Passive event triggered on page load"
                )
        else:
            print("    [Notice] No dataLayer events detected on initial page load.")
            self.exporter.add_record(
                link_trigger=current_url,
                button_name="[PAGE_LOAD / INITIAL_RENDER]",
                datalayer_payload={},
                ga4_event="(None)",
                status="NOTICE - No dataLayer.push detected on page load"
            )

    def audit_triggers(
        self,
        url: str,
        mode: str = "auto",
        filter_keywords: Optional[List[str]] = None,
        max_triggers: int = 15,
        wait_buffer_ms: int = 1500
    ) -> None:
        """
        Dynamically discover interactables and execute triggers.
        Modes:
          - 'auto': Trigger all discoverable buttons/interactables up to max_triggers.
          - 'flow': Trigger only elements matching specified keywords or selectors.
        """
        print(f"\n[*] Starting interactive trigger audit on: {url}")
        session = self.engine.start(url)
        current_url = session.get("current_url", url)

        # 1. Record passive load events first
        for evt in session.get("initial_events", []):
            payload = evt.get("payload", {})
            self.exporter.add_record(
                link_trigger=current_url,
                button_name="[PAGE_LOAD / INITIAL_RENDER]",
                datalayer_payload=payload,
                ga4_event=payload.get("event", ""),
                status="PASS - Passive load event"
            )

        # 2. Extract interactables dynamically
        interactables = session.get("interactables", [])
        print(f"[*] Discovered {len(interactables)} interactable elements on the page.")

        # 3. Filter targets based on user mode
        targets = []
        if mode == "flow" and filter_keywords:
            keywords_lower = [k.lower().strip() for k in filter_keywords if k.strip()]
            for el in interactables:
                text = (el.get("text", "") or "").lower()
                sel = (el.get("selector", "") or "").lower()
                name_attr = (el.get("name", "") or "").lower()
                if any(kw in text or kw in sel or kw in name_attr for kw in keywords_lower):
                    targets.append(el)
        else:
            # Auto mode: select visible buttons, inputs, links with text
            targets = [el for el in interactables if el.get("text") and not el.get("text").startswith("[")]

        targets = targets[:max_triggers]
        print(f"[*] Selected {len(targets)} elements to trigger.\n")

        # 4. Execute triggers sequentially
        for idx, target in enumerate(targets, start=1):
            btn_name = target.get("text") or target.get("selector")
            selector = target.get("selector")
            print(f"[{idx}/{len(targets)}] Triggering: '{btn_name}' (Selector: {selector})")

            res = self.engine.execute_action(
                action="click",
                selector=selector,
                button_name=btn_name,
                wait_buffer_ms=wait_buffer_ms
            )

            link_trigger = res.get("link_trigger", current_url)
            captured = res.get("new_events", [])

            if captured:
                print(f"    [Captured] {len(captured)} new DataLayer event(s) fired!")
                for evt in captured:
                    payload = evt.get("payload", {})
                    evt_name = payload.get("event", "")
                    print(f"    -> Event Name: '{evt_name}'")
                    self.exporter.add_record(
                        link_trigger=link_trigger,
                        button_name=btn_name,
                        datalayer_payload=payload,
                        ga4_event=evt_name,
                        status="PASS - Event triggered by user action"
                    )
            else:
                print("    [Warning] Action performed but no dataLayer.push captured.")
                self.exporter.add_record(
                    link_trigger=link_trigger,
                    button_name=btn_name,
                    datalayer_payload={},
                    ga4_event="(None)",
                    status="WARNING - Click executed but no dataLayer event fired"
                )

    def close(self) -> None:
        """Close browser resources."""
        self.engine.close()

    def export(self, output_dir: str = ".", custom_filename: Optional[str] = None) -> str:
        """Export accumulated audit records to an Excel file."""
        return self.exporter.export(output_dir=output_dir, custom_filename=custom_filename)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file if it exists."""
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to read config file '{config_path}': {e}")
    return {}


def save_config(config_path: str, data: Dict[str, Any]) -> None:
    """Save current configuration to a JSON file."""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[*] Configuration saved to: {config_path}")
    except Exception as e:
        print(f"[Warning] Could not save config file: {e}")


def run_interactive_onboarding(config_file: str = "audit_config.json") -> None:
    """Interactive CLI onboarding wizard to guide users when no target URL is configured."""
    print("=================================================================")
    print("      AUTONOMOUS DATALAYER AUDIT AGENT (ADAA) - ONBOARDING       ")
    print("=================================================================")
    print("Welcome! ADAA is an autonomous, headless agent designed to audit")
    print("Google Analytics 4 & Google Tag Manager DataLayer implementations.")
    print("The final output will be a standardized Excel (.xlsx) report.\n")

    # Step 1: Target URL(s)
    while True:
        raw_urls = input("[1/4] Enter target website URL(s) [separate multiple with comma]: ").strip()
        if raw_urls:
            urls = [u.strip() for u in raw_urls.split(",") if u.strip()]
            if all(u.startswith("http://") or u.startswith("https://") for u in urls):
                break
        print(" [!] Please provide valid URL(s) starting with http:// or https://")

    # Determine domain name from first URL
    parsed_domain = urllib.parse.urlparse(urls[0]).netloc or "Website"

    # Step 2: Trigger Requirements / Audit Mode
    print("\n[2/4] Select Audit Trigger Mode:")
    print("  [1] Full Auto-Discovery Mode")
    print("      (Agent dynamically scans and clicks all interactable buttons)")
    print("  [2] Targeted / Flow Trigger Mode")
    print("      (Agent triggers buttons matching specific keywords, e.g. add-to-cart, buy, checkout)")
    print("  [3] Passive Page Load Audit Only")
    print("      (Agent audits page_view / view_item across URLs without clicking)")

    choice = input("Enter choice (1, 2, or 3) [Default: 1]: ").strip() or "1"
    
    mode = "auto"
    keywords = []
    if choice == "2":
        mode = "flow"
        raw_kw = input("Enter trigger keywords (comma-separated, e.g. 'cart, buy, select, checkout'): ").strip()
        if raw_kw:
            keywords = [k.strip() for k in raw_kw.split(",") if k.strip()]
        else:
            keywords = ["cart", "buy", "order", "checkout", "add"]
    elif choice == "3":
        mode = "passive"

    # Step 3: Maximum Triggers per page
    max_triggers = 10
    if mode != "passive":
        raw_max = input("\n[3/4] Enter maximum buttons to trigger per page [Default: 10]: ").strip()
        if raw_max.isdigit() and int(raw_max) > 0:
            max_triggers = int(raw_max)

    # Step 4: Output details
    custom_filename = input(f"\n[4/4] Enter Excel output filename [Press Enter for default]: ").strip() or None

    # Save to config file for future runs
    save_config(config_file, {
        "target_url": urls[0] if len(urls) == 1 else urls,
        "mode": mode,
        "keywords": keywords,
        "max_triggers": max_triggers,
        "output_filename": custom_filename or "",
        "headless": True
    })

    print("\n-----------------------------------------------------------------")
    print(f"[*] Configuration Summary:")
    print(f"    - URLs: {urls}")
    print(f"    - Mode: {mode.upper()}")
    if keywords:
        print(f"    - Target Keywords: {keywords}")
    if mode != "passive":
        print(f"    - Max Triggers: {max_triggers}")
    print("-----------------------------------------------------------------\n")

    # Execute Audit
    agent = AutonomousDataLayerAgent(target_domain=parsed_domain, headless=True)
    try:
        for u in urls:
            if mode == "passive":
                agent.audit_passive(u)
            else:
                agent.audit_triggers(u, mode=mode, filter_keywords=keywords, max_triggers=max_triggers)
    finally:
        agent.close()

    excel_file = agent.export(output_dir=".", custom_filename=custom_filename)
    print("\n=================================================================")
    print(f"[SUCCESS] DataLayer audit completed!")
    print(f"Excel report generated at: {excel_file}")
    print("=================================================================")


def main():
    """Main entrypoint supporting config files, CLI arguments, and interactive onboarding."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Autonomous DataLayer Audit Agent (Headless, No-UI)")
    parser.add_argument("--config", type=str, default="audit_config.json", help="Path to JSON configuration file (default: audit_config.json)")
    parser.add_argument("--url", type=str, default=None, help="Target website URL (overrides config)")
    parser.add_argument("--mode", choices=["auto", "flow", "passive"], default=None, help="Audit mode (auto, flow, passive)")
    parser.add_argument("--keywords", type=str, default=None, help="Comma-separated trigger keywords for flow mode")
    parser.add_argument("--max-triggers", type=int, default=None, help="Maximum triggers to execute per page")
    parser.add_argument("--output", type=str, default=None, help="Custom output filename for Excel report")
    parser.add_argument("--headless", action="store_true", default=None, help="Run browser in headless mode")

    args = parser.parse_args()

    # Load configuration file if present
    cfg = load_config(args.config)

    # Determine parameter values (CLI arguments take precedence over config file)
    target_url = args.url or cfg.get("target_url")
    mode = args.mode or cfg.get("mode", "auto")
    max_triggers = args.max_triggers if args.max_triggers is not None else cfg.get("max_triggers", 10)
    output_filename = args.output or cfg.get("output_filename") or None
    headless = args.headless if args.headless is not None else cfg.get("headless", True)

    if args.keywords is not None:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    else:
        keywords = cfg.get("keywords", ["cart", "buy", "order", "checkout", "add"])

    # If target URL is missing or empty, launch interactive onboarding wizard
    if not target_url:
        print(f"[*] Notice: No target URL configured in CLI or '{args.config}'.")
        print("[*] Launching interactive onboarding wizard...\n")
        run_interactive_onboarding(config_file=args.config)
        return

    # Normalize URLs into a list
    if isinstance(target_url, list):
        urls = target_url
    else:
        urls = [u.strip() for u in str(target_url).split(",") if u.strip()]

    parsed_domain = urllib.parse.urlparse(urls[0]).netloc or "Website"
    print(f"[*] Running audit with configuration (Domain: {parsed_domain}, Mode: {mode}, Headless: {headless})")

    agent = AutonomousDataLayerAgent(target_domain=parsed_domain, headless=headless)
    try:
        for u in urls:
            if mode == "passive":
                agent.audit_passive(u)
            else:
                agent.audit_triggers(
                    u,
                    mode=mode,
                    filter_keywords=keywords,
                    max_triggers=max_triggers
                )
    finally:
        agent.close()

    excel_file = agent.export(output_dir=".", custom_filename=output_filename)
    print(f"\n[OK] Excel audit report exported to: {excel_file}")


if __name__ == "__main__":
    main()
