"""
Test E2E per navigazione mobile (menu hamburger).
Verifica apertura, chiusura e comportamento del menu su viewport mobile.
"""
import pytest
from playwright.sync_api import Page, expect

from conftest import BASE_URL, VIEWPORTS


# Viewport mobili per test menu hamburger
MOBILE_VIEWPORTS = {
    "iphone_se": {"width": 375, "height": 667},
    "iphone_15_pro": {"width": 393, "height": 852},
    "iphone_15_pro_max": {"width": 430, "height": 932},
    "pixel_7": {"width": 412, "height": 915},
    "galaxy_s21": {"width": 360, "height": 800},
}


def dismiss_cookie_banner(page: Page):
    """Chiude il cookie banner se presente."""
    try:
        cookie_banner = page.locator("#cookie-banner")
        if cookie_banner.is_visible(timeout=1000):
            accept_btn = page.locator("#cookie-accept-btn")
            if accept_btn.is_visible(timeout=500):
                accept_btn.click()
                page.wait_for_timeout(300)
    except Exception:
        pass  # Banner non presente o già chiuso


class TestMobileMenuBasic:
    """Test base per menu hamburger mobile."""
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_hamburger_menu_opens(self, browser, device_name, viewport):
        """
        Verifica che il click sul menu hamburger apra l'overlay.
        Questo è il bug riportato su iPhone 15 Pro.
        """
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            # Menu hamburger deve essere visibile su mobile
            hamburger = page.locator("#mobile-toggle")
            expect(hamburger).to_be_visible()
            
            # Menu overlay inizialmente nascosto
            mobile_menu = page.locator("#mobile-menu")
            expect(mobile_menu).to_have_css("opacity", "0")
            expect(mobile_menu).to_have_css("pointer-events", "none")
            
            # Salva posizione scroll iniziale
            scroll_before = page.evaluate("window.scrollY")
            
            # Click su hamburger
            hamburger.click()
            page.wait_for_timeout(400)  # Attendi transizione
            
            # Menu deve essere visibile
            expect(mobile_menu).to_have_css("opacity", "1")
            expect(mobile_menu).to_have_css("pointer-events", "auto")
            
            # Scroll NON deve essere cambiato (bug fix verification)
            scroll_after = page.evaluate("window.scrollY")
            assert scroll_before == scroll_after, (
                f"Scroll cambiato dopo apertura menu! "
                f"Prima: {scroll_before}, Dopo: {scroll_after}"
            )
            
            # Body deve avere overflow hidden
            body_overflow = page.evaluate("document.body.style.overflow")
            assert body_overflow == "hidden", (
                f"Body overflow non bloccato: {body_overflow}"
            )
            
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_menu_links_visible_with_contrast(self, browser, device_name, viewport):
        """
        Verifica che i link del menu siano effettivamente visibili (contrasto colori).
        Bug rilevato: menu bianco su sfondo bianco = link invisibili.
        """
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            # Apri menu
            page.locator("#mobile-toggle").click()
            page.wait_for_timeout(400)
            
            mobile_menu = page.locator("#mobile-menu")
            expect(mobile_menu).to_have_css("opacity", "1")
            
            # Verifica che i link siano visibili e abbiano colore diverso dallo sfondo
            links = page.locator("#mobile-menu a")
            link_count = links.count()
            assert link_count >= 5, f"Trovati solo {link_count} link, attesi almeno 5"
            
            # Ottieni colore sfondo del menu
            menu_bg = page.evaluate("""
                () => {
                    const menu = document.getElementById('mobile-menu');
                    const style = getComputedStyle(menu);
                    return style.backgroundColor;
                }
            """)
            
            # Verifica che ogni link abbia un colore diverso dallo sfondo
            for i in range(link_count):
                link = links.nth(i)
                expect(link).to_be_visible()
                
                link_color = link.evaluate("""
                    el => getComputedStyle(el).color
                """)
                
                # Il colore del link NON deve essere uguale allo sfondo
                assert link_color != menu_bg, (
                    f"Link {i} ha stesso colore dello sfondo! "
                    f"Link: {link_color}, Sfondo: {menu_bg}"
                )
                
                # Verifica che il colore non sia bianco/quasi bianco
                # RGB bianco: rgb(255, 255, 255) o rgba(255, 255, 255, 1)
                assert "255, 255, 255" not in link_color or "rgba(255, 255, 255, 0)" in link_color, (
                    f"Link {i} è bianco su sfondo bianco! Color: {link_color}"
                )
            
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_hamburger_menu_closes_with_x_button(self, browser, device_name, viewport):
        """Verifica che il pulsante X chiuda il menu."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            # Apri menu
            page.locator("#mobile-toggle").click()
            page.wait_for_timeout(400)
            
            mobile_menu = page.locator("#mobile-menu")
            expect(mobile_menu).to_have_css("opacity", "1")
            
            # Pulsante X deve essere visibile
            close_button = page.locator("#mobile-close")
            expect(close_button).to_be_visible()
            
            # Chiudi menu
            close_button.click()
            page.wait_for_timeout(400)
            
            # Menu deve essere nascosto
            expect(mobile_menu).to_have_css("opacity", "0")
            
            # Body overflow ripristinato
            body_overflow = page.evaluate("document.body.style.overflow")
            assert body_overflow == "", f"Body overflow non ripristinato: {body_overflow}"
            
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_hamburger_menu_closes_with_escape(self, browser, device_name, viewport):
        """Verifica che Escape chiuda il menu (accessibilità)."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            # Apri menu
            page.locator("#mobile-toggle").click()
            page.wait_for_timeout(400)
            
            mobile_menu = page.locator("#mobile-menu")
            expect(mobile_menu).to_have_css("opacity", "1")
            
            # Premi Escape
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            
            # Menu deve essere nascosto
            expect(mobile_menu).to_have_css("opacity", "0")
            
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_menu_link_navigation(self, browser, device_name, viewport):
        """Verifica che i link del menu funzionino e chiudano il menu."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            # Chiudi cookie banner se presente (potrebbe bloccare i click)
            dismiss_cookie_banner(page)
            
            # Apri menu
            page.locator("#mobile-toggle").click()
            page.wait_for_timeout(400)
            
            mobile_menu = page.locator("#mobile-menu")
            expect(mobile_menu).to_have_css("opacity", "1")
            
            # Click su un link (Contatti)
            page.locator("#mobile-menu a[href='/contatti/']").click()
            page.wait_for_load_state("networkidle")
            
            # Dovremmo essere sulla pagina contatti
            assert "/contatti" in page.url, f"URL non corretto: {page.url}"
            
            # Menu dovrebbe essere chiuso dopo navigazione
            expect(mobile_menu).to_have_css("opacity", "0")
            
        finally:
            page.close()
            context.close()


class TestMobileMenuAccessibility:
    """Test accessibilità per menu mobile."""
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_aria_attributes_toggle(self, browser, device_name, viewport):
        """Verifica attributi ARIA corretti durante apertura/chiusura."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            hamburger = page.locator("#mobile-toggle")
            
            # Stato iniziale
            expect(hamburger).to_have_attribute("aria-expanded", "false")
            expect(hamburger).to_have_attribute("aria-label", "Apri menu di navigazione")
            
            # Dopo apertura
            hamburger.click()
            page.wait_for_timeout(400)
            
            expect(hamburger).to_have_attribute("aria-expanded", "true")
            expect(hamburger).to_have_attribute("aria-label", "Chiudi menu di navigazione")
            
            # Dopo chiusura
            page.locator("#mobile-close").click()
            page.wait_for_timeout(400)
            
            expect(hamburger).to_have_attribute("aria-expanded", "false")
            expect(hamburger).to_have_attribute("aria-label", "Apri menu di navigazione")
            
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_focus_management(self, browser, device_name, viewport):
        """Verifica gestione focus corretta (accessibilità tastiera)."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            # Apri menu
            page.locator("#mobile-toggle").click()
            page.wait_for_timeout(400)
            
            # Focus dovrebbe essere sul pulsante chiusura (non su un link)
            focused_id = page.evaluate("document.activeElement?.id")
            assert focused_id == "mobile-close", (
                f"Focus non sul pulsante chiusura: {focused_id}"
            )
            
            # Chiudi menu
            page.locator("#mobile-close").click()
            page.wait_for_timeout(400)
            
            # Focus dovrebbe tornare sul toggle
            focused_id = page.evaluate("document.activeElement?.id")
            assert focused_id == "mobile-toggle", (
                f"Focus non tornato sul toggle: {focused_id}"
            )
            
        finally:
            page.close()
            context.close()


class TestMobileMenuZIndex:
    """Test z-index e layering corretto."""
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_menu_overlay_covers_page(self, browser, device_name, viewport):
        """Verifica che il menu copra completamente la pagina."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            # Apri menu
            page.locator("#mobile-toggle").click()
            page.wait_for_timeout(400)
            
            mobile_menu = page.locator("#mobile-menu")
            
            # Verifica dimensioni overlay
            box = mobile_menu.bounding_box()
            assert box is not None, "Menu overlay non ha bounding box"
            
            # Deve coprire tutto il viewport
            assert box["x"] == 0, f"Menu non inizia da x=0: {box['x']}"
            assert box["y"] == 0, f"Menu non inizia da y=0: {box['y']}"
            assert box["width"] >= viewport["width"] - 1, (
                f"Menu non copre larghezza: {box['width']} vs {viewport['width']}"
            )
            assert box["height"] >= viewport["height"] - 1, (
                f"Menu non copre altezza: {box['height']} vs {viewport['height']}"
            )
            
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_menu_z_index_above_nav(self, browser, device_name, viewport):
        """Verifica che il menu abbia z-index superiore alla nav."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            # Apri menu
            page.locator("#mobile-toggle").click()
            page.wait_for_timeout(400)
            
            # Ottieni z-index
            nav_z = page.evaluate(
                "parseInt(getComputedStyle(document.getElementById('nav')).zIndex) || 0"
            )
            menu_z = page.evaluate(
                "parseInt(getComputedStyle(document.getElementById('mobile-menu')).zIndex) || 0"
            )
            
            assert menu_z > nav_z, (
                f"Menu z-index ({menu_z}) non superiore a nav ({nav_z})"
            )
            
        finally:
            page.close()
            context.close()


class TestMobileMenuNoJSErrors:
    """Test assenza errori JavaScript."""
    
    @pytest.mark.parametrize("device_name,viewport", MOBILE_VIEWPORTS.items())
    def test_no_js_errors_on_menu_interaction(self, browser, device_name, viewport):
        """Verifica assenza errori JS durante interazione con menu."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            # Interazioni multiple
            for _ in range(3):
                page.locator("#mobile-toggle").click()
                page.wait_for_timeout(300)
                page.locator("#mobile-close").click()
                page.wait_for_timeout(300)
            
            # Nessun errore JS
            assert len(js_errors) == 0, f"Errori JavaScript: {js_errors}"
            
        finally:
            page.close()
            context.close()


class TestDesktopMenuHidden:
    """Test che menu mobile sia nascosto su desktop."""
    
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("desktop_small", VIEWPORTS["desktop_small"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_hamburger_hidden_on_desktop(self, browser, viewport_name, viewport):
        """Verifica che hamburger sia nascosto su viewport desktop."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            
            hamburger = page.locator("#mobile-toggle")
            expect(hamburger).to_be_hidden()
            
        finally:
            page.close()
            context.close()
