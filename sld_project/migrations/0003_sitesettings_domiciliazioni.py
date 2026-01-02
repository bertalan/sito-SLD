# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sld_project', '0002_sitesettings_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='domiciliazioni_tribunali',
            field=models.TextField(
                blank=True,
                default="roma|Tribunale di Roma\ncorte_appello|Corte d'Appello di Roma\ngdp|Giudice di Pace di Roma\ntar|TAR Lazio\nunep|Ufficio UNEP di Roma",
                help_text='Una voce per riga. Formato: codice|Etichetta visibile. Es: roma|Tribunale di Roma',
                verbose_name='Tribunali / Uffici',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='domiciliazioni_tipi_udienza',
            field=models.TextField(
                blank=True,
                default="civile|Udienza Civile\npenale|Udienza Penale\nlavoro|Udienza Lavoro\nfamiglia|Udienza Famiglia\nesecuzioni|Esecuzioni\nfallimentare|Fallimentare\nvolontaria|Volontaria Giurisdizione\nnotificazioni|Ufficio notificazioni\nesecuzione_protesti|Ufficio esecuzione e protesti\naltro|Altro",
                help_text='Una voce per riga. Formato: codice|Etichetta visibile. Es: civile|Udienza Civile',
                verbose_name='Tipi Udienza / Servizio',
            ),
        ),
    ]
