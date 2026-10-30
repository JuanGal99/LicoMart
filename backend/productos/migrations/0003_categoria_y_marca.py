from django.db import migrations, models
import django.db.models.deletion


CATEGORIAS = [
    ("Cervezas", "cervezas"),
    ("Ginebra", "ginebra"),
    ("Otros licores", "otros-licores"),
    ("Ron", "ron"),
    ("Tequila", "tequila"),
    ("Vodka", "vodka"),
    ("Whisky", "whisky"),
    ("Vinos", "vinos"),
]


def asignar_categorias_existentes(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Productos")
    categorias = {
        slug: Categoria.objects.using(schema_editor.connection.alias).get_or_create(
            slug=slug,
            defaults={"nombre": nombre},
        )[0]
        for nombre, slug in CATEGORIAS
    }

    palabras_clave = [
        ("whisky", "whisky"),
        ("whiskey", "whisky"),
        ("vodka", "vodka"),
        ("ron", "ron"),
        ("rum", "ron"),
        ("tequila", "tequila"),
        ("ginebra", "ginebra"),
        ("gin", "ginebra"),
        ("cerveza", "cervezas"),
        ("beer", "cervezas"),
        ("vino", "vinos"),
        ("espumante", "vinos"),
        ("champagne", "vinos"),
    ]

    for producto in Producto.objects.using(schema_editor.connection.alias).all().iterator():
        nombre = producto.nombre.casefold()
        slug = next(
            (categoria_slug for palabra, categoria_slug in palabras_clave if palabra in nombre),
            "otros-licores",
        )
        Producto.objects.using(schema_editor.connection.alias).filter(pk=producto.pk).update(
            categoria_id=categorias[slug].pk
        )


class Migration(migrations.Migration):
    dependencies = [
        ("productos", "0002_alter_productos_imagen"),
    ]

    operations = [
        migrations.CreateModel(
            name="Categoria",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=60, unique=True)),
                ("slug", models.SlugField(max_length=60, unique=True)),
            ],
            options={
                "ordering": ["nombre"],
                "verbose_name_plural": "categorías",
            },
        ),
        migrations.AddField(
            model_name="productos",
            name="marca",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="productos",
            name="categoria",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="productos",
                to="productos.categoria",
            ),
        ),
        migrations.RunPython(asignar_categorias_existentes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="productos",
            name="categoria",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="productos",
                to="productos.categoria",
            ),
        ),
    ]
