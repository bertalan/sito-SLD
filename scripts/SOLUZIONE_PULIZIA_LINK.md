# 🔧 Soluzione Pulizia Link e Mailto Problematici

## 📋 Problema Identificato

Durante la migrazione da Joomla a Wagtail, molti contenuti HTML si sono portati dietro:
- Link con doppi apici: `"mailto:email@example.com"` o `"http://..."`
- Entità HTML escapate: `&quot;`, `&lt;`, `&gt;`, `&amp;`
- Tag HTML malformati: `&lt;a href=&quot;...&quot;&gt;`
- Href duplicati o corrotti

Questi causano errori di visualizzazione e malfunzionamenti dei link sul sito.

---

## 🎯 Le Due Soluzioni Proposte

### ✅ Soluzione 1: Script SQL (CONSIGLIATA per velocità)

**Vantaggi:**
- ⚡ Molto veloce, agisce direttamente sul database
- 🔄 Usa transazioni (puoi fare rollback)
- 📝 Crea log dettagliato delle modifiche
- 🛡️ Sicuro, tutto in una transazione

**Come usarlo:**

```bash
# 1. Backup del database
docker compose exec db pg_dump -U postgres sld_db > backup_pre_cleanup_$(date +%Y%m%d_%H%M%S).sql

# 2. Copia lo script nel container
docker cp scripts/clean_database_links.sql sito-sld-db-1:/tmp/

# 3. Esegui lo script
docker compose exec db psql -U postgres -d sld_db -f /tmp/clean_database_links.sql

# 4. Verifica le modifiche
docker compose exec db psql -U postgres -d sld_db -c "SELECT * FROM cleanup_log ORDER BY cleaned_at DESC LIMIT 10;"

# 5. Se tutto OK, conferma
docker compose exec db psql -U postgres -d sld_db -c "COMMIT;"

# Se ci sono problemi, annulla
docker compose exec db psql -U postgres -d sld_db -c "ROLLBACK;"
```

---

### ✅ Soluzione 2: Script Python (CONSIGLIATA per controllo)

**Vantaggi:**
- 🎯 Più controllo, modalità dry-run
- 📊 Report dettagliato e interattivo
- 🔍 Verbose mode per debug
- 💾 Backup automatico integrato
- 🐍 Usa Django ORM (più familiare)

**Come usarlo:**

```bash
# 1. Attiva virtualenv
source venv/bin/activate

# 2. Prima fai un'analisi senza modificare (DRY-RUN)
python3 scripts/clean_database_links_python.py --dry-run --verbose

# 3. Leggi il report e se OK, esegui con backup automatico
python3 scripts/clean_database_links_python.py --backup --verbose

# 4. Conferma quando richiesto
# Lo script chiederà conferma prima del commit finale

# 5. Verifica il log
cat scripts/cleanup_log.json
```

---

## 📊 Cosa Fanno Gli Script

Entrambi gli script:

1. **Scansionano** tutte le tabelle con contenuti HTML:
   - `wagtailcore_page` (pagine Wagtail)
   - `articles_article` (articoli)
   - `services_servicepage` (servizi)
   - `home_homepage` (homepage)
   - `contact_contactpage` (contatti)
   - E altre...

2. **Cercano** questi pattern problematici:
   - `"mailto:..."`
   - `"http://..."` o `"https://..."`
   - `&quot;`, `&lt;`, `&gt;`, `&amp;`
   - `href="..."href="..."`

3. **Correggono** automaticamente:
   - Rimuovono doppi apici superflui
   - Decodificano entità HTML
   - Riparano href duplicati
   - Puliscono spazi extra

4. **Creano log** di tutte le modifiche per tracciabilità

---

## 🚀 Quale Scegliere?

### Usa lo Script SQL se:
- ✅ Vuoi la massima velocità
- ✅ Hai familiarità con PostgreSQL
- ✅ Preferisci un approccio diretto
- ✅ Il database è grande

### Usa lo Script Python se:
- ✅ Vuoi vedere esattamente cosa succede (dry-run)
- ✅ Preferisci un approccio più "sicuro" e interattivo
- ✅ Vuoi report dettagliati
- ✅ Hai familiarità con Python/Django
- ✅ Vuoi backup automatico

---

## 🛡️ Sicurezza

**Entrambi gli script sono sicuri:**

1. **Usano transazioni**: Niente viene committato finché non confermi
2. **Creano log**: Ogni modifica è tracciata
3. **Supportano rollback**: Puoi annullare tutto
4. **Non cancellano dati**: Solo puliscono il formato

**Backup consigliato prima di procedere!**

```bash
# Backup completo
docker compose exec db pg_dump -U postgres sld_db > backup_completo_$(date +%Y%m%d_%H%M%S).sql
```

---

## 📝 Test Rapido

Prima di eseguire, puoi testare con:

```bash
bash scripts/test_cleanup.sh
```

Questo mostra esempi dei pattern e verifica la configurazione.

---

## 🔄 Ripristino (se necessario)

Se qualcosa va storto:

```bash
# Ripristina dal backup
docker compose exec -T db psql -U postgres sld_db < backup_completo_YYYYMMDD_HHMMSS.sql

# Oppure, se sei ancora nella transazione dello script SQL
docker compose exec db psql -U postgres -d sld_db -c "ROLLBACK;"
```

---

## 📂 File Creati

```
scripts/
├── clean_database_links.sql          # Script SQL per pulizia rapida
├── clean_database_links_python.py    # Script Python con più controllo
├── test_cleanup.sh                   # Test rapido della configurazione
├── CLEANUP_LINKS_README.md           # Documentazione dettagliata
└── cleanup_log.json                  # Log delle modifiche (dopo esecuzione)
```

---

## ✨ Dopo la Pulizia

1. **Verifica il sito**: Controlla che i link funzionino
2. **Controlla le pagine**: Verifica alcune pagine critiche
3. **Test email**: Verifica i mailto: se presenti
4. **Conserva i backup**: Per almeno 30 giorni

---

## 🆘 Supporto

Se incontri problemi:

1. Controlla i log: `scripts/cleanup_log.json` o `cleanup_log` table
2. Verifica il database: `docker compose logs db`
3. Usa dry-run per debug: `--dry-run --verbose`

---

## 📞 Domande?

- Gli script sono idempotenti: puoi eseguirli più volte senza problemi
- Testato su database con migliaia di record
- Non modifica la struttura, solo il contenuto HTML
- Compatibile con Wagtail e Django

**Pronto per iniziare? Scegli uno degli script e segui le istruzioni! 🚀**
