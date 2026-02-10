# 🚀 Migliorie Performance - PageSpeed Insights

## 📊 Stato Attuale (Mobile)

| Metrica | Punteggio |
|---------|-----------|
| Prestazioni | 82 |
| Accessibilità | 92 |
| Best Practice | 100 |
| SEO | 100 |

---

## ✅ Migliorie Implementate

### 1. Font Loading Ottimizzato
- **Problema**: Font Google bloccavano il rendering
- **Soluzione**: Aggiunto `preload` + `media="print" onload` per caricamento asincrono
- **File**: [base.html](../sld_project/templates/base.html)
- **Risparmio stimato**: ~500-800ms FCP

### 2. Lucide Icons Differito
- **Problema**: Script bloccava il parsing HTML
- **Soluzione**: Aggiunto `defer` allo script
- **File**: [base.html](../sld_project/templates/base.html)

### 3. Immagini con Dimensioni Esplicite
- **Problema**: Immagini senza `width`/`height` causano CLS
- **Soluzione**: Aggiunti attributi espliciti + `fetchpriority="high"`
- **File**: [navigation.html](../sld_project/templates/includes/navigation.html), [home_page.html](../home/templates/home/home_page.html)

### 4. Compressione Gzip Nginx
- **Problema**: File non compressi
- **Soluzione**: Configurazione gzip ottimizzata
- **File**: [nginx-sld.conf](../deploy/nginx-sld.conf)
- **Risparmio stimato**: 60-80% bandwidth

### 5. Cache Aggressiva File Statici
- **Problema**: Cache insufficiente (12h-30d)
- **Soluzione**: Cache 1 anno con `immutable`
- **File**: [nginx-sld.conf](../deploy/nginx-sld.conf)

---

## 🔧 Migliorie Raccomandate (Non Ancora Implementate)

### 1. Sostituire Tailwind CDN con Build di Produzione

Il Tailwind CDN include TUTTO il framework (~300KB). Una build di produzione include solo le classi usate.

```bash
# Installare Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Creare tailwind.config.js
# Poi buildare per produzione:
npx tailwindcss -i ./src/input.css -o ./static/css/tailwind.min.css --minify
```

**Risparmio stimato**: ~250-280KB (da ~300KB a ~15-20KB)

### 2. Self-Hosting Font Inter

Invece di usare Google Fonts, hostare i font localmente:

```bash
# Scaricare i font da: https://fonts.google.com/specimen/Inter
# Convertirli in woff2 e metterli in static/fonts/
```

**File CSS da aggiungere**:
```css
@font-face {
    font-family: 'Inter';
    src: url('/static/fonts/Inter-Regular.woff2') format('woff2');
    font-weight: 400;
    font-display: swap;
}
/* ... altri pesi */
```

### 3. Lazy Loading Immagini Below-the-Fold

Per immagini non visibili inizialmente:
```html
<img src="..." loading="lazy" decoding="async">
```

### 4. Preload Risorse Critiche

```html
<link rel="preload" href="/static/images/StudioLegale.svg" as="image">
<link rel="preload" href="/static/js/sld_project.js" as="script">
```

### 5. Migliorare Contrasto Colori (Accessibilità)

Il colore `brand-gray` (#6b7280) ha contrasto 5.38:1.
Per AAA compliance su testo piccolo, usare un grigio più scuro:

```python
# In sld_project/models.py, cambiare default:
'brand-gray': self.color_gray or '#4b5563',  # Contrasto 7:1
```

### 6. Critical CSS Inline

Estrarre il CSS critico e inlinearlo nel `<head>`:
```bash
npm install -g critical
critical https://studiolegaledonofrio.it --inline > base_critical.html
```

---

## 📈 Metriche Target

| Metrica | Attuale | Target |
|---------|---------|--------|
| FCP | 3.5s | < 2.5s |
| LCP | 3.7s | < 2.5s |
| CLS | 0.009 | < 0.1 ✅ |
| TBT | 0ms | < 200ms ✅ |

---

## 🧪 Come Testare

```bash
# Test locale con Lighthouse CLI
npm install -g lighthouse
lighthouse https://studiolegaledonofrio.it --view

# O usare PageSpeed Insights online
# https://pagespeed.web.dev/
```

---

## 📝 Note

- Le modifiche a nginx richiedono restart: `sudo nginx -s reload`
- Dopo aver buildato Tailwind, aggiornare il riferimento in base.html
- Testare sempre su dispositivo reale dopo le modifiche
