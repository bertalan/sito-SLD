#!/bin/bash
# Script di test per verificare la pulizia dei link

echo "========================================"
echo "TEST PATTERN PROBLEMATICI"
echo "========================================"
echo ""

# Test 1: Doppi apici attorno a mailto
echo "Test 1: Pattern \"mailto:...\""
echo "Input:  <a href=\"mailto:test@example.com\">Email</a>"
echo "Output: <a href=mailto:test@example.com>Email</a>"
echo ""

# Test 2: Entità HTML escapate
echo "Test 2: Pattern &quot;"
echo "Input:  &quot;http://example.com&quot;"
echo "Output: \"http://example.com\""
echo ""

# Test 3: Tag HTML escapati
echo "Test 3: Pattern &lt;a"
echo "Input:  &lt;a href=&quot;test&quot;&gt;"
echo "Output: <a href=\"test\">"
echo ""

# Test 4: href duplicati
echo "Test 4: Href duplicati"
echo "Input:  href=\"link1\"href=\"link2\""
echo "Output: href=\"link1\""
echo ""

echo "========================================"
echo "VERIFICA DATABASE (se disponibile)"
echo "========================================"
echo ""

# Verifica se Docker è disponibile
if command -v docker &> /dev/null; then
    if docker compose ps | grep -q "db.*running"; then
        echo "✓ Database Docker in esecuzione"
        echo ""
        echo "Query di esempio per trovare pattern problematici:"
        echo ""
        
        # Query di esempio (commentate, da eseguire manualmente)
        cat << 'EOF'
docker compose exec db psql -U postgres -d sld_db -c "
  SELECT 
    id, 
    title,
    substring(body::text, 1, 100) as preview
  FROM wagtailcore_page 
  WHERE body::text ~ '\"mailto:' 
     OR body::text ~ '&quot;http'
     OR body::text ~ '&lt;a'
  LIMIT 5;
"
EOF
        echo ""
    else
        echo "⚠ Database Docker non in esecuzione"
    fi
else
    echo "ℹ Docker non disponibile, verifica manuale necessaria"
fi

echo ""
echo "========================================"
echo "PROSSIMI PASSI"
echo "========================================"
echo ""
echo "1. Analisi (dry-run):"
echo "   source venv/bin/activate"
echo "   python3 scripts/clean_database_links_python.py --dry-run --verbose"
echo ""
echo "2. Esecuzione con backup:"
echo "   python3 scripts/clean_database_links_python.py --backup --verbose"
echo ""
echo "3. Oppure usa lo script SQL:"
echo "   docker compose exec db psql -U postgres -d sld_db -f /app/scripts/clean_database_links.sql"
echo ""
