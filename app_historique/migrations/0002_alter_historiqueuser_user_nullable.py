from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("app_historique", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historiqueuser",
            name="user",
            field=models.ForeignKey(
                to="app_contact.user",
                related_name="historiques_actions",
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
            ),
        ),
    ]
