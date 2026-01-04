#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Script di Verifica Produzione - Studio Legale Wagtail CMS
# ═══════════════════════════════════════════════════════════════════════════
# Esegui con: ./2_verifiche.sh
# Richiede: curl, openssl, dig
# ═══════════════════════════════════════════════════════════════════════════

# Non usare set -e per permettere al script di continuare

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAZIONE - MODIFICA QUESTI VALORI PER IL TUO PROGETTO
# ═══════════════════════════════════════════════════════════════════════════

# Dominio principale (senza www)
DOMAIN="example.com"

# Base URL (di solito https://DOMAIN)
BASE_URL="https://${DOMAIN}"

# ═══════════════════════════════════════════════════════════════════════════
# FINE CONFIGURAZIONE - NON MODIFICARE SOTTO QUESTA RIGA
# ═══════════════════════════════════════════════════════════════════════════

# Domini derivati
DOMAIN_WWW="www.${DOMAIN}"
DOMAIN_NAKED="${DOMAIN}"

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Flag curl per ignorare errori SSL temporanei
CURL_OPTS="-sk"

# Contatori
PASS=0
FAIL=0
WARN=0

# Funzioni helper
print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_section() {
    echo ""
    echo -e "${CYAN}▶ $1${NC}"
    echo -e "${CYAN}───────────────────────────────────────────────────────────────${NC}"
}

pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "  ${RED}✗${NC} $1"
    FAIL=$((FAIL + 1))
}

warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    WARN=$((WARN + 1))
}

info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

