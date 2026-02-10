-- ============================================================================
-- SCRIPT SQL PER PULIZIA LINK E MAILTO PROBLEMATICI
-- ============================================================================
-- Questo script pulisce contenuti HTML mal formattati durante la migrazione
-- Pattern problematici:
--   - "mailto:" o "http://" tra doppi apici
--   - &quot;http invece di "http
--   - &lt;a invece di <a
--   - href="..." ripetuto o malformato
-- ============================================================================

BEGIN;

-- Crea tabella di log per tracciare le modifiche
CREATE TABLE IF NOT EXISTS cleanup_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255),
    column_name VARCHAR(255),
    record_id INTEGER,
    pattern_found VARCHAR(100),
    old_content TEXT,
    new_content TEXT,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FUNZIONE: Pulizia contenuti HTML
-- ============================================================================
CREATE OR REPLACE FUNCTION clean_html_content(content TEXT) 
RETURNS TEXT AS $$
BEGIN
    IF content IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- 1. Rimuovi doppi apici attorno a mailto:
    -- Da: "mailto:email@example.com" -> mailto:email@example.com
    content := regexp_replace(content, '"mailto:([^"]+)"', 'mailto:\1', 'g');
    
    -- 2. Rimuovi doppi apici attorno a http/https:
    -- Da: "http://example.com" -> http://example.com  
    content := regexp_replace(content, '"(https?://[^"]+)"', '\1', 'g');
    
    -- 3. Decodifica entità HTML:
    -- &quot; -> "
    content := replace(content, '&quot;', '"');
    -- &lt; -> <
    content := replace(content, '&lt;', '<');
    -- &gt; -> >
    content := replace(content, '&gt;', '>');
    -- &amp; -> &
    content := replace(content, '&amp;', '&');
    
    -- 4. Correggi href duplicati o malformati
    -- Da: href="..."href="..." -> href="..."
    content := regexp_replace(content, 'href="([^"]*)"[^>]*href="[^"]*"', 'href="\1"', 'g');
    
    -- 5. Rimuovi spazi extra attorno ai link
    content := regexp_replace(content, '\s+href=', ' href=', 'g');
    
    RETURN content;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PULIZIA TABELLE WAGTAIL
-- ============================================================================

-- Pagine Wagtail (body fields in JSON)
DO $$
DECLARE
    r RECORD;
    old_body TEXT;
    new_body TEXT;
    needs_update BOOLEAN;
BEGIN
    FOR r IN 
        SELECT id, body 
        FROM wagtailcore_page
        WHERE body IS NOT NULL 
        AND (
            body::text ~ '"mailto:' 
            OR body::text ~ '&quot;http'
            OR body::text ~ '&lt;a'
        )
    LOOP
        old_body := r.body::text;
        new_body := clean_html_content(old_body);
        
        IF old_body != new_body THEN
            UPDATE wagtailcore_page 
            SET body = new_body::jsonb
            WHERE id = r.id;
            
            INSERT INTO cleanup_log (table_name, column_name, record_id, pattern_found, old_content, new_content)
            VALUES ('wagtailcore_page', 'body', r.id, 'html_entities', 
                    substring(old_body, 1, 500), 
                    substring(new_body, 1, 500));
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- PULIZIA MODELLI PERSONALIZZATI
-- ============================================================================

-- Articoli
UPDATE articles_article
SET content = clean_html_content(content)
WHERE content IS NOT NULL 
AND (
    content ~ '"mailto:' 
    OR content ~ '&quot;http'
    OR content ~ '&lt;a'
);

-- Servizi
UPDATE services_servicepage
SET body = clean_html_content(body)
WHERE body IS NOT NULL 
AND (
    body ~ '"mailto:' 
    OR body ~ '&quot;http'
    OR body ~ '&lt;a'
);

-- Pagina Home
UPDATE home_homepage
SET hero_text = clean_html_content(hero_text),
    hero_subtitle = clean_html_content(hero_subtitle)
WHERE hero_text IS NOT NULL OR hero_subtitle IS NOT NULL;

-- Contatti
UPDATE contact_contactpage
SET intro = clean_html_content(intro)
WHERE intro IS NOT NULL 
AND (
    intro ~ '"mailto:' 
    OR intro ~ '&quot;http'
    OR intro ~ '&lt;a'
);

-- ============================================================================
-- PULIZIA REVISIONI WAGTAIL (per preservare history)
-- ============================================================================
UPDATE wagtailcore_pagerevision
SET content = clean_html_content(content::text)::jsonb
WHERE content::text ~ '"mailto:' 
   OR content::text ~ '&quot;http'
   OR content::text ~ '&lt;a';

-- ============================================================================
-- REPORT FINALE
-- ============================================================================
DO $$
DECLARE
    total_cleaned INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_cleaned FROM cleanup_log WHERE cleaned_at >= NOW() - INTERVAL '1 minute';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'PULIZIA COMPLETATA';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Record modificati: %', total_cleaned;
    RAISE NOTICE 'Log salvato in tabella: cleanup_log';
    RAISE NOTICE '';
    RAISE NOTICE 'Per verificare le modifiche:';
    RAISE NOTICE '  SELECT * FROM cleanup_log ORDER BY cleaned_at DESC LIMIT 20;';
    RAISE NOTICE '';
    RAISE NOTICE 'Per fare rollback (se necessario):';
    RAISE NOTICE '  ROLLBACK;';
    RAISE NOTICE '';
    RAISE NOTICE 'Per confermare:';
    RAISE NOTICE '  COMMIT;';
    RAISE NOTICE '============================================================================';
END $$;

-- NON FARE COMMIT AUTOMATICO - lascia decidere all'utente
-- COMMIT;
