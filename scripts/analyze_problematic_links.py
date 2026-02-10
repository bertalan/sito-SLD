#!/usr/bin/env python3
"""
Script per analizzare il database e identificare contenuti con link/mailto problematici.
Cerca pattern come:
- "mailto:" tra virgolette
- "&quot;http" (link escapati)
- "&lt;a" (tag HTML escapati)
"""

import os
import sys
import django
import re
from collections import defaultdict

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sld_project.settings.dev')
django.setup()

from django.db import connection
from wagtail.models import Page
from wagtail.rich_text import RichText
from django.contrib.contenttypes.models import ContentType
import json


def analyze_database():
    """Analizza il database per trovare pattern problematici"""
    
    print("=" * 80)
    print("ANALISI DATABASE - PATTERN PROBLEMATICI")
    print("=" * 80)
    
    # Pattern da cercare
    patterns = {
        'mailto_quotes': r'"mailto:',
        'http_quotes': r'&quot;http',
        'html_escaped': r'&lt;a\s',
        'double_quoted_links': r'""http',
        'malformed_mailto': r'href="mailto:[^"]*"[^>]*"'
    }
    
    results = defaultdict(list)
    
    # 1. Analizza pagine Wagtail
    print("\n1. ANALISI PAGINE WAGTAIL")
    print("-" * 80)
    
    pages = Page.objects.all()
    for page in pages:
        try:
            specific = page.specific
            page_dict = specific.__dict__
            
            for field_name, field_value in page_dict.items():
                if field_name.startswith('_'):
                    continue
                    
                # Converti in stringa se è un RichText o altro
                content = str(field_value) if field_value is not None else ''
                
                for pattern_name, pattern in patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        results[pattern_name].append({
                            'type': 'Page',
                            'id': page.id,
                            'title': page.title,
                            'field': field_name,
                            'content_preview': content[:200]
                        })
                        print(f"✗ Page {page.id} ({page.title}): {field_name} -> {pattern_name}")
                        break
        except Exception as e:
            print(f"  Errore su pagina {page.id}: {str(e)}")
    
    # 2. Query diretta sul database per cercare in tutte le colonne di tipo text
    print("\n2. ANALISI DIRETTA TABELLE")
    print("-" * 80)
    
    with connection.cursor() as cursor:
        # Ottieni tutte le tabelle
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name NOT LIKE 'django_%'
            AND table_name NOT LIKE 'wagtail%_revision%'
        """)
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            # Ottieni le colonne di tipo text/varchar
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s 
                AND data_type IN ('text', 'character varying', 'json', 'jsonb')
            """, [table_name])
            columns = cursor.fetchall()
            
            if not columns:
                continue
            
            for (column_name,) in columns:
                try:
                    # Cerca i pattern
                    for pattern_name, pattern in patterns.items():
                        query = f"""
                            SELECT id, "{column_name}" 
                            FROM {table_name} 
                            WHERE "{column_name}" ~ %s 
                            LIMIT 10
                        """
                        cursor.execute(query, [pattern])
                        rows = cursor.fetchall()
                        
                        if rows:
                            print(f"\n✗ Tabella: {table_name}, Colonna: {column_name}, Pattern: {pattern_name}")
                            for row_id, content in rows:
                                preview = str(content)[:150] if content else ''
                                print(f"  - ID: {row_id}")
                                print(f"    Preview: {preview}...")
                                results[pattern_name].append({
                                    'type': 'Table',
                                    'table': table_name,
                                    'column': column_name,
                                    'id': row_id,
                                    'content_preview': preview
                                })
                except Exception as e:
                    pass  # Ignora errori su tabelle/colonne specifiche
    
    # 3. Riepilogo
    print("\n" + "=" * 80)
    print("RIEPILOGO RISULTATI")
    print("=" * 80)
    
    if not any(results.values()):
        print("\n✓ Nessun pattern problematico trovato nel database!")
        return None
    
    for pattern_name, items in results.items():
        if items:
            print(f"\n{pattern_name}: {len(items)} occorrenze trovate")
    
    total = sum(len(items) for items in results.values())
    print(f"\nTotale occorrenze problematiche: {total}")
    
    return results


if __name__ == '__main__':
    results = analyze_database()
    
    if results:
        print("\n" + "=" * 80)
        print("PROSSIMI PASSI")
        print("=" * 80)
        print("\n1. Esegui lo script di pulizia SQL: python scripts/clean_database_links.py")
        print("2. Oppure esegui lo script SQL generato: scripts/clean_links.sql")
