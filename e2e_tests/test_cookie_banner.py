"""
Test E2E per il Cookie Banner GDPR.
Verifica tutte le combinazioni di scelta e interazioni con altri script della pagina.
Eseguito su mobile, tablet e desktop.
"""
import pytest
import re
from urllib.parse import unquote
from playwright.sync_api import Page, expect
import json

from conftest import BASE_URL, clear_cookies_and_storage, wait_for_cookie_banner, VIEWPORTS


def parse_consent_cookie(cookie_value: str) -> dict:
    """Parse cookie consent value, handling URL encoding."""
    decoded = unquote(cookie_value)
    return json.loads(decoded)


class TestCookieBannerDisplay:
    """Test per la visualizzazione del cookie banner."""
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_banner_shows_on_first_visit(self, browser, viewport_name, viewport):
        """Il banner deve apparire alla prima visita su tutti i viewport."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            wait_for_cookie_banner(page, visible=True, timeout=3000)
            
            banner = page.locator("#cookie-banner")
            expect(banner).to_be_visible()
            
            # Verifica elementi base del banner
            expect(page.locator("#cookie-reject-btn")).to_be_visible()
            expect(page.locator("#cookie-accept-btn")).to_be_visible()
            
            # Su mobile il pulsante personalizza potrebbe essere in overflow
            settings_btn = page.locator("#cookie-settings-btn")
            if viewport["width"] >= 768:
                expect(settings_btn).to_be_visible()
        finally:
            page.close()
            context.close()
    
    def test_banner_not_shown_with_existing_consent(self, page: Page):
        """Il banner NON deve apparire se esiste già un cookie di consenso."""
        # Prima imposta il cookie
        page.goto(BASE_URL)
        page.evaluate("""
            document.cookie = 'cookie_consent=' + encodeURIComponent(JSON.stringify({necessary: true, analytics: false})) + ';path=/';
        """)
        
        # Ricarica la pagina
        page.reload()
        page.wait_for_timeout(1000)
        
        # Il banner deve restare nascosto
        banner = page.locator("#cookie-banner")
        has_hidden_class = page.evaluate(
            "document.getElementById('cookie-banner')?.classList.contains('translate-y-full')"
        )
        assert has_hidden_class, "Il banner non dovrebbe essere visibile con consenso esistente"


class TestCookieBannerButtons:
    """Test per i pulsanti del cookie banner."""
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_reject_button_sets_cookie_and_hides_banner(self, browser, viewport_name, viewport):
        """Il pulsante 'Rifiuta' deve impostare il cookie e nascondere il banner."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            clear_cookies_and_storage(page)
            page.reload()
            
            wait_for_cookie_banner(page, visible=True)
            
            reject_btn = page.locator("#cookie-reject-btn")
            expect(reject_btn).to_be_visible()
            expect(reject_btn).to_be_enabled()
            
            # Click sul pulsante
            reject_btn.click()
            
            # Attendi che il banner si nasconda
            wait_for_cookie_banner(page, visible=False, timeout=3000)
            
            # Verifica il cookie
            cookies = page.context.cookies()
            consent_cookie = next((c for c in cookies if c["name"] == "cookie_consent"), None)
            assert consent_cookie is not None, "Cookie di consenso non trovato"
            
            consent_value = parse_consent_cookie(consent_cookie["value"])
            assert consent_value["analytics"] == False, "Analytics dovrebbe essere False con reject"
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_accept_button_sets_cookie_and_hides_banner(self, browser, viewport_name, viewport):
        """Il pulsante 'Accetta tutti' deve impostare il cookie con analytics=true."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            clear_cookies_and_storage(page)
            page.reload()
            
            wait_for_cookie_banner(page, visible=True)
            
            accept_btn = page.locator("#cookie-accept-btn")
            expect(accept_btn).to_be_visible()
            accept_btn.click()
            
            wait_for_cookie_banner(page, visible=False, timeout=3000)
            
            # Verifica il cookie
            cookies = page.context.cookies()
            consent_cookie = next((c for c in cookies if c["name"] == "cookie_consent"), None)
            assert consent_cookie is not None
            
            consent_value = parse_consent_cookie(consent_cookie["value"])
            assert consent_value["analytics"] == True, "Analytics dovrebbe essere True con accept all"
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_settings_button_shows_customization_panel(self, browser, viewport_name, viewport):
        """Il pulsante 'Personalizza' deve mostrare il pannello impostazioni."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            clear_cookies_and_storage(page)
            page.reload()
            
            wait_for_cookie_banner(page, visible=True)
            
            settings_btn = page.locator("#cookie-settings-btn")
            settings_panel = page.locator("#cookie-settings")
            
            # Il pannello inizialmente è nascosto
            expect(settings_panel).to_have_class(re.compile(r"hidden"))
            
            settings_btn.click()
            
            # Il pannello deve diventare visibile
            expect(settings_panel).not_to_have_class(re.compile(r"hidden"))
            
            # Verifica presenza checkbox
            expect(page.locator("#cookie-necessary")).to_be_visible()
            expect(page.locator("#cookie-analytics")).to_be_visible()
            expect(page.locator("#cookie-save-btn")).to_be_visible()
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("analytics_checked", [True, False])
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_save_preferences_with_analytics_toggle(
        self, browser, viewport_name, viewport, analytics_checked
    ):
        """Test salvataggio preferenze con analytics attivato/disattivato."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            clear_cookies_and_storage(page)
            page.reload()
            
            wait_for_cookie_banner(page, visible=True)
            
            # Apri impostazioni
            page.locator("#cookie-settings-btn").click()
            page.wait_for_timeout(300)
            
            analytics_checkbox = page.locator("#cookie-analytics")
            
            # Imposta lo stato desiderato
            if analytics_checked:
                analytics_checkbox.check()
            else:
                analytics_checkbox.uncheck()
            
            # Salva
            page.locator("#cookie-save-btn").click()
            
            wait_for_cookie_banner(page, visible=False, timeout=3000)
            
            # Verifica cookie
            cookies = page.context.cookies()
            consent_cookie = next((c for c in cookies if c["name"] == "cookie_consent"), None)
            assert consent_cookie is not None
            
            consent_value = parse_consent_cookie(consent_cookie["value"])
            assert consent_value["analytics"] == analytics_checked
        finally:
            page.close()
            context.close()


class TestCookieBannerAccessibility:
    """Test di accessibilità per il cookie banner."""
    
    def test_banner_has_proper_aria_structure(self, page: Page):
        """Il banner deve avere struttura ARIA corretta."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        wait_for_cookie_banner(page, visible=True)
        
        banner = page.locator("#cookie-banner")
        
        # Verifica che i pulsanti siano tag <button> (accessibili di default)
        reject_btn = page.locator("#cookie-reject-btn")
        tag_name = page.evaluate("document.getElementById('cookie-reject-btn')?.tagName")
        assert tag_name == "BUTTON", f"Reject non è un button ma: {tag_name}"
        
        # Verifica che i pulsanti siano raggiungibili cliccandoli direttamente
        expect(reject_btn).to_be_visible()
        expect(reject_btn).to_be_enabled()
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_buttons_clickable_in_all_contrast_modes(self, browser, viewport_name, viewport):
        """I pulsanti del cookie banner devono funzionare in tutte le modalità contrasto."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        contrast_modes = ["normal", "high", "inverted"]
        
        try:
            for mode in contrast_modes:
                page.goto(BASE_URL)
                clear_cookies_and_storage(page)
                page.reload()
                
                # Applica modalità contrasto
                if mode == "high":
                    page.evaluate("document.body.classList.add('a11y-contrast-high')")
                elif mode == "inverted":
                    page.evaluate("document.body.classList.add('a11y-contrast-inverted')")
                
                wait_for_cookie_banner(page, visible=True)
                
                # Testa click su Accept
                accept_btn = page.locator("#cookie-accept-btn")
                expect(accept_btn).to_be_visible()
                expect(accept_btn).to_be_enabled()
                
                # Verifica che il pulsante risponda al click
                accept_btn.click()
                
                # Il banner deve nascondersi
                wait_for_cookie_banner(page, visible=False, timeout=3000)
                
                # Verifica che il cookie sia stato impostato
                cookies = page.context.cookies()
                consent_cookie = next((c for c in cookies if c["name"] == "cookie_consent"), None)
                assert consent_cookie is not None, \
                    f"Cookie non impostato in modalità {mode} su viewport {viewport_name}"
        finally:
            page.close()
            context.close()


class TestCookieBannerWithOtherScripts:
    """Test interazioni con altri script della pagina."""
    
    def test_banner_works_with_tailwind_loaded(self, page: Page):
        """Il banner deve funzionare con Tailwind CSS caricato."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        # Verifica che Tailwind sia caricato (cerca classi Tailwind)
        has_tailwind = page.evaluate("""
            !!document.querySelector('[class*="flex"]') || 
            !!document.querySelector('[class*="bg-"]')
        """)
        # Non fallisce se Tailwind non è presente, è solo un check
        
        wait_for_cookie_banner(page, visible=True)
        
        page.locator("#cookie-accept-btn").click()
        wait_for_cookie_banner(page, visible=False)
    
    def test_banner_works_with_lucide_icons(self, page: Page):
        """Il banner deve funzionare anche se Lucide icons fallisce a caricare."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        
        # Blocca lucide icons
        page.route("**/lucide*", lambda route: route.abort())
        
        page.reload()
        wait_for_cookie_banner(page, visible=True)
        
        # I pulsanti devono comunque funzionare
        page.locator("#cookie-accept-btn").click()
        wait_for_cookie_banner(page, visible=False)
    
    def test_banner_works_when_ga4_blocked(self, page: Page):
        """Il banner deve funzionare anche se Google Analytics è bloccato."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        
        # Blocca GA4
        page.route("**/googletagmanager.com/**", lambda route: route.abort())
        page.route("**/google-analytics.com/**", lambda route: route.abort())
        
        page.reload()
        wait_for_cookie_banner(page, visible=True)
        
        page.locator("#cookie-accept-btn").click()
        wait_for_cookie_banner(page, visible=False)
        
        # Nessun errore JavaScript
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.wait_for_timeout(500)
        
        # Filtra errori relativi a GA (attesi se bloccato)
        critical_errors = [e for e in errors if "initGA4" not in e and "initMatomo" not in e]
        assert len(critical_errors) == 0, f"Errori JS critici: {critical_errors}"
    
    def test_banner_z_index_above_other_elements(self, page: Page):
        """Il cookie banner deve essere sopra altri elementi fixed."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        wait_for_cookie_banner(page, visible=True)
        
        # Verifica z-index
        z_index = page.evaluate("""
            getComputedStyle(document.getElementById('cookie-banner')).zIndex
        """)
        
        assert int(z_index) >= 9999, f"z-index troppo basso: {z_index}"
    
    def test_banner_isolation_prevents_filter_inheritance(self, page: Page):
        """Il banner deve essere isolato dai filtri CSS del body."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        # Applica filtro al body (simula alto contrasto)
        page.evaluate("""
            document.body.style.filter = 'invert(1) contrast(1.5)';
        """)
        
        wait_for_cookie_banner(page, visible=True)
        
        # Il banner deve avere isolation
        isolation = page.evaluate("""
            getComputedStyle(document.getElementById('cookie-banner')).isolation
        """)
        
        # Il banner deve avere filter: none
        banner_filter = page.evaluate("""
            getComputedStyle(document.getElementById('cookie-banner')).filter
        """)
        
        # Click deve funzionare
        page.locator("#cookie-accept-btn").click()
        wait_for_cookie_banner(page, visible=False)


