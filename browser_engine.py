"""
Headless Browser Engine using Playwright.
Injects non-intrusive DataLayer interception proxy before page execution.
Operates 100% headless (Zero-UI) for autonomous AI Agent execution.
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

    def get_interactables(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Extract visible interactable DOM elements (buttons, links, inputs)."""
        if not self.page:
            return []

        js_extract = """
        () => {
            const elements = Array.from(document.querySelectorAll(
                'button, a, input[type="submit"], input[type="button"], [role="button"], select'
            ));
            return elements
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && 
                           style.visibility !== 'hidden' && 
                           style.display !== 'none';
                })
                .slice(0, 50)
                .map((el, idx) => {
                    let text = (el.innerText || el.value || el.getAttribute('aria-label') || el.placeholder || '').trim();
                    text = text.replace(/\\s+/g, ' ').substring(0, 60);
                    let selector = '';
                    if (el.id) {
                        selector = `#${el.id}`;
                    } else if (el.name) {
                        selector = `${el.tagName.toLowerCase()}[name="${el.name}"]`;
                    } else if (el.className && typeof el.className === 'string') {
                        const firstClass = el.className.trim().split(/\\s+/)[0];
                        selector = firstClass ? `.${firstClass}` : el.tagName.toLowerCase();
                    } else {
                        selector = el.tagName.toLowerCase();
                    }
                    return {
                        index: idx,
                        tag: el.tagName.toLowerCase(),
                        text: text || `[${el.tagName.toLowerCase()}]`,
                        selector: selector,
                        id: el.id || '',
                        name: el.getAttribute('name') || ''
                    };
                });
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
                self.page.click(selector, timeout=8000)
            elif action == "fill":
                self.page.fill(selector, value, timeout=8000)
            elif action == "select":
                self.page.select_option(selector, value, timeout=8000)
            elif action == "scroll":
                self.page.evaluate("window.scrollBy(0, 500)")
            elif action == "hover":
                self.page.hover(selector, timeout=8000)
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
