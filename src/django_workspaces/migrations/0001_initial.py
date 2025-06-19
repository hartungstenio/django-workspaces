from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Workspace",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "name",
                    models.CharField(
                        db_comment="Workspace name",
                        help_text="Required. 255 characters or fewer.",
                        max_length=255,
                        verbose_name="name",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "swappable": "WORKSPACE_MODEL",
            },
        ),
    ]
