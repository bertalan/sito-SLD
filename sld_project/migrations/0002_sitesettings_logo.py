# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0026_delete_uploadedimage'),
        ('sld_project', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='logo',
            field=models.ForeignKey(
                blank=True,
                help_text='Logo dello studio (preferibilmente SVG o PNG trasparente)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='wagtailimages.image',
                verbose_name='Logo',
            ),
        ),
    ]
