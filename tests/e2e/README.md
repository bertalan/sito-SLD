# Test E2E per Cookie Banner e Accessibilità

## Setup

1. Installa le dipendenze:
```bash
pip install pytest-playwright
playwright install chromium
```

2. Assicurati che il server Django sia in esecuzione:
```bash
docker compose up -d
# oppure
python manage.py runserver
```

## Esecuzione Test

### Tutti i test
```bash
cd tests/e2e
pytest -v -n 4  # con 4 worker paralleli
```

### Solo test cookie banner
```bash
pytest test_cookie_banner.py -v
```

### Solo test widget accessibilità
```bash
pytest test_accessibility_widget.py -v
```

### Solo test interazioni complete
```bash
pytest test_complete_interactions.py -v
```

### Test su viewport specifico
```bash
# Solo mobile
pytest -v -k "mobile"

# Solo desktop
pytest -v -k "desktop"

# Solo tablet
pytest -v -k "tablet"
```

### Test con browser visibile (debugging)
```bash
pytest -v --headed
```

### Test con slowmo (per vedere le azioni)
```bash
pytest -v --slowmo 500
```

## Struttura Test

### test_cookie_banner.py
- **TestCookieBannerDisplay**: Visualizzazione banner su tutti i viewport
- **TestCookieBannerButtons**: Funzionalità pulsanti (rifiuta, accetta, personalizza)
- **TestCookieBannerAccessibility**: ARIA, tastiera, modalità contrasto
- **TestCookieBannerWithOtherScripts**: Interazioni con Tailwind, Lucide, GA4
- **TestCookieBannerPersistence**: Persistenza consenso tra pagine/reload
- **TestCookieBannerKeyboard**: Navigazione Tab, Enter, Space
- **TestCookieBannerTiming**: Double click, click durante animazione

### test_accessibility_widget.py
- **TestAccessibilityWidgetDisplay**: Visualizzazione widget e pannello
- **TestFontSizeControls**: Aumento/diminuzione font, limiti min/max
- **TestContrastModes**: Normale, alto, invertito, esclusività
- **TestToggleSwitches**: Tutti i toggle (link, focus, motion, lettura, cursore)
- **TestResetFunctionality**: Reset pannello e reset emergenza
- **TestPersistence**: Salvataggio/ripristino preferenze
- **TestAccessibilityWidgetWithCookieBanner**: Interazione widget-banner
- **TestKeyboardAccessibility**: Enter, Escape, Tab navigation
- **TestWidgetIsolation**: Isolamento da filtri CSS

### test_complete_interactions.py
- **TestCompleteUserFlows**: Flussi utente completi
- **TestAllContrastCombinations**: Tutte le combo contrasto + cookie
- **TestAllToggleCombinations**: Tutti i toggle + cookie banner
- **TestEdgeCases**: Casi limite (click rapidi, reload durante animazione)
- **TestMobileSpecific**: Touch, landscape, scroll
- **TestTabletSpecific**: Layout portrait/landscape
- **TestScriptInterference**: Senza Lucide, senza Tailwind, errori JS

## Viewport Testati

| Nome | Larghezza | Altezza | Dispositivo |
|------|-----------|---------|-------------|
| mobile_portrait | 375px | 667px | iPhone SE |
| mobile_landscape | 667px | 375px | iPhone landscape |
| tablet_portrait | 768px | 1024px | iPad portrait |
| tablet_landscape | 1024px | 768px | iPad landscape |
| desktop_small | 1280px | 800px | Laptop |
| desktop_large | 1920px | 1080px | Full HD |

## Configurazione

Modifica `conftest.py` per:
- Cambiare URL base (`BASE_URL`)
- Aggiungere/rimuovere viewport
- Modificare timeout
