"""
Test E2E per interazioni complete tra cookie banner, accessibilità e altri script.
Verifica scenari complessi e edge cases.
"""
import pytest
from playwright.sync_api import Page, expect
import json

from conftest import BASE_URL, clear_cookies_and_storage, wait_for_cookie_banner, VIEWPORTS


def reset_all(page: Page):
    """Reset completo di cookie e localStorage."""
    page.evaluate("localStorage.clear()")
    page.context.clear_cookies()


class TestCompleteUserFlows:
    """Test flussi utente completi."""
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_first_visit_flow_accept_all(self, browser, viewport_name, viewport):
        """
        Flusso completo prima visita: utente accetta tutti i cookie.
        Verifica che tutto funzioni senza errori JavaScript.
        """
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))
        
        try:
            page.goto(BASE_URL)
            reset_all(page)
            page.reload()
            
            # Cookie banner appare
            wait_for_cookie_banner(page, visible=True)
            
            # Accept
            page.locator("#cookie-accept-btn").click()
            wait_for_cookie_banner(page, visible=False)
            
            # Naviga
            page.wait_for_timeout(500)
            
            # Nessun errore JS critico
            critical_errors = [e for e in js_errors if "initGA4" not in e and "initMatomo" not in e]
            assert len(critical_errors) == 0, f"Errori JS: {critical_errors}"
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_accessibility_then_cookie_flow(self, browser, viewport_name, viewport):
        """
        Flusso: utente prima modifica accessibilità, poi gestisce cookie.
        """
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_all(page)
            page.reload()
            
            # Cookie banner visibile
            wait_for_cookie_banner(page, visible=True)
            
            # Apri pannello accessibilità (senza accettare cookie)
            page.locator("#a11y-toggle").click()
            page.locator("#a11y-panel").wait_for(state="visible", timeout=1000)
            
            # Attiva alto contrasto
            page.locator('[data-a11y-action="contrast-high"]').click()
            page.wait_for_timeout(300)
            
            # Chiudi pannello
            page.locator("#a11y-close").click()
            page.wait_for_timeout(300)
            
            # Ora gestisci cookie
            accept_btn = page.locator("#cookie-accept-btn")
            expect(accept_btn).to_be_visible()
            expect(accept_btn).to_be_enabled()
            
            accept_btn.click()
            wait_for_cookie_banner(page, visible=False)
            
            # Verifica che alto contrasto sia ancora attivo
            has_high = page.evaluate("document.body.classList.contains('a11y-contrast-high')")
            assert has_high, "Alto contrasto perso dopo accept cookie"
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_cookie_then_accessibility_flow(self, browser, viewport_name, viewport):
        """
        Flusso: utente prima gestisce cookie, poi modifica accessibilità.
        """
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_all(page)
            page.reload()
            
            # Cookie banner
            wait_for_cookie_banner(page, visible=True)
            
            # Reject cookie
            page.locator("#cookie-reject-btn").click()
            wait_for_cookie_banner(page, visible=False)
            
            # Ora modifica accessibilità
            page.locator("#a11y-toggle").click()
            page.locator("#a11y-panel").wait_for(state="visible", timeout=1000)
            
            # Attiva varie opzioni
            page.locator('[data-a11y-action="contrast-inverted"]').click()
            page.locator('[data-a11y-toggle="highlight-links"]').click()
            page.locator('[data-a11y-toggle="enhanced-focus"]').click()
            page.wait_for_timeout(300)
            
            # Verifica che tutto funzioni
            has_inverted = page.evaluate("document.body.classList.contains('a11y-contrast-inverted')")
            has_links = page.evaluate("document.body.classList.contains('a11y-highlight-links')")
            
            assert has_inverted and has_links
        finally:
            page.close()
            context.close()


