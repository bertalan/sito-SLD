# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtaildocs', '0012_uploadeddocument'),
        ('sld_project', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='logo',
            field=models.ForeignKey(
                blank=True,
                help_text='Logo dello studio (SVG, PNG o JPG)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='wagtaildocs.document',
                verbose_name='Logo',
            ),
        ),
    ]
