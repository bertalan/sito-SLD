#!/bin/bash
# ===========================================
# Script di Installazione Iniziale
# Studio Legale - Wagtail CMS
# ===========================================
# Esegui questo script sul server per il primo setup
# Prerequisiti: Ubuntu/Debian con aaPanel installato
# ===========================================

set -e

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAZIONE - MODIFICA QUESTI VALORI PER IL TUO PROGETTO
# ═══════════════════════════════════════════════════════════════════════════

# Dominio principale (senza www)
DOMAIN="example.com"

# Directory applicazione dove INSTALLAREsul server
APP_DIR="/www/wwwroot/${DOMAIN}"

# Repository Git
REPO_URL="https://github.com/username/repository.git"
BRANCH="main"

# Database PostgreSQL
DB_NAME="studio_db"
DB_USER="studio_user"
DB_PASS="CHANGE_THIS_PASSWORD"

# Percorsi configurazione server (aaPanel/BT Panel)
NGINX_CONF_DIR="/www/server/panel/vhost/nginx"
GUNICORN_SERVICE="/etc/systemd/system/gunicorn_studio.service"
GUNICORN_SERVICE_NAME="gunicorn_studio"

# ═══════════════════════════════════════════════════════════════════════════
# FINE CONFIGURAZIONE - NON MODIFICARE SOTTO QUESTA RIGA
# ═══════════════════════════════════════════════════════════════════════════

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Funzioni helper
log_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

log_step() {
    echo -e "${YELLOW}[$1] $2${NC}"
}

log_ok() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
# CONTROLLI PRE-INSTALLAZIONE
# ═══════════════════════════════════════════════════════════════════════════

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Questo script deve essere eseguito come root"
        echo "  Usa: sudo bash $0"
        exit 1
    fi
}

check_aapanel() {
    if [ ! -d "/www/server/panel" ]; then
        log_warn "aaPanel non rilevato"
        echo ""
        read -p "Continuare comunque? (y/N) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_prerequisites() {
    log_step "PRE" "Verifica prerequisiti..."
    
    local missing=()
    
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    command -v pip3 >/dev/null 2>&1 || missing+=("python3-pip")
    command -v git >/dev/null 2>&1 || missing+=("git")
    command -v psql >/dev/null 2>&1 || missing+=("postgresql")
    command -v nginx >/dev/null 2>&1 || missing+=("nginx")
    
    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Pacchetti mancanti: ${missing[*]}"
        echo ""
        echo "  Installa con:"
        echo "  apt update && apt install -y ${missing[*]}"
        exit 1
    fi
    
    log_ok "Tutti i prerequisiti presenti"
}

# ═══════════════════════════════════════════════════════════════════════════
# FUNZIONI DI INSTALLAZIONE
# ═══════════════════════════════════════════════════════════════════════════

install_database() {
    log_step "1/8" "Configurazione PostgreSQL..."
    
    # Verifica se database esiste già
    if sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        log_info "Database '$DB_NAME' già esistente"
        return 0
    fi
    
    # Crea utente
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || log_info "Utente già esistente"
    
    # Crea database
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || log_info "Database già esistente"
    
    # Permessi
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    
    log_ok "Database '$DB_NAME' configurato"
}

install_app_directory() {
    log_step "2/8" "Creazione directory applicazione..."
    
    if [ -d "$APP_DIR" ]; then
        log_info "Directory '$APP_DIR' già esistente"
    else
        mkdir -p "$APP_DIR"
        log_ok "Directory creata: $APP_DIR"
    fi
}

install_git_clone() {
    log_step "3/8" "Clone repository..."
    
    cd "$APP_DIR"
    
    if [ -d ".git" ]; then
        log_info "Repository già clonato, aggiorno..."
        git fetch origin
        git reset --hard origin/$BRANCH
    else
        log_info "Clonazione da $REPO_URL..."
        git clone "$REPO_URL" .
        git checkout $BRANCH
    fi
    
    log_ok "Codice scaricato: $(git rev-parse --short HEAD)"
}

install_virtualenv() {
    log_step "4/8" "Creazione virtualenv..."
    
    cd "$APP_DIR"
    
    if [ -f "venv/bin/activate" ]; then
        log_info "Virtualenv già esistente"
    else
        python3 -m venv venv
        log_ok "Virtualenv creato"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    log_ok "Dipendenze Python installate"
}

install_env_file() {
    log_step "5/8" "Configurazione file .env..."
    
    cd "$APP_DIR"
    
    if [ -f ".env" ]; then
        log_info "File .env già esistente"
        return 0
    fi
    
    if [ -f "deploy/env.production.example" ]; then
        cp deploy/env.production.example .env
        
        # Sostituisci placeholder
        sed -i "s/your_db_name/$DB_NAME/g" .env 2>/dev/null || sed -i '' "s/your_db_name/$DB_NAME/g" .env
        sed -i "s/your_db_user/$DB_USER/g" .env 2>/dev/null || sed -i '' "s/your_db_user/$DB_USER/g" .env
        sed -i "s/your_db_password/$DB_PASS/g" .env 2>/dev/null || sed -i '' "s/your_db_password/$DB_PASS/g" .env
        sed -i "s/yourdomain.com/$DOMAIN/g" .env 2>/dev/null || sed -i '' "s/yourdomain.com/$DOMAIN/g" .env
        
        # Genera SECRET_KEY casuale
        SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
        sed -i "s/your-secret-key-here/$SECRET_KEY/g" .env 2>/dev/null || sed -i '' "s/your-secret-key-here/$SECRET_KEY/g" .env
        
        log_ok "File .env creato"
        log_warn "VERIFICA le impostazioni in: $APP_DIR/.env"
    else
        log_error "Template env.production.example non trovato"
        echo ""
        echo "  Crea manualmente il file .env con le variabili necessarie"
        return 1
    fi
}