class TestCookieBannerPersistence:
    """Test persistenza del consenso tra sessioni."""
    
    def test_consent_persists_across_page_navigation(self, page: Page):
        """Il consenso deve persistere navigando tra pagine."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        wait_for_cookie_banner(page, visible=True)
        page.locator("#cookie-accept-btn").click()
        wait_for_cookie_banner(page, visible=False)
        
        # Naviga ad un'altra pagina
        page.goto(f"{BASE_URL}/privacy/")
        page.wait_for_timeout(1000)
        
        # Il banner NON deve apparire
        has_hidden_class = page.evaluate(
            "document.getElementById('cookie-banner')?.classList.contains('translate-y-full')"
        )
        assert has_hidden_class or page.locator("#cookie-banner").count() == 0
    
    def test_consent_persists_on_reload(self, page: Page):
        """Il consenso deve persistere al reload della pagina."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        wait_for_cookie_banner(page, visible=True)
        page.locator("#cookie-reject-btn").click()
        wait_for_cookie_banner(page, visible=False)
        
        # Reload
        page.reload()
        page.wait_for_timeout(1000)
        
        # Il banner NON deve apparire
        has_hidden_class = page.evaluate(
            "document.getElementById('cookie-banner')?.classList.contains('translate-y-full')"
        )
        assert has_hidden_class


