# Pulizia Link e Mailto Problematici

Questo script risolve i problemi di link e mailto malformati che si sono portati dietro durante la migrazione.

## 🎯 Problemi Risolti

- **Doppi apici**: `"mailto:email@example.com"` → `mailto:email@example.com`
- **Entità HTML**: `&quot;http://...&quot;` → `"http://..."`
- **Tag escapati**: `&lt;a href=...&gt;` → `<a href=...>`
- **Href duplicati**: `href="..."href="..."` → `href="..."`

## 🚀 Uso

### Opzione 1: Script SQL (più veloce)

```bash
# 1. Crea backup del database
docker compose exec db pg_dump -U postgres sld_db > backup_pre_cleanup.sql

# 2. Esegui lo script SQL
docker compose exec db psql -U postgres -d sld_db -f /app/scripts/clean_database_links.sql

# 3. Verifica nel log
docker compose exec db psql -U postgres -d sld_db -c "SELECT * FROM cleanup_log LIMIT 10;"

# 4. Se OK, conferma con COMMIT
docker compose exec db psql -U postgres -d sld_db -c "COMMIT;"

# Se problemi, fai ROLLBACK
docker compose exec db psql -U postgres -d sld_db -c "ROLLBACK;"
```

### Opzione 2: Script Python (più controllo)

```bash
# Attiva virtualenv
source venv/bin/activate

# 1. Analisi senza modifiche (consigliato)
python3 scripts/clean_database_links_python.py --dry-run --verbose

# 2. Se OK, esegui la pulizia con backup automatico
python3 scripts/clean_database_links_python.py --backup --verbose

# 3. Verifica il log
cat scripts/cleanup_log.json
```

## 📊 Output Atteso

```
================================================================================
🔍 SCANSIONE DATABASE - LINK E MAILTO PROBLEMATICI
================================================================================

📋 Scansione tabella: wagtailcore_page
  ✗ ID 5, colonna 'body':
    - Rimuove doppi apici attorno a mailto:
    - Decodifica &quot;

📋 Scansione tabella: articles_article
  ✗ ID 12, colonna 'content':
    - Decodifica &lt;
    - Decodifica &gt;

================================================================================
📊 REPORT FINALE
================================================================================

Tabelle scansionate: 7
Record verificati: 156
Record modificati: 23

Pattern trovati e corretti:
  - Rimuove doppi apici attorno a mailto:: 15 occorrenze
  - Decodifica &quot;: 12 occorrenze
  - Decodifica &lt;: 8 occorrenze

✅ Database pulito con successo!
```

## 🔄 Rollback

### Se hai usato lo script SQL:
```bash
# Ripristina dal backup
docker compose exec db psql -U postgres -d sld_db < backup_pre_cleanup.sql
```

### Se hai usato lo script Python:
Lo script Python usa transazioni, quindi puoi semplicemente rispondere "N" alla conferma finale.

## ⚠️ Note Importanti

1. **Sempre fare backup prima**: Sia gli script che le istruzioni prevedono backup
2. **Test in dry-run**: Lo script Python ha modalità dry-run per testare senza modifiche
3. **Verifica dopo**: Controlla alcune pagine del sito dopo la pulizia
4. **Log dettagliato**: Tutti gli script creano log delle modifiche

## 🐛 Troubleshooting

### Errore "Django non trovato"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Errore di connessione al database
Verifica che il database sia avviato:
```bash
docker compose ps
# oppure
sudo systemctl status postgresql
```

### Permessi insufficienti
```bash
# Assicurati di avere i permessi sul database
docker compose exec db psql -U postgres -d sld_db -c "SELECT current_user;"
```
