# Generated migration for is_deleted field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_pdfreport'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagespeedanalysis',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
