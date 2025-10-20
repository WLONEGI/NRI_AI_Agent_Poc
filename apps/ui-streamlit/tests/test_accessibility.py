"""Automated accessibility audit using axe-core via Playwright."""
from __future__ import annotations

import pytest

try:  # optional dependency guard
    from playwright.sync_api import sync_playwright
    from axe_playwright_python.sync_playwright import Axe
except ImportError:  # pragma: no cover - tooling dependency not installed during unit tests
    pytest.skip("Playwright + axe-core tooling not installed", allow_module_level=True)


@pytest.mark.accessibility
@pytest.mark.parametrize("path", ["/"])
def test_streamlit_accessibility(path: str) -> None:
    """Run axe-core against the Streamlit UI for the given path."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"http://localhost:8501{path}", wait_until="load")
        axe = Axe(page)
        results = axe.run()
        axe.write_results(results, f"axe-report{path.replace('/', '_') or '_root'}.json")
        violations = results.get("violations", [])
        assert not violations, f"Accessibility violations detected: {violations}"
        browser.close()
