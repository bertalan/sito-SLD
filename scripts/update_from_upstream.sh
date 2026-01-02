#!/bin/bash
#
# Script per aggiornare il progetto dal template upstream
# Uso: ./scripts/update_from_upstream.sh
#

set -e

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Aggiornamento da Template Upstream                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verifica che siamo in un repo git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Errore: non sei in un repository git${NC}"
    exit 1
fi

# Verifica che upstream esista
if ! git remote | grep -q "upstream"; then
    echo -e "${YELLOW}⚠️  Remote 'upstream' non configurato.${NC}"
    echo ""
    read -p "Vuoi aggiungerlo ora? (s/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        git remote add upstream https://github.com/bertalan/sito-SLD.git
        echo -e "${GREEN}✓ Upstream aggiunto${NC}"
    else
        echo -e "${RED}Operazione annullata${NC}"
        exit 1
    fi
fi

# Verifica modifiche non committate
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Hai modifiche non committate.${NC}"
    echo ""
    read -p "Vuoi fare stash delle modifiche? (s/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        git stash push -m "Auto-stash prima di update $(date +%Y%m%d-%H%M%S)"
        echo -e "${GREEN}✓ Modifiche salvate in stash${NC}"
        STASHED=true
    else
        echo -e "${RED}Committa o stasha le modifiche prima di procedere${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}📥 Fetch da upstream...${NC}"
git fetch upstream

# Mostra cosa c'è di nuovo
echo ""
echo -e "${BLUE}📋 Nuovi commit disponibili:${NC}"
echo "─────────────────────────────────────────"
COMMITS=$(git log --oneline main..upstream/main 2>/dev/null | head -20)
if [ -z "$COMMITS" ]; then
    echo -e "${GREEN}✓ Sei già aggiornato!${NC}"
    
    # Ripristina stash se fatto
    if [ "$STASHED" = true ]; then
        echo -e "${BLUE}📤 Ripristino modifiche da stash...${NC}"
        git stash pop
    fi
    exit 0
fi
echo "$COMMITS"
echo "─────────────────────────────────────────"

# Mostra CHANGELOG se disponibile
echo ""
echo -e "${BLUE}📝 Ultime modifiche dal CHANGELOG:${NC}"
echo "─────────────────────────────────────────"
git show upstream/main:CHANGELOG.md 2>/dev/null | head -40 || echo "(CHANGELOG non disponibile)"
echo "─────────────────────────────────────────"

# Conferma
echo ""
read -p "Procedere con il merge? (s/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}Operazione annullata${NC}"
    
    # Ripristina stash se fatto
    if [ "$STASHED" = true ]; then
        echo -e "${BLUE}📤 Ripristino modifiche da stash...${NC}"
        git stash pop
    fi
    exit 0
fi

# Merge
echo ""
echo -e "${BLUE}🔄 Merge in corso...${NC}"
if git merge upstream/main -m "Merge upstream $(git describe --tags upstream/main 2>/dev/null || echo 'latest')"; then
    echo -e "${GREEN}✓ Merge completato con successo!${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Ci sono conflitti da risolvere.${NC}"
    echo ""
    echo "File in conflitto:"
    git diff --name-only --diff-filter=U
    echo ""
    echo -e "${BLUE}Per risolvere:${NC}"
    echo "  1. Modifica i file in conflitto"
    echo "  2. git add <file>"
    echo "  3. git commit"
    echo ""
    echo -e "${BLUE}Oppure:${NC}"
    echo "  git merge --abort  # per annullare"
    exit 1
fi

# Ripristina stash se fatto
if [ "$STASHED" = true ]; then
    echo -e "${BLUE}📤 Ripristino modifiche da stash...${NC}"
    if git stash pop; then
        echo -e "${GREEN}✓ Modifiche ripristinate${NC}"
    else
        echo -e "${YELLOW}⚠️  Conflitti nello stash. Risolvi manualmente con: git stash show -p | git apply${NC}"
    fi
fi

# Post-merge
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Aggiornamento completato!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Prossimi passi:${NC}"
echo "  1. Verifica le modifiche: git log --oneline -10"
echo "  2. Esegui le migrazioni:"
echo "     - Docker: docker compose exec web python manage.py migrate"
echo "     - Prod:   python manage.py migrate"
echo "  3. Esegui i test: python manage.py test"
echo "  4. Push: git push origin main"
echo ""