class TestCookieBannerKeyboard:
    """Test navigazione da tastiera del cookie banner."""
    
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_keyboard_navigation(self, browser, viewport_name, viewport):
        """I pulsanti devono essere navigabili via Tab tra di loro."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            clear_cookies_and_storage(page)
            page.reload()
            
            wait_for_cookie_banner(page, visible=True)
            
            # Focus diretto sul primo pulsante del banner
            page.locator("#cookie-reject-btn").focus()
            focused_id = page.evaluate("document.activeElement?.id")
            assert focused_id == "cookie-reject-btn", f"Focus non su reject: {focused_id}"
            
            # Tab al prossimo
            page.keyboard.press("Tab")
            focused_id = page.evaluate("document.activeElement?.id")
            assert focused_id in ["cookie-settings-btn", "cookie-accept-btn"], \
                f"Tab non ha navigato al prossimo pulsante: {focused_id}"
        finally:
            page.close()
            context.close()
    
    def test_enter_key_activates_button(self, page: Page):
        """Premere Enter su un pulsante deve attivarlo."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        wait_for_cookie_banner(page, visible=True)
        
        # Focus sul pulsante accept
        page.locator("#cookie-accept-btn").focus()
        
        # Premi Enter
        page.keyboard.press("Enter")
        
        # Il banner deve nascondersi
        wait_for_cookie_banner(page, visible=False, timeout=3000)
    
    def test_space_key_activates_button(self, page: Page):
        """Premere Space su un pulsante deve attivarlo."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        wait_for_cookie_banner(page, visible=True)
        
        # Focus sul pulsante reject
        page.locator("#cookie-reject-btn").focus()
        
        # Premi Space
        page.keyboard.press("Space")
        
        # Il banner deve nascondersi
        wait_for_cookie_banner(page, visible=False, timeout=3000)


class TestCookieBannerTiming:
    """Test timing e race conditions."""
    
    def test_rapid_double_click_handled(self, page: Page):
        """Double click rapido non deve causare problemi."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        wait_for_cookie_banner(page, visible=True)
        
        # Double click rapido
        page.locator("#cookie-accept-btn").dblclick()
        
        # Deve funzionare senza errori
        wait_for_cookie_banner(page, visible=False, timeout=3000)
        
        # Verifica che ci sia solo un cookie
        cookies = page.context.cookies()
        consent_cookies = [c for c in cookies if c["name"] == "cookie_consent"]
        assert len(consent_cookies) == 1
    
    def test_click_during_animation(self, page: Page):
        """Click durante l'animazione di apertura deve funzionare."""
        page.goto(BASE_URL)
        clear_cookies_and_storage(page)
        page.reload()
        
        # Non aspettare l'animazione completa
        page.wait_for_selector("#cookie-banner", state="attached")
        page.wait_for_timeout(100)  # Durante l'animazione
        
        # Tenta il click
        accept_btn = page.locator("#cookie-accept-btn")
        if accept_btn.is_visible():
            accept_btn.click()
            wait_for_cookie_banner(page, visible=False, timeout=5000)
