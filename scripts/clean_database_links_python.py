#!/usr/bin/env python3
"""
Script Python per pulire link e mailto problematici nel database.
Alternativa allo script SQL, con più controllo e logging dettagliato.

Uso:
    # Analisi senza modifiche (dry-run)
    python3 scripts/clean_database_links_python.py --dry-run
    
    # Pulizia effettiva
    python3 scripts/clean_database_links_python.py
    
    # Pulizia con backup automatico
    python3 scripts/clean_database_links_python.py --backup
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime
from pathlib import Path

# Setup Django
sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sld_project.settings.dev')

try:
    import django
    django.setup()
except ImportError:
    print("❌ Errore: Django non trovato. Assicurati di essere nel virtualenv:")
    print("   source venv/bin/activate")
    sys.exit(1)

from django.db import connection, transaction
from django.core.management import call_command


class LinkCleaner:
    """Classe per pulire link e mailto problematici"""
    
    PATTERNS = {
        'double_quoted_mailto': (
            r'"mailto:([^"]+)"',
            r'mailto:\1',
            'Rimuove doppi apici attorno a mailto:'
        ),
        'double_quoted_http': (
            r'"(https?://[^"]+)"',
            r'\1',
            'Rimuove doppi apici attorno a http/https'
        ),
        'html_entities': [
            (r'&quot;', '"', 'Decodifica &quot;'),
            (r'&lt;', '<', 'Decodifica &lt;'),
            (r'&gt;', '>', 'Decodifica &gt;'),
            (r'&amp;', '&', 'Decodifica &amp;'),
        ],
        'duplicate_href': (
            r'href="([^"]*)"[^>]*href="[^"]*"',
            r'href="\1"',
            'Corregge href duplicati'
        ),
    }
    
    def __init__(self, dry_run=False, verbose=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.changes = []
        self.stats = {
            'tables_scanned': 0,
            'records_checked': 0,
            'records_modified': 0,
            'patterns_found': {}
        }
    
    def clean_content(self, content):
        """Pulisce il contenuto applicando tutti i pattern"""
        if not content:
            return content, []
        
        original = content
        changes_made = []
        
        # Applica pattern singoli
        for pattern_name, pattern_data in self.PATTERNS.items():
            if pattern_name == 'html_entities':
                # Pattern multipli per entità HTML
                for entity_pattern, replacement, description in pattern_data:
                    if entity_pattern in content:
                        content = content.replace(entity_pattern, replacement)
                        changes_made.append(f"{description} ({entity_pattern})")
            else:
                # Pattern regex singolo
                pattern, replacement, description = pattern_data
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    changes_made.append(description)
        
        return content, changes_made if content != original else []
    
    def clean_table(self, table_name, text_columns, pk_field='id'):
        """Pulisce una tabella specifica"""
        print(f"\n📋 Scansione tabella: {table_name}")
        self.stats['tables_scanned'] += 1
        
        with connection.cursor() as cursor:
            # Ottieni tutti i record con ID (gestisce diversi nomi di primary key)
            try:
                cursor.execute(f'SELECT {pk_field} FROM {table_name}')
                record_ids = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                print(f"  ⚠️  Errore lettura tabella: {str(e)}")
                return
            
            for record_id in record_ids:
                self.stats['records_checked'] += 1
                record_modified = False
                
                for column in text_columns:
                    # Leggi il contenuto
                    cursor.execute(
                        f'SELECT "{column}" FROM {table_name} WHERE {pk_field} = %s',
                        [record_id]
                    )
                    result = cursor.fetchone()
                    if not result or not result[0]:
                        continue
                    
                    old_content = str(result[0])
                    
                    # Pulisci il contenuto
                    new_content, changes = self.clean_content(old_content)
                    
                    if changes:
                        record_modified = True
                        change_info = {
                            'table': table_name,
                            'column': column,
                            'id': record_id,
                            'changes': changes,
                            'preview_old': old_content[:200],
                            'preview_new': new_content[:200]
                        }
                        self.changes.append(change_info)
                        
                        for change in changes:
                            self.stats['patterns_found'][change] = \
                                self.stats['patterns_found'].get(change, 0) + 1
                        
                        if self.verbose:
                            print(f"  ✗ ID {record_id}, colonna '{column}':")
                            for change in changes:
                                print(f"    - {change}")
                        
                        # Aggiorna il database (se non dry-run)
                        if not self.dry_run:
                            cursor.execute(
                                f'UPDATE {table_name} SET "{column}" = %s WHERE {pk_field} = %s',
                                [new_content, record_id]
                            )
                
                if record_modified:
                    self.stats['records_modified'] += 1
    
    def scan_database(self):
        """Scansiona il database per trovare contenuti problematici"""
        print("=" * 80)
        print("🔍 SCANSIONE DATABASE - LINK E MAILTO PROBLEMATICI")
        print("=" * 80)
        
        if self.dry_run:
            print("⚠️  MODALITÀ DRY-RUN: Nessuna modifica verrà effettuata\n")
        
        # Tabelle da pulire con le colonne di testo e primary key
        # Formato: 'table_name': (['columns'], 'pk_field')
        tables_to_clean = {
            'wagtailcore_page': (['title', 'draft_title', 'seo_title'], 'id'),
            'home_homepage': (['about_text', 'about_title', 'cta_text', 'cta_title', 
                              'hero_line1', 'hero_line2', 'hero_line3', 'hero_line4',
                              'hero_txt_accent', 'hero_txt_legale', 'hero_txt_studio'], 'page_ptr_id'),
            'services_servicepage': (['body', 'subtitle'], 'page_ptr_id'),
            'contact_contactpage': (['intro', 'thank_you_text'], 'page_ptr_id'),
            'booking_appointment': (['notes'], 'id'),
            'domiciliazioni_domiciliazionipage': (['intro'], 'page_ptr_id'),
        }
        
        # Pulisci ogni tabella
        for table_name, (columns, pk_field) in tables_to_clean.items():
            try:
                self.clean_table(table_name, columns, pk_field)
            except Exception as e:
                print(f"  ⚠️  Errore su {table_name}: {str(e)}")
        
        # Stampa report
        self.print_report()
    
    def print_report(self):
        """Stampa il report finale"""
        print("\n" + "=" * 80)
        print("📊 REPORT FINALE")
        print("=" * 80)
        
        print(f"\nTabelle scansionate: {self.stats['tables_scanned']}")
        print(f"Record verificati: {self.stats['records_checked']}")
        print(f"Record modificati: {self.stats['records_modified']}")
        
        if self.stats['patterns_found']:
            print("\nPattern trovati e corretti:")
            for pattern, count in sorted(
                self.stats['patterns_found'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"  - {pattern}: {count} occorrenze")
        
        if not self.changes:
            print("\n✅ Nessun pattern problematico trovato!")
            return
        
        if self.dry_run:
            print("\n" + "=" * 80)
            print("⚠️  MODALITÀ DRY-RUN ATTIVA")
            print("=" * 80)
            print("\nPer effettuare le modifiche, esegui:")
            print(f"  python3 {sys.argv[0]}")
        else:
            print("\n✅ Database pulito con successo!")
            print("\nModifiche salvate nel database.")
    
    def save_log(self, filename='cleanup_log.json'):
        """Salva il log delle modifiche in un file JSON"""
        log_path = Path(__file__).parent / filename
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'dry_run': self.dry_run,
                'stats': self.stats,
                'changes': self.changes
            }, f, indent=2, ensure_ascii=False)
        print(f"\n📝 Log salvato in: {log_path}")


def create_backup(backup_name=None):
    """Crea un backup del database"""
    if not backup_name:
        backup_name = f"backup_before_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    backup_path = Path(__file__).parent.parent / backup_name
    
    print(f"\n💾 Creazione backup: {backup_path}")
    
    # Leggi configurazione database da .env o settings
    db_name = os.getenv('POSTGRES_DB', 'sld_db')
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    
    cmd = f"PGPASSWORD={db_password} pg_dump -h {db_host} -U {db_user} {db_name} > {backup_path}"
    os.system(cmd)
    
    if backup_path.exists():
        print(f"✅ Backup creato: {backup_path}")
        return True
    else:
        print("❌ Errore nella creazione del backup!")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Pulisce link e mailto problematici nel database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Esegue senza modificare il database (solo analisi)'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Crea un backup del database prima della pulizia'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Output dettagliato'
    )
    
    args = parser.parse_args()
    
    # Crea backup se richiesto
    if args.backup and not args.dry_run:
        if not create_backup():
            print("\n⚠️  Backup fallito. Continuare comunque? (y/N): ", end='')
            if input().lower() != 'y':
                print("Operazione annullata.")
                return
    
    # Esegui la pulizia
    cleaner = LinkCleaner(dry_run=args.dry_run, verbose=args.verbose)
    
    try:
        with transaction.atomic():
            cleaner.scan_database()
            cleaner.save_log()
            
            if args.dry_run:
                # Rollback automatico in dry-run
                transaction.set_rollback(True)
            else:
                # Chiedi conferma prima del commit
                print("\n" + "=" * 80)
                print("⚠️  ATTENZIONE: Le modifiche sono state effettuate in una transazione.")
                print("=" * 80)
                print("\nConfermare le modifiche? (y/N): ", end='')
                
                if input().lower() != 'y':
                    print("\n🔙 Rollback effettuato. Nessuna modifica salvata.")
                    transaction.set_rollback(True)
                else:
                    print("\n✅ Modifiche confermate e salvate nel database.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operazione interrotta dall'utente.")
        print("🔙 Rollback automatico effettuato.")
    except Exception as e:
        print(f"\n❌ Errore durante l'esecuzione: {str(e)}")
        print("🔙 Rollback automatico effettuato.")
        raise


if __name__ == '__main__':
    main()
