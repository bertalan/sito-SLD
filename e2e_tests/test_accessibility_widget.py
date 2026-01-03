"""
Test E2E per il Widget Accessibilità.
Verifica tutte le funzionalità con combinazioni di impostazioni.
Eseguito su mobile, tablet e desktop.
"""
import pytest
import re
from playwright.sync_api import Page, expect
import json

from conftest import BASE_URL, clear_cookies_and_storage, VIEWPORTS


def open_a11y_panel(page: Page, timeout: int = 3000):
    """Apre il pannello accessibilità."""
    toggle = page.locator("#a11y-toggle")
    panel = page.locator("#a11y-panel")
    
    toggle.click()
    panel.wait_for(state="visible", timeout=timeout)


def close_a11y_panel(page: Page):
    """Chiude il pannello accessibilità."""
    page.locator("#a11y-close").click()
    page.wait_for_timeout(300)


def reset_a11y_preferences(page: Page):
    """Resetta le preferenze accessibilità."""
    page.evaluate("localStorage.removeItem('a11y_preferences')")


class TestAccessibilityWidgetDisplay:
    """Test visualizzazione widget accessibilità."""
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_widget_toggle_visible(self, browser, viewport_name, viewport):
        """Il pulsante toggle del widget deve essere sempre visibile."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            
            toggle = page.locator("#a11y-toggle")
            expect(toggle).to_be_visible()
            
            # Verifica che abbia aria-label
            expect(toggle).to_have_attribute("aria-label", re.compile(r".+"))
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_emergency_reset_button_visible(self, browser, viewport_name, viewport):
        """Il pulsante reset emergenza deve essere visibile."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            
            reset_btn = page.locator("#a11y-emergency-reset")
            expect(reset_btn).to_be_visible()
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    def test_panel_opens_and_closes(self, browser, viewport_name, viewport):
        """Il pannello deve aprirsi e chiudersi correttamente."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            
            panel = page.locator("#a11y-panel")
            
            # Inizialmente nascosto
            expect(panel).to_have_attribute("hidden", "")
            
            # Apri
            open_a11y_panel(page)
            expect(panel).not_to_have_attribute("hidden", "")
            
            # Chiudi
            close_a11y_panel(page)
            page.wait_for_timeout(500)
            expect(panel).to_have_attribute("hidden", "")
        finally:
            page.close()
            context.close()


class TestFontSizeControls:
    """Test controlli dimensione testo."""
    
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_increase_font_size(self, browser, viewport_name, viewport):
        """Aumentare la dimensione del testo deve funzionare."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            page.reload()
            
            open_a11y_panel(page)
            
            increase_btn = page.locator('[data-a11y-action="font-increase"]')
            font_display = page.locator("#a11y-font-size")
            
            initial_size = font_display.inner_text()
            
            # Click per aumentare
            increase_btn.click()
            page.wait_for_timeout(300)
            
            new_size = font_display.inner_text()
            
            # La percentuale deve essere aumentata
            initial_pct = int(initial_size.replace("%", ""))
            new_pct = int(new_size.replace("%", ""))
            
            assert new_pct > initial_pct, f"Font size non aumentato: {initial_size} -> {new_size}"
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_decrease_font_size(self, browser, viewport_name, viewport):
        """Diminuire la dimensione del testo deve funzionare."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            page.reload()
            
            open_a11y_panel(page)
            
            # Prima aumenta per avere spazio per diminuire
            increase_btn = page.locator('[data-a11y-action="font-increase"]')
            increase_btn.click()
            page.wait_for_timeout(200)
            
            decrease_btn = page.locator('[data-a11y-action="font-decrease"]')
            font_display = page.locator("#a11y-font-size")
            
            before_size = font_display.inner_text()
            decrease_btn.click()
            page.wait_for_timeout(300)
            after_size = font_display.inner_text()
            
            before_pct = int(before_size.replace("%", ""))
            after_pct = int(after_size.replace("%", ""))
            
            assert after_pct < before_pct, f"Font size non diminuito: {before_size} -> {after_size}"
        finally:
            page.close()
            context.close()
    
    def test_font_size_limits(self, page: Page):
        """La dimensione testo deve avere limiti min/max."""
        page.goto(BASE_URL)
        reset_a11y_preferences(page)
        page.reload()
        
        open_a11y_panel(page)
        
        decrease_btn = page.locator('[data-a11y-action="font-decrease"]')
        increase_btn = page.locator('[data-a11y-action="font-increase"]')
        font_display = page.locator("#a11y-font-size")
        
        # Diminuisci al minimo
        for _ in range(20):
            decrease_btn.click()
            page.wait_for_timeout(50)
        
        min_size = int(font_display.inner_text().replace("%", ""))
        assert min_size >= 80, f"Minimo troppo basso: {min_size}%"
        
        # Aumenta al massimo
        for _ in range(20):
            increase_btn.click()
            page.wait_for_timeout(50)
        
        max_size = int(font_display.inner_text().replace("%", ""))
        assert max_size <= 200, f"Massimo troppo alto: {max_size}%"


class TestContrastModes:
    """Test modalità contrasto."""
    
    CONTRAST_ACTIONS = [
        ("contrast-normal", "a11y-contrast-normal", None),
        ("contrast-high", "a11y-contrast-high", "body filter invert/contrast"),
        ("contrast-inverted", "a11y-contrast-inverted", "yellow bg"),
    ]
    
    @pytest.mark.parametrize("viewport_name,viewport", VIEWPORTS.items())
    @pytest.mark.parametrize("action,css_class,description", CONTRAST_ACTIONS)
    def test_contrast_mode_applies(self, browser, viewport_name, viewport, action, css_class, description):
        """Ogni modalità contrasto deve applicare la classe CSS corretta."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            page.reload()
            
            open_a11y_panel(page)
            
            # Click sul pulsante contrasto
            contrast_btn = page.locator(f'[data-a11y-action="{action}"]')
            contrast_btn.click()
            page.wait_for_timeout(300)
            
            # Verifica che la classe sia applicata (o rimossa per normal)
            if action == "contrast-normal":
                has_high = page.evaluate("document.body.classList.contains('a11y-contrast-high')")
                has_inverted = page.evaluate("document.body.classList.contains('a11y-contrast-inverted')")
                assert not has_high and not has_inverted, "Classi contrasto non rimosse in modalità normale"
            else:
                has_class = page.evaluate(f"document.body.classList.contains('{css_class}')")
                assert has_class, f"Classe {css_class} non applicata"
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_contrast_modes_mutually_exclusive(self, browser, viewport_name, viewport):
        """Solo una modalità contrasto può essere attiva alla volta."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            page.reload()
            
            open_a11y_panel(page)
            
            # Attiva alto contrasto
            page.locator('[data-a11y-action="contrast-high"]').click()
            page.wait_for_timeout(200)
            
            assert page.evaluate("document.body.classList.contains('a11y-contrast-high')")
            
            # Attiva invertito
            page.locator('[data-a11y-action="contrast-inverted"]').click()
            page.wait_for_timeout(200)
            
            # Solo invertito deve essere attivo
            has_high = page.evaluate("document.body.classList.contains('a11y-contrast-high')")
            has_inverted = page.evaluate("document.body.classList.contains('a11y-contrast-inverted')")
            
            assert not has_high, "Alto contrasto dovrebbe essere disattivato"
            assert has_inverted, "Invertito dovrebbe essere attivo"
        finally:
            page.close()
            context.close()


class TestToggleSwitches:
    """Test per i toggle switch (evidenzia link, focus potenziato, ecc.)."""
    
    TOGGLES = [
        "highlight-links",
        "enhanced-focus",
        "reduce-motion",
        "reading-mode",
        "large-cursor",
    ]
    
    @pytest.mark.parametrize("toggle_name", TOGGLES)
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_toggle_switch_works(self, browser, viewport_name, viewport, toggle_name):
        """Ogni toggle deve attivare/disattivare correttamente."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            page.reload()
            
            open_a11y_panel(page)
            
            toggle = page.locator(f'[data-a11y-toggle="{toggle_name}"]')
            
            # Verifica stato iniziale (off)
            initial_state = toggle.get_attribute("aria-checked")
            assert initial_state == "false", f"Toggle {toggle_name} dovrebbe essere off inizialmente"
            
            # Attiva
            toggle.click()
            page.wait_for_timeout(200)
            
            new_state = toggle.get_attribute("aria-checked")
            assert new_state == "true", f"Toggle {toggle_name} dovrebbe essere on dopo click"
            
            # Verifica che la classe CSS sia applicata al body
            css_class = f"a11y-{toggle_name}"
            has_class = page.evaluate(f"document.body.classList.contains('{css_class}')")
            assert has_class, f"Classe {css_class} non applicata al body"
            
            # Disattiva
            toggle.click()
            page.wait_for_timeout(200)
            
            final_state = toggle.get_attribute("aria-checked")
            assert final_state == "false", f"Toggle {toggle_name} dovrebbe essere off dopo secondo click"
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_multiple_toggles_can_be_active(self, browser, viewport_name, viewport):
        """Più toggle possono essere attivi contemporaneamente."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            page.reload()
            
            open_a11y_panel(page)
            
            # Attiva più toggle
            page.locator('[data-a11y-toggle="highlight-links"]').click()
            page.wait_for_timeout(100)
            page.locator('[data-a11y-toggle="enhanced-focus"]').click()
            page.wait_for_timeout(100)
            page.locator('[data-a11y-toggle="reduce-motion"]').click()
            page.wait_for_timeout(200)
            
            # Verifica che tutti siano attivi
            assert page.evaluate("document.body.classList.contains('a11y-highlight-links')")
            assert page.evaluate("document.body.classList.contains('a11y-enhanced-focus')")
            assert page.evaluate("document.body.classList.contains('a11y-reduce-motion')")
        finally:
            page.close()
            context.close()


class TestResetFunctionality:
    """Test funzionalità di reset."""
    
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_reset_button_in_panel(self, browser, viewport_name, viewport):
        """Il pulsante reset nel pannello deve ripristinare le impostazioni."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            page.reload()
            
            open_a11y_panel(page)
            
            # Modifica alcune impostazioni
            page.locator('[data-a11y-action="contrast-high"]').click()
            page.locator('[data-a11y-toggle="highlight-links"]').click()
            page.locator('[data-a11y-action="font-increase"]').click()
            page.locator('[data-a11y-action="font-increase"]').click()
            page.wait_for_timeout(300)
            
            # Verifica che le modifiche siano state applicate
            assert page.evaluate("document.body.classList.contains('a11y-contrast-high')")
            
            # Click reset
            page.locator('[data-a11y-action="reset"]').click()
            page.wait_for_timeout(500)
            
            # Verifica reset
            has_high = page.evaluate("document.body.classList.contains('a11y-contrast-high')")
            has_links = page.evaluate("document.body.classList.contains('a11y-highlight-links')")
            
            assert not has_high, "Alto contrasto dovrebbe essere disattivato dopo reset"
            assert not has_links, "Highlight links dovrebbe essere disattivato dopo reset"
            
            # Verifica dimensione testo
            font_display = page.locator("#a11y-font-size")
            expect(font_display).to_have_text("100%")
        finally:
            page.close()
            context.close()
    
    def test_emergency_reset_double_click(self, page: Page):
        """Il doppio click sul pulsante emergenza deve resettare tutto."""
        page.goto(BASE_URL)
        reset_a11y_preferences(page)
        page.reload()
        
        open_a11y_panel(page)
        
        # Applica modifiche pesanti
        page.locator('[data-a11y-action="contrast-inverted"]').click()
        page.locator('[data-a11y-toggle="large-cursor"]').click()
        page.wait_for_timeout(200)
        
        # Chiudi il pannello
        close_a11y_panel(page)
        
        # Doppio click sul reset emergenza
        reset_btn = page.locator("#a11y-emergency-reset")
        reset_btn.dblclick()
        
        # Attendi il reload
        page.wait_for_url(BASE_URL + "**")
        page.wait_for_timeout(500)
        
        # Verifica che tutto sia resettato
        has_inverted = page.evaluate("document.body.classList.contains('a11y-contrast-inverted')")
        has_cursor = page.evaluate("document.body.classList.contains('a11y-large-cursor')")
        
        assert not has_inverted, "Contrast inverted dovrebbe essere off dopo emergency reset"
        assert not has_cursor, "Large cursor dovrebbe essere off dopo emergency reset"


