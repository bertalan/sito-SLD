"""
Migrazione originariamente usata per creare la HomePage.
Ora i dati di esempio vengono creati con: python manage.py setup_demo_data

NOTA: Questa migrazione è mantenuta vuota per compatibilità con i database esistenti.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        # Nessuna operazione - i dati vengono creati con setup_demo_data
    ]
