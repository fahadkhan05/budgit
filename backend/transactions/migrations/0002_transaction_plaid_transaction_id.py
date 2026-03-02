from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='plaid_transaction_id',
            field=models.CharField(blank=True, max_length=200, null=True, unique=True),
        ),
    ]
