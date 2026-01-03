"""
Configurazione Pytest per test E2E con Playwright.
Test accessibilità, cookie banner e interazioni su multiple viewport.
"""
import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

# Viewport standard per test responsive
VIEWPORTS = {
    "mobile_portrait": {"width": 375, "height": 667},      # iPhone SE
    "mobile_landscape": {"width": 667, "height": 375},     # iPhone landscape
    "tablet_portrait": {"width": 768, "height": 1024},     # iPad portrait
    "tablet_landscape": {"width": 1024, "height": 768},    # iPad landscape
    "desktop_small": {"width": 1280, "height": 800},       # Laptop
    "desktop_large": {"width": 1920, "height": 1080},      # Full HD
}

# URL base del sito (locale o Docker)
BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def browser():
    """Browser condiviso per tutta la sessione di test."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser):
    """Contesto browser con cookie puliti per ogni test."""
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext):
    """Pagina pulita per ogni test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(params=list(VIEWPORTS.keys()))
def responsive_page(browser: Browser, request):
    """
    Fixture parametrizzata per test su tutti i viewport.
    Ogni test verrà eseguito su mobile, tablet e desktop.
    """
    viewport_name = request.param
    viewport = VIEWPORTS[viewport_name]
    
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    page.viewport_name = viewport_name  # Per logging/debug
    
    yield page
    
    page.close()
    context.close()


@pytest.fixture
def mobile_page(browser: Browser):
    """Pagina configurata per viewport mobile con touch support."""
    context = browser.new_context(
        viewport=VIEWPORTS["mobile_portrait"],
        has_touch=True
    )
    page = context.new_page()
    yield page
    page.close()
    context.close()


@pytest.fixture
def tablet_page(browser: Browser):
    """Pagina configurata per viewport tablet."""
    context = browser.new_context(viewport=VIEWPORTS["tablet_portrait"])
    page = context.new_page()
    yield page
    page.close()
    context.close()


@pytest.fixture
def desktop_page(browser: Browser):
    """Pagina configurata per viewport desktop."""
    context = browser.new_context(viewport=VIEWPORTS["desktop_large"])
    page = context.new_page()
    yield page
    page.close()
    context.close()


def clear_cookies_and_storage(page: Page):
    """Helper per pulire cookie e localStorage."""
    page.evaluate("localStorage.clear()")
    page.context.clear_cookies()


def wait_for_cookie_banner(page: Page, visible: bool = True, timeout: int = 5000):
    """
    Attende che il cookie banner sia visibile o nascosto.
    Il banner usa translate-y-full per nascondersi.
    """
    banner = page.locator("#cookie-banner")
    if visible:
        # Attendi che il banner sia visibile (senza translate-y-full)
        banner.wait_for(state="visible", timeout=timeout)
        # Verifica che non abbia la classe di nascondimento
        page.wait_for_function(
            "!document.getElementById('cookie-banner').classList.contains('translate-y-full')",
            timeout=timeout
        )
    else:
        # Attendi che abbia la classe translate-y-full (nascosto)
        page.wait_for_function(
            "document.getElementById('cookie-banner').classList.contains('translate-y-full')",
            timeout=timeout
        )
