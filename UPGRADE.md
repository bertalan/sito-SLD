# Guida Aggiornamento da Template

Questa guida spiega come mantenere la tua installazione di produzione aggiornata con le nuove versioni del template.

## 🏗️ Architettura Consigliata

```
┌─────────────────────────────────┐
│   bertalan/sito-SLD (template)  │  ← Repository pubblico
│   upstream                      │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   tuo-repo/sito-sld-prod        │  ← Tuo repository privato
│   origin                        │
└─────────────────────────────────┘
```

## 📋 Setup Iniziale (una volta sola)

### Opzione A: Partendo dal template

```bash
# 1. Clona il template
git clone https://github.com/bertalan/sito-SLD.git mio-studio-legale
cd mio-studio-legale

# 2. Rinomina origin in upstream
git remote rename origin upstream

# 3. Aggiungi il tuo repository come origin
git remote add origin git@github.com:tuo-username/mio-studio-legale.git

# 4. Push iniziale
git push -u origin main
```

### Opzione B: Hai già un repository

```bash
cd mio-studio-legale

# Aggiungi il template come upstream
git remote add upstream https://github.com/bertalan/sito-SLD.git

# Verifica
git remote -v
# origin    git@github.com:tuo-username/mio-studio-legale.git (fetch)
# upstream  https://github.com/bertalan/sito-SLD.git (fetch)
```

## 🔄 Aggiornamento da Template

### Metodo Automatico (consigliato)

```bash
./scripts/update_from_upstream.sh
```

### Metodo Manuale

```bash
# 1. Fetch aggiornamenti
git fetch upstream

# 2. Vedi cosa c'è di nuovo
git log --oneline main..upstream/main

# 3. Leggi il CHANGELOG
curl -s https://raw.githubusercontent.com/bertalan/sito-SLD/main/CHANGELOG.md | head -50

# 4. Merge nel tuo branch
git checkout main
git merge upstream/main

# 5. Risolvi eventuali conflitti
# I conflitti tipici sono in file che hai personalizzato

# 6. Commit e push
git push origin main
```

## ⚠️ Gestione Conflitti

### File che NON dovresti modificare (core)
Questi file vengono aggiornati dal template. Evita modifiche dirette:
- `booking/*.py` (tranne configurazioni)
- `domiciliazioni/*.py`
- `home/management/commands/*.py`
- `sld_project/settings/*.py`
- Migrazioni (`*/migrations/*.py`)

### File che PUOI personalizzare
Questi sono tuoi, il template non li sovrascrive:
- `.env` (mai committato)
- `media/*` (mai committato)
- Template HTML custom in `templates/`

### File ibridi (attenzione ai conflitti)
- `sld_project/templates/*.html` - struttura dal template, contenuti tuoi
- `README.md` - potresti voler mantenere il tuo

### Risoluzione tipica

```bash
# Se hai conflitto su un file core, prendi la versione upstream
git checkout --theirs path/to/file.py

# Se hai conflitto su un file tuo, mantieni la tua versione
git checkout --ours path/to/my-custom-file.html

# Dopo aver risolto
git add .
git commit -m "Merge upstream v1.x.x"
```

## 🗄️ Migrazioni Database

Dopo ogni aggiornamento:

```bash
# Sviluppo (Docker)
docker compose exec web python manage.py migrate

# Produzione (senza Docker)
source venv/bin/activate
python manage.py migrate
```

### Se le migrazioni falliscono

1. **Conflitto migrazioni**: il template ha squashato le migrazioni
   ```bash
   # Marca come applicate senza eseguire
   python manage.py migrate <app> --fake
   ```

2. **Tabella già esiste**: migrazione già applicata manualmente
   ```bash
   python manage.py migrate <app> --fake-initial
   ```

## 📦 Aggiornamento Dipendenze

Se `requirements.txt` è cambiato:

```bash
# Docker
docker compose build --no-cache
docker compose up -d

# Produzione
pip install -r requirements.txt --upgrade
```

## 🔖 Versioning

Il template segue [Semantic Versioning](https://semver.org/):

| Versione | Significato | Azione |
|----------|-------------|--------|
| `1.0.x` → `1.0.y` | Bugfix | Aggiorna tranquillamente |
| `1.x.0` → `1.y.0` | Nuove feature | Leggi CHANGELOG, poi aggiorna |
| `x.0.0` → `y.0.0` | Breaking changes | Leggi UPGRADE notes, backup, test |

## 🛡️ Backup Prima di Aggiornare

```bash
# Database
pg_dump -U postgres dbname > backup_$(date +%Y%m%d).sql

# Media
tar -czvf media_$(date +%Y%m%d).tar.gz media/

# Codice
git stash  # se hai modifiche non committate
```

## 📞 Supporto

- **Issues**: https://github.com/bertalan/sito-SLD/issues
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Guida personalizzazione**: [CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md)