# ═══════════════════════════════════════════════════════════════════════════
# 1. DNS E CONNETTIVITÀ
# ═══════════════════════════════════════════════════════════════════════════
check_dns() {
    print_header "1. DNS E CONNETTIVITÀ"
    
    print_section "Risoluzione DNS"
    
    # DNS www
    WWW_IP=$(dig +short ${DOMAIN_WWW} | tail -1)
    if [ -n "$WWW_IP" ]; then
        pass "${DOMAIN_WWW} → ${WWW_IP}"
    else
        fail "${DOMAIN_WWW} non risolve"
    fi
    
    # DNS naked
    NAKED_IP=$(dig +short ${DOMAIN_NAKED} | tail -1)
    if [ -n "$NAKED_IP" ]; then
        pass "${DOMAIN_NAKED} → ${NAKED_IP}"
    else
        fail "${DOMAIN_NAKED} non risolve"
    fi
    
    # Confronto IP
    if [ "$WWW_IP" = "$NAKED_IP" ]; then
        info "Entrambi i domini puntano allo stesso IP"
    else
        warn "I domini puntano a IP diversi (www: ${WWW_IP}, naked: ${NAKED_IP})"
    fi
    
    print_section "Redirect HTTP → HTTPS"
    
    # Test redirect HTTP
    HTTP_RESPONSE=$(curl $CURL_OPTS -I -L --max-redirs 0 "http://${DOMAIN_NAKED}/" 2>/dev/null)
    HTTP_CODE=$(echo "$HTTP_RESPONSE" | head -1 | awk '{print $2}')
    
    if [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        REDIRECT_LOC=$(echo "$HTTP_RESPONSE" | grep -i "^location:" | head -1 | tr -d '\r')
        if echo "$REDIRECT_LOC" | grep -qi "https://"; then
            pass "HTTP → HTTPS redirect attivo (${HTTP_CODE})"
        else
            warn "Redirect presente ma non verso HTTPS"
        fi
    else
        fail "HTTP non redireziona a HTTPS (code: ${HTTP_CODE})"
    fi
    
    print_section "Redirect www → naked"
    
    # Test redirect www domain
    WWW_RESPONSE=$(curl $CURL_OPTS -I -L --max-redirs 0 "https://${DOMAIN_WWW}/" 2>/dev/null)
    WWW_CODE=$(echo "$WWW_RESPONSE" | head -1 | awk '{print $2}')
    WWW_LOC=$(echo "$WWW_RESPONSE" | grep -i "^location:" | head -1 | tr -d '\r')
    
    if [ "$WWW_CODE" = "301" ]; then
        if echo "$WWW_LOC" | grep -q "${DOMAIN_NAKED}"; then
            pass "www → naked redirect attivo (301)"
        else
            warn "Redirect 301 ma non verso naked domain"
            info "Location: ${WWW_LOC:-nessuno}"
        fi
    elif [ "$WWW_CODE" = "200" ]; then
        fail "www serve contenuto invece di redirect (SEO: contenuto duplicato!)"
    else
        warn "www restituisce code ${WWW_CODE}"
        info "Location: ${WWW_LOC:-nessuno}"
    fi
    
    print_section "Tempo di risposta (TTFB)"
    
    TTFB=$(curl $CURL_OPTS -o /dev/null -w "%{time_starttransfer}" "${BASE_URL}/" 2>/dev/null)
    TTFB_MS=$(echo "$TTFB * 1000" | bc 2>/dev/null || echo "N/A")
    
    if [ "$TTFB_MS" != "N/A" ]; then
        TTFB_INT=${TTFB_MS%.*}
        if [ "$TTFB_INT" -lt 500 ]; then
            pass "TTFB: ${TTFB_MS}ms (< 500ms)"
        elif [ "$TTFB_INT" -lt 1000 ]; then
            warn "TTFB: ${TTFB_MS}ms (500-1000ms)"
        else
            fail "TTFB: ${TTFB_MS}ms (> 1000ms - troppo lento)"
        fi
    else
        info "TTFB: ${TTFB}s"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. SSL/TLS
# ═══════════════════════════════════════════════════════════════════════════
check_ssl() {
    print_header "2. SSL/TLS"
    
    print_section "Certificato SSL (naked domain)"
    
    # Ottieni info certificato dal naked domain (quello principale)
    CERT_INFO=$(echo | openssl s_client -servername ${DOMAIN_NAKED} -connect ${DOMAIN_NAKED}:443 2>/dev/null | openssl x509 -noout -dates -subject 2>/dev/null)
    
    if [ -n "$CERT_INFO" ]; then
        # Scadenza
        EXPIRY=$(echo "$CERT_INFO" | grep "notAfter" | cut -d= -f2)
        if [ -n "$EXPIRY" ]; then
            # Prova prima formato macOS, poi Linux
            EXPIRY_EPOCH=$(date -j -f "%b %d %T %Y %Z" "$EXPIRY" "+%s" 2>/dev/null || date -d "$EXPIRY" "+%s" 2>/dev/null)
            NOW_EPOCH=$(date "+%s")
            
            if [ -n "$EXPIRY_EPOCH" ] && [ -n "$NOW_EPOCH" ]; then
                DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
                
                if [ "$DAYS_LEFT" -gt 30 ]; then
                    pass "Certificato valido (scade tra ${DAYS_LEFT} giorni)"
                elif [ "$DAYS_LEFT" -gt 7 ]; then
                    warn "Certificato scade tra ${DAYS_LEFT} giorni!"
                else
                    fail "Certificato scade tra ${DAYS_LEFT} giorni! RINNOVO URGENTE"
                fi
            else
                info "Scadenza: ${EXPIRY}"
            fi
        fi
        
        # Subject
        SUBJECT=$(echo "$CERT_INFO" | grep "subject" | sed 's/subject=//')
        info "Subject: ${SUBJECT}"
        
        # Verifica che il CN contenga il dominio configurato
        DOMAIN_BASE="${DOMAIN%%.*}"
        if echo "$SUBJECT" | grep -qi "$DOMAIN_BASE"; then
            pass "Certificato emesso per il dominio corretto"
        else
            fail "Certificato NON emesso per ${DOMAIN}!"
        fi
    else
        fail "Impossibile ottenere info certificato"
    fi
    
    print_section "Versione TLS"
    
    # Test TLS 1.3
    TLS13=$(echo | openssl s_client -tls1_3 -connect ${DOMAIN_NAKED}:443 2>&1 | grep -c "TLSv1.3" || echo "0")
    if [ "$TLS13" -gt 0 ]; then
        pass "TLS 1.3 supportato"
    else
        warn "TLS 1.3 non supportato"
    fi
    
    # Test TLS 1.2
    TLS12=$(echo | openssl s_client -tls1_2 -connect ${DOMAIN_NAKED}:443 2>&1 | grep -c "TLSv1.2" || echo "0")
    if [ "$TLS12" -gt 0 ]; then
        pass "TLS 1.2 supportato"
    else
        fail "TLS 1.2 non supportato"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 3. SECURITY HEADERS
# ═══════════════════════════════════════════════════════════════════════════
check_security_headers() {
    print_header "3. SECURITY HEADERS"
    
    HEADERS=$(curl $CURL_OPTS -I "${BASE_URL}/" 2>/dev/null)
    
    print_section "Headers di Sicurezza"
    
    # HSTS
    if echo "$HEADERS" | grep -qi "strict-transport-security"; then
        HSTS_VALUE=$(echo "$HEADERS" | grep -i "strict-transport-security" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
        pass "HSTS: ${HSTS_VALUE}"
    else
        fail "HSTS mancante (Strict-Transport-Security)"
    fi
    
    # X-Content-Type-Options
    if echo "$HEADERS" | grep -qi "x-content-type-options"; then
        pass "X-Content-Type-Options presente"
    else
        warn "X-Content-Type-Options mancante"
    fi
    
    # X-Frame-Options
    if echo "$HEADERS" | grep -qi "x-frame-options"; then
        XFO=$(echo "$HEADERS" | grep -i "x-frame-options" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
        pass "X-Frame-Options: ${XFO}"
    else
        warn "X-Frame-Options mancante (clickjacking)"
    fi
    
    # X-XSS-Protection
    if echo "$HEADERS" | grep -qi "x-xss-protection"; then
        pass "X-XSS-Protection presente"
    else
        info "X-XSS-Protection mancante (deprecato nei browser moderni)"
    fi
    
    # Referrer-Policy
    if echo "$HEADERS" | grep -qi "referrer-policy"; then
        RP=$(echo "$HEADERS" | grep -i "referrer-policy" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
        pass "Referrer-Policy: ${RP}"
    else
        warn "Referrer-Policy mancante"
    fi
    
    # Content-Security-Policy
    if echo "$HEADERS" | grep -qi "content-security-policy"; then
        pass "Content-Security-Policy presente"
    else
        warn "Content-Security-Policy mancante"
    fi
    
    # Permissions-Policy
    if echo "$HEADERS" | grep -qi "permissions-policy"; then
        pass "Permissions-Policy presente"
    else
        info "Permissions-Policy mancante (opzionale)"
    fi
    
    print_section "Server Header (Information Disclosure)"
    
    SERVER_HEADER=$(echo "$HEADERS" | grep -i "^server:" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
    if [ -n "$SERVER_HEADER" ]; then
        if echo "$SERVER_HEADER" | grep -qiE "nginx/[0-9]|apache/[0-9]|gunicorn"; then
            warn "Server header espone versione: ${SERVER_HEADER}"
        else
            info "Server: ${SERVER_HEADER}"
        fi
    else
        pass "Server header nascosto"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 4. FILE STATICI
# ═══════════════════════════════════════════════════════════════════════════
check_static_files() {
    print_header "4. FILE STATICI"
    
    print_section "Risorse statiche principali"
    
    # Homepage per trovare CSS/JS
    HTML=$(curl $CURL_OPTS "${BASE_URL}/" 2>/dev/null)
    
    # Cerca primo CSS
    CSS_URL=$(echo "$HTML" | grep -oE 'href="[^"]+\.css[^"]*"' | head -1 | sed 's/href="//;s/"$//')
    if [ -n "$CSS_URL" ]; then
        if [[ ! "$CSS_URL" =~ ^https?:// ]]; then
            CSS_URL="${BASE_URL}${CSS_URL}"
        fi
        CSS_CODE=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "$CSS_URL" 2>/dev/null)
        if [ "$CSS_CODE" = "200" ]; then
            pass "CSS accessibile: ${CSS_URL##*/}"
        else
            fail "CSS non accessibile (${CSS_CODE}): ${CSS_URL##*/}"
        fi
    else
        info "Nessun CSS esterno trovato (potrebbe usare Tailwind CDN)"
    fi
    
    # Logo
    LOGO_URL=$(echo "$HTML" | grep -oE 'src="[^"]*logo[^"]*\.(svg|png|jpg)[^"]*"' | head -1 | sed 's/src="//;s/"$//' || echo "")
    if [ -n "$LOGO_URL" ]; then
        if [[ ! "$LOGO_URL" =~ ^https?:// ]]; then
            LOGO_URL="${BASE_URL}${LOGO_URL}"
        fi
        LOGO_CODE=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "$LOGO_URL" 2>/dev/null)
        if [ "$LOGO_CODE" = "200" ]; then
            pass "Logo accessibile"
        else
            fail "Logo non accessibile (${LOGO_CODE})"
        fi
    fi
    
    # Favicon
    FAVICON_CODE=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "${BASE_URL}/favicon.ico" 2>/dev/null)
    if [ "$FAVICON_CODE" = "200" ]; then
        pass "Favicon /favicon.ico accessibile"
    else
        # Prova altri path
        FAVICON_CODE2=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "${BASE_URL}/static/favicon.ico" 2>/dev/null)
        if [ "$FAVICON_CODE2" = "200" ]; then
            pass "Favicon accessibile in /static/"
        else
            warn "Favicon non trovata in path standard"
        fi
    fi
    
    print_section "Compressione"
    
    # Test gzip
    GZIP_TEST=$(curl $CURL_OPTS -H "Accept-Encoding: gzip" -I "${BASE_URL}/" 2>/dev/null | grep -i "content-encoding")
    if echo "$GZIP_TEST" | grep -qi "gzip\|br"; then
        pass "Compressione attiva: $(echo $GZIP_TEST | tr -d '\r' | xargs)"
    else
        warn "Compressione gzip/brotli non rilevata"
    fi
    
    print_section "Caching Headers"
    
    # Test su risorsa statica
    if [ -n "$CSS_URL" ]; then
        CACHE_HEADERS=$(curl $CURL_OPTS -I "$CSS_URL" 2>/dev/null)
        
        if echo "$CACHE_HEADERS" | grep -qi "cache-control"; then
            CC=$(echo "$CACHE_HEADERS" | grep -i "cache-control" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
            pass "Cache-Control su CSS: ${CC}"
        else
            warn "Cache-Control mancante su risorse statiche"
        fi
        
        if echo "$CACHE_HEADERS" | grep -qi "etag"; then
            pass "ETag presente"
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 5. SEO & META TAGS
# ═══════════════════════════════════════════════════════════════════════════
check_seo() {
    print_header "5. SEO & META TAGS"
    
    HTML=$(curl $CURL_OPTS "${BASE_URL}/" 2>/dev/null)
    
    print_section "Meta Tags Homepage"
    
    # Title - cerca il tag title
    TITLE=$(echo "$HTML" | grep -oE '<title[^>]*>[^<]+</title>' | sed 's/<title[^>]*>//;s/<\/title>//' | head -1 | xargs)
    if [ -n "$TITLE" ]; then
        TITLE_LEN=${#TITLE}
        if [ "$TITLE_LEN" -le 60 ]; then
            pass "Title (${TITLE_LEN} chars): ${TITLE:0:60}"
        else
            warn "Title troppo lungo (${TITLE_LEN} chars): ${TITLE:0:60}..."
        fi
    else
        fail "Tag <title> mancante"
    fi
    
    # Meta description
    META_DESC=$(echo "$HTML" | grep -oE 'name="description" content="[^"]*"' | sed 's/name="description" content="//;s/"$//' | head -1)
    if [ -n "$META_DESC" ]; then
        DESC_LEN=${#META_DESC}
        if [ "$DESC_LEN" -le 160 ]; then
            pass "Meta description (${DESC_LEN} chars)"
        else
            warn "Meta description troppo lunga (${DESC_LEN} chars)"
        fi
    else
        fail "Meta description mancante"
    fi
    
    # Robots
    if echo "$HTML" | grep -qi 'name="robots"'; then
        ROBOTS=$(echo "$HTML" | grep -oE 'name="robots" content="[^"]*"' | sed 's/name="robots" content="//;s/"$//' | head -1)
        if echo "$ROBOTS" | grep -qi "noindex"; then
            fail "robots: ${ROBOTS} (ATTENZIONE: noindex!)"
        else
            pass "Meta robots: ${ROBOTS}"
        fi
    else
        info "Meta robots non specificato (default: index,follow)"
    fi
    
    # Canonical
    CANONICAL=$(echo "$HTML" | grep -oE 'rel="canonical" href="[^"]*"' | sed 's/rel="canonical" href="//;s/"$//' | head -1)
    if [ -n "$CANONICAL" ]; then
        pass "Canonical: ${CANONICAL}"
    else
        warn "Canonical URL mancante"
    fi
    
    print_section "Open Graph"
    
    # og:title
    if echo "$HTML" | grep -qi 'property="og:title"'; then
        pass "og:title presente"
    else
        warn "og:title mancante"
    fi
    
    # og:description
    if echo "$HTML" | grep -qi 'property="og:description"'; then
        pass "og:description presente"
    else
        warn "og:description mancante"
    fi
    
    # og:image
    OG_IMAGE=$(echo "$HTML" | grep -oE 'property="og:image" content="[^"]*"' | sed 's/property="og:image" content="//;s/"$//' | head -1)
    if [ -n "$OG_IMAGE" ]; then
        pass "og:image: ${OG_IMAGE:0:50}..."
        # Verifica accessibilità
        IMG_CODE=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "$OG_IMAGE" 2>/dev/null)
        if [ "$IMG_CODE" = "200" ]; then
            pass "og:image accessibile"
        else
            fail "og:image non accessibile (${IMG_CODE})"
        fi
    else
        warn "og:image mancante"
    fi
    
    # og:type
    if echo "$HTML" | grep -qi 'property="og:type"'; then
        pass "og:type presente"
    else
        info "og:type mancante"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 6. SCHEMA.ORG JSON-LD
# ═══════════════════════════════════════════════════════════════════════════
check_schema_org() {
    print_header "6. SCHEMA.ORG JSON-LD"
    
    print_section "Homepage - LegalService"
    
    HTML=$(curl $CURL_OPTS "${BASE_URL}/" 2>/dev/null)
    
    # Estrai JSON-LD - cerca script con type application/ld+json
    JSONLD=$(echo "$HTML" | tr '\n' ' ' | grep -oE '<script type="application/ld\+json">[^<]+</script>' | sed 's/<script type="application\/ld+json">//;s/<\/script>//' | head -1)
    
    if [ -n "$JSONLD" ]; then
        pass "JSON-LD trovato"
        
        # Verifica LegalService
        if echo "$JSONLD" | grep -q '"LegalService"'; then
            pass "LegalService presente"
        else
            warn "LegalService non trovato"
        fi
        
        # Verifica address diretto su LegalService
        if echo "$JSONLD" | grep -q '"address"'; then
            pass "Proprietà 'address' presente"
        else
            fail "LegalService SENZA 'address' diretto"
        fi
        
        # Verifica postalCode
        if echo "$JSONLD" | grep -q '"postalCode"'; then
            POSTAL_CODE=$(echo "$JSONLD" | grep -oE '"postalCode"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1)
            if echo "$POSTAL_CODE" | grep -q '""'; then
                fail "postalCode presente ma VUOTO (compila CAP in admin)"
            else
                pass "postalCode presente: ${POSTAL_CODE}"
            fi
        else
            fail "postalCode MANCANTE nel JSON-LD"
        fi
        
        # Verifica addressRegion
        if echo "$JSONLD" | grep -q '"addressRegion"'; then
            pass "addressRegion presente"
        else
            warn "addressRegion mancante"
        fi
        
    else
        fail "Nessun JSON-LD trovato nella homepage"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 7. RISORSE SEO
# ═══════════════════════════════════════════════════════════════════════════
check_seo_resources() {
    print_header "7. RISORSE SEO"
    
    print_section "robots.txt"
    
    ROBOTS_CODE=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "${BASE_URL}/robots.txt" 2>/dev/null)
    if [ "$ROBOTS_CODE" = "200" ]; then
        ROBOTS_CONTENT=$(curl $CURL_OPTS "${BASE_URL}/robots.txt" 2>/dev/null)
        pass "robots.txt accessibile"
        
        if echo "$ROBOTS_CONTENT" | grep -qi "Sitemap:"; then
            SITEMAP_URL=$(echo "$ROBOTS_CONTENT" | grep -i "Sitemap:" | head -1 | awk '{print $2}' | tr -d '\r')
            pass "Sitemap dichiarata: ${SITEMAP_URL}"
            
            # Verifica che il dominio nella sitemap sia corretto
            if echo "$SITEMAP_URL" | grep -q "${DOMAIN_NAKED}"; then
                pass "Sitemap usa il dominio corretto"
            else
                fail "Sitemap usa dominio SBAGLIATO: ${SITEMAP_URL}"
            fi
        else
            warn "Sitemap non dichiarata in robots.txt"
        fi
        
        if echo "$ROBOTS_CONTENT" | grep -E "^Disallow:[[:space:]]*/[[:space:]]*$" | grep -qv "#"; then
            fail "ATTENZIONE: Disallow: / blocca tutto il sito!"
        fi
    else
        warn "robots.txt non trovato (${ROBOTS_CODE})"
    fi
    
    print_section "sitemap.xml"
    
    SITEMAP_CODE=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "${BASE_URL}/sitemap.xml" 2>/dev/null)
    if [ "$SITEMAP_CODE" = "200" ]; then
        SITEMAP=$(curl $CURL_OPTS "${BASE_URL}/sitemap.xml" 2>/dev/null)
        URL_COUNT=$(echo "$SITEMAP" | grep -c "<loc>" || echo "0")
        pass "sitemap.xml accessibile (${URL_COUNT} URLs)"
        
        # Verifica che gli URL nella sitemap usino il dominio corretto
        FIRST_URL=$(echo "$SITEMAP" | grep -oE "<loc>[^<]*</loc>" | head -1 | sed 's/<loc>//;s/<\/loc>//')
        if echo "$FIRST_URL" | grep -q "${DOMAIN_NAKED}"; then
            pass "URLs nella sitemap usano il dominio corretto"
        else
            fail "URLs nella sitemap usano dominio SBAGLIATO: ${FIRST_URL}"
        fi
    else
        warn "sitemap.xml non trovato (${SITEMAP_CODE})"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 8. PAGINE CRITICHE (DINAMICHE DA HOMEPAGE)
# ═══════════════════════════════════════════════════════════════════════════
check_critical_pages() {
    print_header "8. PAGINE CRITICHE (da Homepage)"
    
    print_section "Estrazione link interni"
    
    # Scarica homepage e estrai link interni
    HTML=$(curl $CURL_OPTS "${BASE_URL}/" 2>/dev/null)
    
    # Estrai tutti i link interni (che iniziano con /)
    # Escludi anchor (#), static, media, admin
    ALL_LINKS=$(echo "$HTML" | grep -oE 'href="(/[^"]*)"' | sed 's/href="//;s/"$//' | grep -v '#' | grep -v '/static' | grep -v '/media' | grep -v '/admin' | grep -v 'favicon' | sort -u)
    
    # Prendi solo i link "principali" (non sotto-pagine troppo profonde)
    # Conta max 2 livelli di profondità
    MAIN_LINKS=$(echo "$ALL_LINKS" | awk -F'/' 'NF<=4' | sort -u)
    
    if [ -n "$MAIN_LINKS" ]; then
        LINK_COUNT=$(echo "$MAIN_LINKS" | wc -l | xargs)
        info "Link interni trovati: ${LINK_COUNT}"
    else
        warn "Nessun link interno trovato"
        MAIN_LINKS="/ /contatti/ /privacy/"
    fi
    
    print_section "Status Code Pagine"
    
    # Testa ogni pagina
    for PAGE in $MAIN_LINKS; do
        CODE=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "${BASE_URL}${PAGE}" 2>/dev/null)
        if [ "$CODE" = "200" ]; then
            pass "${PAGE} → 200 OK"
        elif [ "$CODE" = "301" ] || [ "$CODE" = "302" ]; then
            REDIR_LOC=$(curl $CURL_OPTS -I "${BASE_URL}${PAGE}" 2>/dev/null | grep -i "^location:" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
            info "${PAGE} → ${CODE} → ${REDIR_LOC}"
        elif [ "$CODE" = "404" ]; then
            fail "${PAGE} → 404 Not Found"
        else
            fail "${PAGE} → ${CODE}"
        fi
    done
    
    print_section "Pagina 404 personalizzata"
    
    NOTFOUND_HTML=$(curl $CURL_OPTS "${BASE_URL}/pagina-che-non-esiste-12345/" 2>/dev/null)
    NOTFOUND_CODE=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "${BASE_URL}/pagina-che-non-esiste-12345/" 2>/dev/null)
    
    if [ "$NOTFOUND_CODE" = "404" ]; then
        if echo "$NOTFOUND_HTML" | grep -qi "404\|non trovata\|not found"; then
            pass "Pagina 404 personalizzata"
        else
            info "404 restituito ma pagina non sembra personalizzata"
        fi
    else
        warn "Pagina inesistente restituisce ${NOTFOUND_CODE} invece di 404"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 9. PERFORMANCE SERVER
# ═══════════════════════════════════════════════════════════════════════════
check_nginx_performance() {
    print_header "9. PERFORMANCE SERVER"
    
    HEADERS=$(curl $CURL_OPTS -I "${BASE_URL}/" 2>/dev/null)
    
    print_section "HTTP/2"
    
    H2_CHECK=$(curl $CURL_OPTS -I --http2 "${BASE_URL}/" 2>/dev/null | head -1)
    if echo "$H2_CHECK" | grep -qi "HTTP/2"; then
        pass "HTTP/2 attivo"
    else
        warn "HTTP/2 non rilevato (potrebbe essere HTTP/1.1)"
    fi
    
    print_section "Keep-Alive"
    
    if echo "$HEADERS" | grep -qi "keep-alive\|connection: keep-alive"; then
        pass "Keep-Alive attivo"
    else
        info "Keep-Alive non esplicitamente dichiarato"
    fi
    
    print_section "Vary Header"
    
    if echo "$HEADERS" | grep -qi "vary:"; then
        VARY=$(echo "$HEADERS" | grep -i "vary:" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
        pass "Vary: ${VARY}"
    else
        info "Vary header non presente"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 10. CONFRONTO DOMINI
# ═══════════════════════════════════════════════════════════════════════════
check_domain_comparison() {
    print_header "10. CONFRONTO DOMINI"
    
    print_section "www.${DOMAIN}"
    
    WWW_RESPONSE=$(curl $CURL_OPTS -I "https://${DOMAIN_WWW}/" 2>/dev/null)
    WWW_CODE=$(echo "$WWW_RESPONSE" | head -1 | awk '{print $2}')
    info "Status: ${WWW_CODE}"
    
    if [ "$WWW_CODE" = "301" ]; then
        WWW_LOC=$(echo "$WWW_RESPONSE" | grep -i "^location:" | head -1 | cut -d: -f2- | tr -d '\r' | xargs)
        info "Redirect a: ${WWW_LOC}"
        if echo "$WWW_LOC" | grep -q "${DOMAIN_NAKED}"; then
            pass "Redirect www → naked configurato correttamente (301)"
        fi
    elif [ "$WWW_CODE" = "200" ]; then
        fail "www serve contenuto direttamente (dovrebbe fare redirect)"
    fi
    
    print_section "${DOMAIN} (naked)"
    
    NAKED_CODE=$(curl $CURL_OPTS -o /dev/null -w "%{http_code}" "https://${DOMAIN_NAKED}/" 2>/dev/null)
    info "Status: ${NAKED_CODE}"
    
    if [ "$NAKED_CODE" = "200" ]; then
        pass "Naked domain serve contenuto correttamente"
    else
        fail "Naked domain non restituisce 200 (${NAKED_CODE})"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
main() {
    echo ""
    echo -e "${BOLD}${CYAN}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║   VERIFICA PRODUZIONE - Studio Legale                         ║"
    echo "  ║   $(date '+%Y-%m-%d %H:%M:%S')                                      ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Mostra configurazione
    echo -e "${CYAN}Configurazione:${NC}"
    echo "  Dominio:     ${DOMAIN}"
    echo "  Base URL:    ${BASE_URL}"
    echo ""
    
    # Verifica dipendenze
    for cmd in curl openssl dig bc; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${YELLOW}Attenzione: $cmd non trovato, alcune verifiche potrebbero fallire${NC}"
        fi
    done
    
    # Esegui tutti i check
    check_dns
    check_ssl
    check_security_headers
    check_static_files
    check_seo
    check_schema_org
    check_seo_resources
    check_critical_pages
    check_nginx_performance
    check_domain_comparison
    
    # Riepilogo finale
    print_header "RIEPILOGO"
    echo ""
    echo -e "  ${GREEN}✓ Passati:${NC}  ${PASS}"
    echo -e "  ${YELLOW}⚠ Warning:${NC} ${WARN}"
    echo -e "  ${RED}✗ Falliti:${NC}  ${FAIL}"
    echo ""
    
    TOTAL=$((PASS + WARN + FAIL))
    if [ "$TOTAL" -gt 0 ]; then
        SCORE=$(( (PASS * 100) / TOTAL ))
        echo -e "  ${BOLD}Score: ${SCORE}%${NC}"
    fi
    
    if [ "$FAIL" -gt 0 ]; then
        echo ""
        echo -e "  ${RED}Ci sono ${FAIL} problemi da risolvere!${NC}"
        exit 1
    elif [ "$WARN" -gt 0 ]; then
        echo ""
        echo -e "  ${YELLOW}Ci sono ${WARN} warning da valutare.${NC}"
        exit 0
    else
        echo ""
        echo -e "  ${GREEN}Tutto OK! 🎉${NC}"
        exit 0
    fi
}

main "$@"
