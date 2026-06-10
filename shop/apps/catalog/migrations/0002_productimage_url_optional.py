from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productimage",
            name="image",
            field=models.ImageField(blank=True, upload_to="products/", verbose_name="Фото"),
        ),
        migrations.AlterField(
            model_name="productimage",
            name="image_url",
            field=models.URLField(blank=True, default="", max_length=500, verbose_name="URL зображення"),
        ),
    ]