class TestPersistence:
    """Test persistenza impostazioni in localStorage."""
    
    def test_preferences_saved_to_localstorage(self, page: Page):
        """Le preferenze devono essere salvate in localStorage."""
        page.goto(BASE_URL)
        reset_a11y_preferences(page)
        page.reload()
        
        open_a11y_panel(page)
        
        # Modifica impostazioni
        page.locator('[data-a11y-action="contrast-high"]').click()
        page.locator('[data-a11y-toggle="highlight-links"]').click()
        page.wait_for_timeout(300)
        
        # Verifica localStorage
        prefs = page.evaluate("localStorage.getItem('a11y_preferences')")
        assert prefs is not None, "Preferenze non salvate in localStorage"
        
        prefs_obj = json.loads(prefs)
        assert prefs_obj.get("contrast") == "high" or "a11y-contrast-high" in str(prefs_obj)
    
    def test_preferences_restored_on_reload(self, page: Page):
        """Le preferenze devono essere ripristinate al reload."""
        page.goto(BASE_URL)
        reset_a11y_preferences(page)
        page.reload()
        
        open_a11y_panel(page)
        
        # Modifica impostazioni
        page.locator('[data-a11y-action="contrast-high"]').click()
        page.locator('[data-a11y-action="font-increase"]').click()
        page.locator('[data-a11y-action="font-increase"]').click()
        page.wait_for_timeout(300)
        
        # Reload
        page.reload()
        page.wait_for_timeout(500)
        
        # Verifica che le impostazioni siano state ripristinate
        has_high = page.evaluate("document.body.classList.contains('a11y-contrast-high')")
        assert has_high, "Alto contrasto non ripristinato dopo reload"


