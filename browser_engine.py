"""
Headless Browser Engine using Playwright.
Injects non-intrusive DataLayer interception proxy before page execution.
Operates 100% headless (Zero-UI) for autonomous AI Agent execution.
Features Smart Prioritization: prioritizes business tracking & CTA buttons ahead of UI utilities.
Supports general-purpose websites (E-commerce, Lead Gen, SaaS, Media, Banking, Blogs).
Pure English documentation and codebase.
"""

import time
import json
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


class HeadlessDataLayerEngine:
    """Manages stateful headless browser execution and non-intrusive DataLayer interception."""

    INIT_SCRIPT = """
    (() => {
        window.__capturedDataLayerEvents = [];
        const originalPush = Array.prototype.push;

        function hookArray(arr) {
            arr.push = function(...args) {
                for (const item of args) {
                    try {
                        window.__capturedDataLayerEvents.push({
                            timestamp: Date.now(),
                            payload: JSON.parse(JSON.stringify(item))
                        });
                    } catch (e) {
                        window.__capturedDataLayerEvents.push({
                            timestamp: Date.now(),
                            payload: item
                        });
                    }
                }
                return originalPush.apply(this, args);
            };
        }

        let _dl = window.dataLayer || [];
        hookArray(_dl);

        Object.defineProperty(window, 'dataLayer', {
            get: () => _dl,
            set: (val) => {
                _dl = val;
                if (Array.isArray(_dl)) {
                    hookArray(_dl);
                }
            },
            configurable: true
        });
    })();
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.last_read_index: int = 0

    def start(self, url: str, wait_buffer_sec: float = 2.5) -> Dict[str, Any]:
        """Launch headless browser session, inject proxy script, and navigate to target URL."""
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        self.context = self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        self.context.add_init_script(self.INIT_SCRIPT)
        self.page = self.context.new_page()

        self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(wait_buffer_sec)

        initial_events = self._get_new_events()
        interactables = self.get_interactables()

        return {
            "status": "READY",
            "current_url": self.page.url,
            "initial_events": initial_events,
            "interactables": interactables
        }

    def navigate(self, url: str, wait_buffer_sec: float = 2.5) -> Dict[str, Any]:
        """Navigate to a new URL within the active browser session."""
        if not self.page:
            return self.start(url, wait_buffer_sec)

        self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(wait_buffer_sec)
        new_events = self._get_new_events()
        return {
            "status": "NAVIGATED",
            "current_url": self.page.url,
            "new_events": new_events,
            "interactables": self.get_interactables()
        }

    def _get_new_events(self) -> List[Dict[str, Any]]:
        """Extract newly generated events since last check (Event Diff)."""
        if not self.page:
            return []
        try:
            all_events = self.page.evaluate("() => window.__capturedDataLayerEvents || []")
        except Exception:
            all_events = []

        new_events = all_events[self.last_read_index:]
        self.last_read_index = len(all_events)
        return new_events

    def get_all_captured_events(self) -> List[Dict[str, Any]]:
        """Retrieve all events captured in the entire session."""
        if not self.page:
            return []
        try:
            return self.page.evaluate("() => window.__capturedDataLayerEvents || []")
        except Exception:
            return []

    def get_interactables(self, limit: int = 60) -> List[Dict[str, Any]]:
        """
        Extract visible interactable DOM elements across all types of websites.
        Smart Prioritization:
          1. Business tracking elements (data-event, data-testid, data-track) -> Highest Priority.
          2. Meaningful action buttons/links with clear labels -> Medium-High Priority.
          3. General navigation & document links -> Medium Priority.
          4. UI utilities (Copy, Clear, color-dots, decorative icons) -> Deprioritized to prevent quota starvation.
        """
        if not self.page:
            return []

        js_extract = """
        () => {
            const elements = Array.from(document.querySelectorAll(
                'button, a, input[type="submit"], input[type="button"], [role="button"], select, [data-event], [data-testid]'
            ));

            const visibleElements = elements.filter(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && 
                       style.visibility !== 'hidden' && 
                       style.display !== 'none';
            });

            const items = visibleElements.map((el, idx) => {
                let text = (el.innerText || el.value || el.getAttribute('aria-label') || el.placeholder || '').trim();
                text = text.replace(/\\s+/g, ' ').substring(0, 60);

                const dataEvent = el.getAttribute('data-event');
                const dataTestId = el.getAttribute('data-testid');
                const id = el.id;
                const name = el.getAttribute('name');
                const tag = el.tagName.toLowerCase();
                const className = (el.className || '').toString().toLowerCase();
                const lowerText = text.toLowerCase();

                // Compute Smart Priority Score
                let priority = 50;
                if (dataEvent) priority += 100;
                if (dataTestId) priority += 60;
                if (text && text.length >= 3) priority += 25;

                // Deprioritize UI utilities and decorative dots so they do not exhaust trigger quotas
                let isUtility = false;
                if (lowerText === 'copy' || lowerText === 'clear' || 
                    className.includes('color-dot') || className.includes('log-btn') || 
                    className.includes('btn-icon') || id.includes('clear')) {
                    priority -= 40;
                    isUtility = true;
                }
                if (!text && !dataEvent && !dataTestId) {
                    priority -= 50;
                    isUtility = true;
                }

                // Compute Unique Selector
                let selector = '';
                if (id && !id.match(/^\\d/)) {
                    selector = `#${id}`;
                } else if (dataEvent) {
                    selector = `${tag}[data-event="${dataEvent}"]`;
                } else if (dataTestId) {
                    selector = `${tag}[data-testid="${dataTestId}"]`;
                } else if (name) {
                    selector = `${tag}[name="${name}"]`;
                } else if (text && text.length >= 2 && text.length <= 35 && !text.includes('\\n') && !text.includes('"')) {
                    selector = `${tag}:has-text("${text}")`;
                } else if (className) {
                    const firstClass = className.trim().split(/\\s+/)[0];
                    selector = firstClass ? `${tag}.${firstClass} >> nth=${idx}` : `${tag} >> nth=${idx}`;
                } else {
                    selector = `${tag} >> nth=${idx}`;
                }

                return {
                    index: idx,
                    tag: tag,
                    text: text || dataEvent || `[${tag}]`,
                    selector: selector,
                    id: id || '',
                    name: name || '',
                    data_event: dataEvent || '',
                    data_testid: dataTestId || '',
                    priority: priority,
                    is_utility: isUtility
                };
            });

            // Sort by priority descending: high-value tracking & CTAs first
            items.sort((a, b) => b.priority - a.priority);
            return items;
        }
        """
        try:
            return self.page.evaluate(js_extract)[:limit]
        except Exception:
            return []

    def execute_action(
        self,
        action: str,
        selector: str,
        button_name: str,
        value: str = "",
        wait_buffer_ms: int = 1500
    ) -> Dict[str, Any]:
        """Execute a DOM interaction (click, fill, select, scroll) and capture event diff."""
        if not self.page:
            return {"status": "NO_SESSION_ERROR", "new_events": []}

        current_url = self.page.url
        try:
            if action == "click":
                self.page.locator(selector).first.click(timeout=8000)
            elif action == "fill":
                self.page.locator(selector).first.fill(value, timeout=8000)
            elif action == "select":
                self.page.locator(selector).first.select_option(value, timeout=8000)
            elif action == "scroll":
                self.page.evaluate("window.scrollBy(0, 500)")
            elif action == "hover":
                self.page.locator(selector).first.hover(timeout=8000)
        except Exception as ex:
            return {
                "status": "ACTION_ERROR",
                "error": str(ex),
                "link_trigger": current_url,
                "button_name": button_name,
                "new_events": []
            }

        time.sleep(wait_buffer_ms / 1000.0)
        new_events = self._get_new_events()
        new_url = self.page.url

        return {
            "status": "SUCCESS",
            "link_trigger": current_url,
            "button_name": button_name,
            "new_events": new_events,
            "current_url": new_url,
            "interactables": self.get_interactables()
        }

    def close(self) -> None:
        """Close browser context, page, and clean up Playwright resources."""
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
