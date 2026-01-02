"""
Management command per creare le festività italiane come date bloccate.
Uso: python manage.py setup_holidays [--years N] [--exclude FESTIVITÀ...] [--list] [--clear]
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand


def easter_date(year):
    """
    Calcola la data di Pasqua con l'algoritmo di Gauss/Meeus.
    Valido per anni dal 1900 al 2099.
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


# Definizione festività italiane
FESTIVITA_ITALIANE = {
    'capodanno': {
        'nome': 'Capodanno',
        'data': lambda year: date(year, 1, 1),
    },
    'epifania': {
        'nome': 'Epifania',
        'data': lambda year: date(year, 1, 6),
    },
    'pasqua': {
        'nome': 'Pasqua',
        'data': lambda year: easter_date(year),
    },
    'pasquetta': {
        'nome': 'Lunedì dell\'Angelo',
        'data': lambda year: easter_date(year) + timedelta(days=1),
    },
    'liberazione': {
        'nome': 'Festa della Liberazione',
        'data': lambda year: date(year, 4, 25),
    },
    'lavoro': {
        'nome': 'Festa del Lavoro',
        'data': lambda year: date(year, 5, 1),
    },
    'repubblica': {
        'nome': 'Festa della Repubblica',
        'data': lambda year: date(year, 6, 2),
    },
    'ferragosto': {
        'nome': 'Ferragosto',
        'data': lambda year: date(year, 8, 15),
    },
    'ognissanti': {
        'nome': 'Ognissanti',
        'data': lambda year: date(year, 11, 1),
    },
    'immacolata': {
        'nome': 'Immacolata Concezione',
        'data': lambda year: date(year, 12, 8),
    },
    'natale': {
        'nome': 'Natale',
        'data': lambda year: date(year, 12, 25),
    },
    'stefano': {
        'nome': 'Santo Stefano',
        'data': lambda year: date(year, 12, 26),
    },
}


class Command(BaseCommand):
    help = 'Crea le festività italiane come date bloccate per le prenotazioni'

    def add_arguments(self, parser):
        parser.add_argument(
            '--years',
            type=int,
            default=2,
            help='Numero di anni da generare (default: 2)',
        )
        parser.add_argument(
            '--exclude',
            nargs='+',
            default=[],
            help='Festività da escludere (es: --exclude pasquetta ferragosto)',
        )
        parser.add_argument(
            '--include-only',
            nargs='+',
            dest='include_only',
            default=[],
            help='Includi solo queste festività (es: --include-only natale pasqua)',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Mostra tutte le festività disponibili',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Rimuovi tutte le festività esistenti prima di creare le nuove',
        )
        parser.add_argument(
            '--start-year',
            type=int,
            dest='start_year',
            default=None,
            help='Anno di partenza (default: anno corrente)',
        )

    def handle(self, *args, **options):
        from booking.models import BlockedDate
        
        # Mostra lista festività
        if options['list']:
            self.stdout.write('\n📅 Festività italiane disponibili:\n')
            self.stdout.write('-' * 50)
            for codice, info in FESTIVITA_ITALIANE.items():
                esempio = info['data'](date.today().year)
                self.stdout.write(f"  {codice:15} {info['nome']:30} (es: {esempio.strftime('%d/%m')})")
            self.stdout.write('-' * 50)
            self.stdout.write('\nUso: python manage.py setup_holidays --years 3')
            self.stdout.write('     python manage.py setup_holidays --exclude pasquetta ferragosto')
            return
        
        # Rimuovi festività esistenti
        if options['clear']:
            # Rimuovi solo le festività (non altre date bloccate come ferie)
            festivity_reasons = [info['nome'] for info in FESTIVITA_ITALIANE.values()]
            deleted, _ = BlockedDate.objects.filter(reason__in=festivity_reasons).delete()
            self.stdout.write(f'  🗑️  Rimosse {deleted} festività esistenti')
        
        # Configura anni
        start_year = options['start_year'] or date.today().year
        years = options['years']
        exclude = set(options['exclude'])
        include_only = set(options['include_only'])
        
        # Determina quali festività creare
        festivita_da_creare = {}
        for codice, info in FESTIVITA_ITALIANE.items():
            if include_only and codice not in include_only:
                continue
            if codice in exclude:
                continue
            festivita_da_creare[codice] = info
        
        if not festivita_da_creare:
            self.stdout.write(self.style.WARNING('⚠️  Nessuna festività da creare (controlla --exclude e --include-only)'))
            return
        
        # Crea le date bloccate
        created_count = 0
        skipped_count = 0
        
        self.stdout.write(f'\n📅 Creazione festività italiane ({start_year}-{start_year + years - 1})...\n')
        
        for year in range(start_year, start_year + years):
            for codice, info in festivita_da_creare.items():
                festa_date = info['data'](year)
                
                # Salta date nel passato
                if festa_date < date.today():
                    continue
                
                # Controlla se esiste già
                if BlockedDate.objects.filter(date=festa_date).exists():
                    skipped_count += 1
                    continue
                
                BlockedDate.objects.create(
                    date=festa_date,
                    reason=info['nome']
                )
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Create {created_count} festività'))
        if skipped_count:
            self.stdout.write(f'  (saltate {skipped_count} già esistenti)')
        
        # Mostra riepilogo
        self.stdout.write(f'\n📋 Festività incluse ({len(festivita_da_creare)}):')
        for codice, info in festivita_da_creare.items():
            self.stdout.write(f'   • {info["nome"]}')
        
        if exclude:
            self.stdout.write(f'\n❌ Escluse: {", ".join(exclude)}')
