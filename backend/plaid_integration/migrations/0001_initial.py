from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlaidItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.CharField(max_length=255)),
                ('item_id', models.CharField(max_length=255, unique=True)),
                ('institution_name', models.CharField(blank=True, default='', max_length=200)),
                ('accounts', models.JSONField(default=list)),
                ('cursor', models.CharField(blank=True, default='', max_length=500)),
                ('last_synced', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='plaid_items',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