class TestAccessibilityWidgetWithCookieBanner:
    """Test interazione tra widget accessibilità e cookie banner."""
    
    @pytest.mark.parametrize("contrast_mode", ["contrast-high", "contrast-inverted"])
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_cookie_banner_clickable_in_contrast_modes(
        self, browser, viewport_name, viewport, contrast_mode
    ):
        """I pulsanti del cookie banner devono funzionare in tutte le modalità contrasto."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            clear_cookies_and_storage(page)
            page.reload()
            
            # Attendi cookie banner
            page.wait_for_function(
                "!document.getElementById('cookie-banner').classList.contains('translate-y-full')",
                timeout=3000
            )
            
            open_a11y_panel(page)
            
            # Attiva modalità contrasto
            page.locator(f'[data-a11y-action="{contrast_mode}"]').click()
            page.wait_for_timeout(300)
            
            close_a11y_panel(page)
            
            # Il cookie banner deve essere ancora cliccabile
            accept_btn = page.locator("#cookie-accept-btn")
            expect(accept_btn).to_be_visible()
            expect(accept_btn).to_be_enabled()
            
            # Click
            accept_btn.click()
            
            # Deve funzionare
            page.wait_for_function(
                "document.getElementById('cookie-banner').classList.contains('translate-y-full')",
                timeout=3000
            )
            
            # Cookie impostato
            cookies = page.context.cookies()
            consent_cookie = next((c for c in cookies if c["name"] == "cookie_consent"), None)
            assert consent_cookie is not None, \
                f"Cookie non impostato in {contrast_mode} su {viewport_name}"
        finally:
            page.close()
            context.close()
    
    @pytest.mark.parametrize("viewport_name,viewport", [
        ("mobile_portrait", VIEWPORTS["mobile_portrait"]),
        ("desktop_large", VIEWPORTS["desktop_large"]),
    ])
    def test_widget_visible_above_cookie_banner(self, browser, viewport_name, viewport):
        """Il widget accessibilità deve essere visibile sopra il cookie banner."""
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(BASE_URL)
            reset_a11y_preferences(page)
            clear_cookies_and_storage(page)
            page.reload()
            
            # Attendi che entrambi siano visibili
            page.wait_for_function(
                "!document.getElementById('cookie-banner').classList.contains('translate-y-full')",
                timeout=3000
            )
            
            # Il toggle widget deve essere visibile
            toggle = page.locator("#a11y-toggle")
            expect(toggle).to_be_visible()
            
            # Il toggle deve essere cliccabile (non coperto dal banner)
            toggle.click()
            
            # Il pannello deve aprirsi
            panel = page.locator("#a11y-panel")
            panel.wait_for(state="visible", timeout=1000)
        finally:
            page.close()
            context.close()


class TestKeyboardAccessibility:
    """Test navigazione da tastiera del widget."""
    
    def test_panel_can_be_opened_with_keyboard(self, page: Page):
        """Il pannello deve essere apribile via tastiera."""
        page.goto(BASE_URL)
        reset_a11y_preferences(page)
        page.reload()
        
        # Focus sul toggle
        page.locator("#a11y-toggle").focus()
        
        # Premi Enter
        page.keyboard.press("Enter")
        
        # Il pannello deve aprirsi
        panel = page.locator("#a11y-panel")
        panel.wait_for(state="visible", timeout=1000)
    
    def test_escape_closes_panel(self, page: Page):
        """Premere Escape deve chiudere il pannello."""
        page.goto(BASE_URL)
        reset_a11y_preferences(page)
        page.reload()
        
        open_a11y_panel(page)
        
        # Premi Escape
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        
        # Il pannello deve essere chiuso
        panel = page.locator("#a11y-panel")
        expect(panel).to_have_attribute("hidden", "")
    
    def test_tab_navigation_within_panel(self, page: Page):
        """Tab deve navigare tra i controlli del pannello."""
        page.goto(BASE_URL)
        reset_a11y_preferences(page)
        page.reload()
        
        open_a11y_panel(page)
        
        focusable_elements = []
        
        # Tab attraverso il pannello
        for _ in range(15):
            page.keyboard.press("Tab")
            focused = page.evaluate("document.activeElement?.dataset?.a11yAction || document.activeElement?.dataset?.a11yToggle || document.activeElement?.id")
            if focused:
                focusable_elements.append(focused)
        
        # Dovrebbero esserci diversi elementi focusabili
        unique_elements = set(focusable_elements)
        assert len(unique_elements) >= 5, f"Troppo pochi elementi navigabili: {unique_elements}"


class TestWidgetIsolation:
    """Test isolamento del widget dagli effetti di accessibilità."""
    
    @pytest.mark.parametrize("contrast_mode", ["contrast-high", "contrast-inverted"])
    def test_widget_not_affected_by_contrast_filters(self, page: Page, contrast_mode):
        """Il widget non deve essere influenzato dai filtri contrasto."""
        page.goto(BASE_URL)
        reset_a11y_preferences(page)
        page.reload()
        
        open_a11y_panel(page)
        
        # Attiva contrasto
        page.locator(f'[data-a11y-action="{contrast_mode}"]').click()
        page.wait_for_timeout(300)
        
        # Verifica che il widget abbia filter: none
        toggle_filter = page.evaluate(
            "getComputedStyle(document.getElementById('a11y-toggle')).filter"
        )
        panel_filter = page.evaluate(
            "getComputedStyle(document.getElementById('a11y-panel')).filter"
        )
        
        assert toggle_filter == "none", f"Toggle ha filtro: {toggle_filter}"
        assert panel_filter == "none", f"Panel ha filtro: {panel_filter}"
    
    def test_widget_pointer_events_always_active(self, page: Page):
        """Il widget deve avere sempre pointer-events attivi."""
        page.goto(BASE_URL)
        reset_a11y_preferences(page)
        page.reload()
        
        # Applica vari effetti
        page.evaluate("document.body.style.pointerEvents = 'none'")
        
        # Il toggle deve comunque essere cliccabile
        toggle = page.locator("#a11y-toggle")
        
        pointer_events = page.evaluate(
            "getComputedStyle(document.getElementById('a11y-toggle')).pointerEvents"
        )
        
        assert pointer_events == "auto", f"Pointer events errati: {pointer_events}"
