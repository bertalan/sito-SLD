# Script di Deploy e Verifica

Questa cartella contiene script bash per l'installazione e la verifica del sito Studio Legale su server di produzione.

## 📋 Indice

| Script | Descrizione | Quando usarlo |
|--------|-------------|---------------|
| `1_install.sh` | Installazione iniziale | Primo deploy su nuovo server |
| `2_verifiche.sh` | Verifica produzione | Dopo ogni deploy, monitoraggio |
| `update_from_upstream.sh` | Aggiornamento da upstream | Sincronizzazione con repo originale |

> **💡 Nota importante:** Entrambi gli script sono **posizione-indipendenti**:
> - `1_install.sh` installa nella directory `APP_DIR` configurata, **non** dove viene eseguito
> - `2_verifiche.sh` verifica il `DOMAIN` configurato via HTTP, può essere eseguito da **qualsiasi macchina**

---

## 1️⃣ 1_install.sh - Installazione Iniziale

### Cosa fa

- Verifica prerequisiti (Python, PostgreSQL, Nginx, Git)
- Crea database PostgreSQL
- Clona repository Git nella directory `APP_DIR`
- Crea virtualenv e installa dipendenze
- Genera file `.env` da template
- Esegue migrazioni Django e collectstatic
- Configura servizio Gunicorn systemd
- Crea superuser admin

### Configurazione

Modifica le variabili all'inizio dello script:

```bash
DOMAIN="example.com"              # Il tuo dominio
APP_DIR="/www/wwwroot/${DOMAIN}"  # Dove verrà installato il sito
REPO_URL="https://github.com/..."
DB_NAME="studio_db"
DB_USER="studio_user"
DB_PASS="CHANGE_THIS_PASSWORD"    # ⚠️ CAMBIA QUESTA PASSWORD!
```

### Esecuzione

```bash
# Sul server, come root, DA QUALSIASI CARTELLA
sudo bash /path/to/scripts/1_install.sh

# Oppure dalla home
sudo bash ~/1_install.sh

# ✅ Lo script installerà in APP_DIR, non nella directory corrente
```

### Prerequisiti

- Ubuntu/Debian con aaPanel (opzionale)
- Python 3.8+, PostgreSQL, Nginx, Git installati

---

## 2️⃣ 2_verifiche.sh - Verifica Produzione

### Cosa fa

Verifica il sito in produzione tramite richieste HTTP al dominio configurato.

**Non richiede accesso al server** - può essere eseguito da qualsiasi macchina con connessione internet.

### Cosa verifica

| # | Categoria | Dettagli |
|---|-----------|----------|
| 1 | **DNS** | Risoluzione, redirect HTTP→HTTPS, www→naked |
| 2 | **SSL/TLS** | Certificato valido, scadenza, TLS 1.2/1.3 |
| 3 | **Security Headers** | HSTS, X-Frame-Options, CSP, Referrer-Policy |
| 4 | **File Statici** | CSS, Logo, Favicon, Compressione gzip |
| 5 | **SEO** | Title, Meta description, Canonical, Open Graph |
| 6 | **Schema.org** | JSON-LD, LegalService, postalCode, address |
| 7 | **Risorse SEO** | robots.txt, sitemap.xml, domini corretti |
| 8 | **Pagine** | Status code di tutte le pagine dal menu |
| 9 | **Performance** | HTTP/2, Keep-Alive, TTFB |
| 10 | **Domini** | Confronto www vs naked domain |

### Configurazione

```bash
DOMAIN="example.com"  # Il dominio da verificare
```

### Esecuzione

```bash
# Da qualsiasi macchina (locale, server, CI/CD)
bash scripts/2_verifiche.sh

# Esempio: dal tuo Mac per verificare il sito in produzione
bash ~/Desktop/2_verifiche.sh

# ✅ Verifica il DOMAIN configurato via HTTP, non serve essere sul server
```

### Output

- ✓ Test passati (verde)
- ⚠ Warning da valutare (giallo)  
- ✗ Errori da risolvere (rosso)
- **Score finale** in percentuale

---

## 🔧 Dipendenze

| Comando | 1_install.sh | 2_verifiche.sh |
|---------|:------------:|:--------------:|
| bash    | ✓            | ✓              |
| curl    |              | ✓              |
| openssl |              | ✓              |
| dig     |              | ✓              |
| bc      |              | opzionale      |
| python3 | ✓            |                |
| git     | ✓            |                |
| psql    | ✓            |                |

---

## 📍 Riepilogo Posizioni

| Script | Dove eseguirlo | Cosa modifica/verifica |
|--------|----------------|------------------------|
| `1_install.sh` | Sul server (qualsiasi cartella) | Installa in `APP_DIR` configurato |
| `2_verifiche.sh` | Ovunque (anche il tuo laptop) | Verifica `DOMAIN` via HTTP |

---

## 🔄 Workflow tipico

```bash
# 1. Prima installazione (sul server)
sudo bash scripts/1_install.sh

# 2. Verifica che tutto funzioni (da qualsiasi macchina)
bash scripts/2_verifiche.sh

# 3. Dopo ogni deploy, verifica di nuovo
bash scripts/2_verifiche.sh
```