install_django_setup() {
    log_step "6/8" "Setup Django (migrate + collectstatic)..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Migrazioni
    python manage.py migrate --noinput
    log_ok "Migrazioni applicate"
    
    # Collectstatic
    python manage.py collectstatic --noinput --clear 2>/dev/null || python manage.py collectstatic --noinput
    log_ok "File statici raccolti"
}

install_gunicorn_service() {
    log_step "7/8" "Configurazione servizio Gunicorn..."
    
    if [ -f "$GUNICORN_SERVICE" ]; then
        log_info "Servizio Gunicorn già configurato"
        return 0
    fi
    
    # Crea file di servizio
    cat > "$GUNICORN_SERVICE" << EOF
[Unit]
Description=Gunicorn daemon for Studio Legale
Requires=postgresql.service
After=network.target postgresql.service

[Service]
User=www
Group=www
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:$APP_DIR/gunicorn.sock sld_project.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
    
    # Attiva servizio
    systemctl daemon-reload
    systemctl enable "$GUNICORN_SERVICE_NAME"
    
    log_ok "Servizio Gunicorn installato"
}

install_superuser() {
    log_step "8/8" "Creazione superuser admin..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Controlla se esistono già superuser
    SUPERUSER_EXISTS=$(python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" 2>/dev/null || echo "False")
    
    if [ "$SUPERUSER_EXISTS" = "True" ]; then
        log_info "Superuser già esistente"
        return 0
    fi
    
    echo ""
    log_warn "Crea un superuser per l'admin:"
    python manage.py createsuperuser
}

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAZIONE NGINX (OPZIONALE)
# ═══════════════════════════════════════════════════════════════════════════

show_nginx_config() {
    log_header "CONFIGURAZIONE NGINX"
    
    echo ""
    echo -e "${CYAN}Esempio configurazione Nginx per $DOMAIN:${NC}"
    echo ""
    cat << 'EOF'
# Redirect HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER;
    return 301 https://DOMAIN_PLACEHOLDER$request_uri;
}

# Redirect www → naked domain
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.DOMAIN_PLACEHOLDER;
    
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    return 301 https://DOMAIN_PLACEHOLDER$request_uri;
}

# Main server block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;
    
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    root APP_DIR_PLACEHOLDER;
    
    location /static/ {
        alias APP_DIR_PLACEHOLDER/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias APP_DIR_PLACEHOLDER/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://unix:APP_DIR_PLACEHOLDER/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    echo ""
    echo -e "${YELLOW}Sostituisci:${NC}"
    echo "  - DOMAIN_PLACEHOLDER → $DOMAIN"
    echo "  - APP_DIR_PLACEHOLDER → $APP_DIR"
    echo "  - /path/to/... → percorso certificati SSL"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

main() {
    echo ""
    echo -e "${BOLD}${CYAN}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║   Installazione Studio Legale - Wagtail CMS                   ║"
    echo "  ║   $(date '+%Y-%m-%d %H:%M:%S')                                      ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Mostra configurazione
    echo -e "${CYAN}Configurazione:${NC}"
    echo "  Dominio:     $DOMAIN"
    echo "  App Dir:     $APP_DIR"
    echo "  Repository:  $REPO_URL"
    echo "  Branch:      $BRANCH"
    echo "  Database:    $DB_NAME"
    echo ""
    
    # Conferma
    read -p "Procedere con l'installazione? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installazione annullata."
        exit 0
    fi
    
    log_header "CONTROLLI"
    check_root
    check_aapanel
    check_prerequisites
    
    log_header "INSTALLAZIONE"
    install_database
    install_app_directory
    install_git_clone
    install_virtualenv
    install_env_file
    install_django_setup
    install_gunicorn_service
    install_superuser
    
    log_header "INSTALLAZIONE COMPLETATA"
    
    echo ""
    echo -e "${GREEN}✓ Installazione completata con successo!${NC}"
    echo ""
    echo -e "${CYAN}Prossimi passi:${NC}"
    echo ""
    echo "  1. Verifica/modifica il file .env:"
    echo -e "     ${YELLOW}nano $APP_DIR/.env${NC}"
    echo ""
    echo "  2. Configura Nginx (vedi configurazione sotto)"
    echo ""
    echo "  3. Genera certificato SSL con Let's Encrypt:"
    echo -e "     ${YELLOW}certbot certonly --webroot -w $APP_DIR -d $DOMAIN -d www.$DOMAIN${NC}"
    echo ""
    echo "  4. Avvia il servizio Gunicorn:"
    echo -e "     ${YELLOW}systemctl start $GUNICORN_SERVICE_NAME${NC}"
    echo ""
    echo "  5. Riavvia Nginx:"
    echo -e "     ${YELLOW}systemctl reload nginx${NC}"
    echo ""
    echo "  6. Accedi all'admin:"
    echo -e "     ${YELLOW}https://$DOMAIN/admin/${NC}"
    echo ""
    
    # Mostra config nginx
    show_nginx_config
}

# Esegui
main "$@"