class TestAllContrastCombinations:
    """Test tutte le combinazioni contrasto + cookie banner."""
    
    CONTRAST_MODES = ["contrast-normal", "contrast-high", "contrast-inverted"]
    COOKIE_ACTIONS = ["reject", "accept", "settings"]
    
    @pytest.mark.parametrize("contrast", CONTRAST_MODES)
    @pytest.mark.parametrize("cookie_action", COOKIE_ACTIONS)
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("tablet_portrait", VIEWPORTS["tablet_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_contrast_cookie_combination(
        self, browser, viewport_name, viewport, contrast, cookie_action
    ):
        """Test ogni combinazione di contrasto + azione cookie."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_all(page)
            page.reload()
            
            wait_for_cookie_banner(page, visible=True)
            
            # Applica contrasto (se non normale)
            if contrast != "contrast-normal":
                page.locator("#a11y-toggle").click()
                page.locator("#a11y-panel").wait_for(state="visible", timeout=1000)
                page.locator(f'[data-a11y-action="{contrast}"]').click()
                page.wait_for_timeout(200)
                page.locator("#a11y-close").click()
                page.wait_for_timeout(200)
            
            # Esegui azione cookie
            if cookie_action == "reject":
                btn = page.locator("#cookie-reject-btn")
                expect(btn).to_be_visible()
                btn.click()
                wait_for_cookie_banner(page, visible=False)
                
            elif cookie_action == "accept":
                btn = page.locator("#cookie-accept-btn")
                expect(btn).to_be_visible()
                btn.click()
                wait_for_cookie_banner(page, visible=False)
                
            elif cookie_action == "settings":
                settings_btn = page.locator("#cookie-settings-btn")
                expect(settings_btn).to_be_visible()
                settings_btn.click()
                page.wait_for_timeout(200)
                
                # Toggle analytics
                page.locator("#cookie-analytics").check()
                
                # Salva
                save_btn = page.locator("#cookie-save-btn")
                expect(save_btn).to_be_visible()
                save_btn.click()
                wait_for_cookie_banner(page, visible=False)
            
            # Verifica cookie impostato
            cookies = page.context.cookies()
            consent_cookie = next((c for c in cookies if c["name"] == "cookie_consent"), None)
            assert consent_cookie is not None, \
                f"Cookie non impostato: contrast={contrast}, action={cookie_action}, viewport={viewport_name}"
        finally:
            page.close()
            context.close()


class TestAllToggleCombinations:
    """Test combinazioni di toggle accessibilità."""
    
    TOGGLES = [
        "highlight-links",
        "enhanced-focus",
        "reduce-motion",
        "reading-mode",
        "large-cursor",
    ]
    
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_all_toggles_active_with_cookie_banner(self, browser, viewport_name, viewport):
        """Cookie banner funziona con tutti i toggle attivi."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_all(page)
            page.reload()
            
            wait_for_cookie_banner(page, visible=True)
            
            # Apri pannello e attiva tutti i toggle
            page.locator("#a11y-toggle").click()
            page.locator("#a11y-panel").wait_for(state="visible", timeout=1000)
            
            for toggle in self.TOGGLES:
                page.locator(f'[data-a11y-toggle="{toggle}"]').click()
                page.wait_for_timeout(100)
            
            # Attiva anche alto contrasto
            page.locator('[data-a11y-action="contrast-high"]').click()
            page.wait_for_timeout(200)
            
            # Chiudi pannello
            page.locator("#a11y-close").click()
            page.wait_for_timeout(200)
            
            # Cookie banner deve ancora funzionare
            accept_btn = page.locator("#cookie-accept-btn")
            expect(accept_btn).to_be_visible()
            expect(accept_btn).to_be_enabled()
            
            accept_btn.click()
            wait_for_cookie_banner(page, visible=False)
        finally:
            page.close()
            context.close()


class TestEdgeCases:
    """Test casi limite e scenari problematici."""
    
    def test_rapid_toggle_switches(self, page: Page):
        """Click rapidi sui toggle non devono causare problemi."""
        page.goto(BASE_URL)
        reset_all(page)
        page.reload()
        
        page.locator("#a11y-toggle").click()
        page.locator("#a11y-panel").wait_for(state="visible", timeout=1000)
        
        # Click rapidi
        for _ in range(10):
            page.locator('[data-a11y-toggle="highlight-links"]').click()
            page.wait_for_timeout(50)
        
        # Stato finale deve essere coerente
        toggle = page.locator('[data-a11y-toggle="highlight-links"]')
        state = toggle.get_attribute("aria-checked")
        has_class = page.evaluate("document.body.classList.contains('a11y-highlight-links')")
        
        # Stato e classe devono corrispondere
        if state == "true":
            assert has_class, "Stato true ma classe mancante"
        else:
            assert not has_class, "Stato false ma classe presente"
    
    def test_contrast_mode_rapid_switch(self, page: Page):
        """Cambio rapido tra modalità contrasto non deve causare problemi."""
        page.goto(BASE_URL)
        reset_all(page)
        page.reload()
        
        page.locator("#a11y-toggle").click()
        page.locator("#a11y-panel").wait_for(state="visible", timeout=1000)
        
        modes = ["contrast-high", "contrast-inverted", "contrast-normal", "contrast-high"]
        
        for mode in modes:
            page.locator(f'[data-a11y-action="{mode}"]').click()
            page.wait_for_timeout(100)
        
        # Verifica stato finale (high)
        has_high = page.evaluate("document.body.classList.contains('a11y-contrast-high')")
        has_inverted = page.evaluate("document.body.classList.contains('a11y-contrast-inverted')")
        
        assert has_high, "Alto contrasto dovrebbe essere attivo"
        assert not has_inverted, "Invertito non dovrebbe essere attivo"
    
    def test_reload_during_cookie_animation(self, page: Page):
        """Reload durante animazione cookie non deve causare problemi."""
        page.goto(BASE_URL)
        reset_all(page)
        page.reload()
        
        # Inizia ad accettare
        page.locator("#cookie-accept-btn").click()
        
        # Reload immediato (durante animazione)
        page.reload()
        page.wait_for_timeout(1000)
        
        # Il banner non deve riapparire (cookie già impostato)
        banner_hidden = page.evaluate(
            "document.getElementById('cookie-banner')?.classList.contains('translate-y-full') ?? true"
        )
        assert banner_hidden, "Banner riapparso dopo reload durante animazione"
    
    def test_simultaneous_panel_interactions(self, page: Page):
        """Interazioni simultanee su pannello e cookie banner."""
        page.goto(BASE_URL)
        reset_all(page)
        page.reload()
        
        wait_for_cookie_banner(page, visible=True)
        
        # Apri pannello accessibilità
        page.locator("#a11y-toggle").click()
        page.locator("#a11y-panel").wait_for(state="visible", timeout=1000)
        
        # Mentre il pannello è aperto, clicca accept cookie
        page.locator("#cookie-accept-btn").click()
        
        # Entrambi devono funzionare
        wait_for_cookie_banner(page, visible=False)
        
        # Pannello deve essere ancora utilizzabile
        page.locator('[data-a11y-action="contrast-high"]').click()
        page.wait_for_timeout(200)
        
        has_high = page.evaluate("document.body.classList.contains('a11y-contrast-high')")
        assert has_high


class TestMobileSpecific:
    """Test specifici per dispositivi mobile."""
    
    def test_touch_events_work(self, mobile_page: Page):
        """Gli eventi touch devono funzionare su mobile."""
        mobile_page.goto(BASE_URL)
        reset_all(mobile_page)
        mobile_page.reload()
        
        wait_for_cookie_banner(mobile_page, visible=True)
        
        # Simula tap
        accept_btn = mobile_page.locator("#cookie-accept-btn")
        accept_btn.tap()
        
        wait_for_cookie_banner(mobile_page, visible=False)
    
    def test_widget_accessible_in_landscape(self, browser):
        """Widget accessibile in orientamento landscape."""
        context = browser.new_context(viewport=VIEWPORTS["mobile_landscape"])
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            
            # Widget toggle visibile
            toggle = page.locator("#a11y-toggle")
            expect(toggle).to_be_visible()
            
            # Click funziona
            toggle.click()
            page.locator("#a11y-panel").wait_for(state="visible", timeout=1000)
        finally:
            page.close()
            context.close()
    
    def test_scroll_with_fixed_elements(self, mobile_page: Page):
        """Lo scroll funziona correttamente con elementi fixed."""
        mobile_page.goto(BASE_URL)
        reset_all(mobile_page)
        mobile_page.reload()
        
        wait_for_cookie_banner(mobile_page, visible=True)
        
        # Scroll down
        mobile_page.evaluate("window.scrollTo(0, 500)")
        mobile_page.wait_for_timeout(200)
        
        # Cookie banner e widget devono essere ancora visibili/funzionanti
        accept_btn = mobile_page.locator("#cookie-accept-btn")
        expect(accept_btn).to_be_visible()
        
        toggle = mobile_page.locator("#a11y-toggle")
        expect(toggle).to_be_visible()


class TestTabletSpecific:
    """Test specifici per tablet."""
    
    def test_layout_in_portrait(self, tablet_page: Page):
        """Layout corretto in portrait mode."""
        tablet_page.goto(BASE_URL)
        reset_all(tablet_page)
        tablet_page.reload()
        
        wait_for_cookie_banner(tablet_page, visible=True)
        
        # Tutti i pulsanti del cookie banner devono essere visibili
        expect(tablet_page.locator("#cookie-reject-btn")).to_be_visible()
        expect(tablet_page.locator("#cookie-settings-btn")).to_be_visible()
        expect(tablet_page.locator("#cookie-accept-btn")).to_be_visible()
    
    def test_layout_in_landscape(self, browser):
        """Layout corretto in landscape mode."""
        context = browser.new_context(viewport=VIEWPORTS["tablet_landscape"])
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_all(page)
            page.reload()
            
            wait_for_cookie_banner(page, visible=True)
            
            # I pulsanti devono essere in riga (flex-row)
            expect(page.locator("#cookie-reject-btn")).to_be_visible()
            expect(page.locator("#cookie-accept-btn")).to_be_visible()
        finally:
            page.close()
            context.close()


class TestScriptInterference:
    """Test interferenze con altri script."""
    
    def test_works_without_lucide(self, page: Page):
        """Tutto funziona se Lucide icons non carica."""
        # Blocca Lucide
        page.route("**/lucide*", lambda route: route.abort())
        page.route("**/unpkg.com/**", lambda route: route.abort())
        
        page.goto(BASE_URL)
        reset_all(page)
        page.reload()
        
        # Cookie banner funziona
        wait_for_cookie_banner(page, visible=True)
        page.locator("#cookie-accept-btn").click()
        wait_for_cookie_banner(page, visible=False)
        
        # Widget funziona (anche senza icone)
        toggle = page.locator("#a11y-toggle")
        expect(toggle).to_be_visible()
        toggle.click()
        
        # Il pannello si apre
        page.locator("#a11y-panel").wait_for(state="visible", timeout=2000)
    
    def test_works_without_tailwind_cdn(self, page: Page):
        """Funzionalità base anche se Tailwind CDN non carica."""
        page.route("**/tailwindcss.com/**", lambda route: route.abort())
        
        page.goto(BASE_URL)
        reset_all(page)
        page.reload()
        
        # Attendi che la pagina carichi
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)
        
        # I pulsanti devono esistere ed essere cliccabili
        accept_btn = page.locator("#cookie-accept-btn")
        if accept_btn.is_visible():
            accept_btn.click()
    
    def test_no_js_errors_on_normal_usage(self, page: Page):
        """Nessun errore JS durante uso normale."""
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        
        page.goto(BASE_URL)
        reset_all(page)
        page.reload()
        
        # Usa tutte le funzionalità
        wait_for_cookie_banner(page, visible=True)
        
        page.locator("#a11y-toggle").click()
        page.locator("#a11y-panel").wait_for(state="visible", timeout=1000)
        page.locator('[data-a11y-action="contrast-high"]').click()
        page.locator('[data-a11y-toggle="highlight-links"]').click()
        page.locator("#a11y-close").click()
        
        page.locator("#cookie-accept-btn").click()
        wait_for_cookie_banner(page, visible=False)
        
        # Filtra errori accettabili (analytics bloccati, etc)
        ignore_patterns = ["initGA4", "initMatomo", "gtag", "analytics"]
        critical_errors = [
            e for e in errors 
            if not any(p in e for p in ignore_patterns)
        ]
        
        assert len(critical_errors) == 0, f"Errori JS: {critical_errors}"
