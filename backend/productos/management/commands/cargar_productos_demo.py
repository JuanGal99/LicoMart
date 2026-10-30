from django.core.management.base import BaseCommand

from productos.models import Categoria, Productos


PRODUCTOS_DEMO = [
    {
        "nombre_anterior": "Whisky Sierra Dorada 8 años",
        "nombre": "Black & White Scotch Whisky",
        "marca": "Black & White",
        "categoria": "whisky",
        "descripcion": "Whisky escocés blended de perfil suave.",
        "stock": 24,
        "precio": 42900,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/41/Black_%26_White_%28whisky%29_bottle_01.jpg/960px-Black_%26_White_%28whisky%29_bottle_01.jpg",
    },
    {
        "nombre_anterior": "Whisky Reserva del Roble",
        "nombre": "Scotch Malt Whisky Society Single Malt",
        "marca": "Scotch Malt Whisky Society",
        "categoria": "whisky",
        "descripcion": "Whisky escocés de malta en presentación de colección.",
        "stock": 15,
        "precio": 68500,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c9/Bottle_of_whisky_from_the_Scotch_Malt_Whisky_Society.jpg/960px-Bottle_of_whisky_from_the_Scotch_Malt_Whisky_Society.jpg",
    },
    {
        "nombre_anterior": "Whisky Malteado Niebla Alta",
        "nombre": "English Whisky Collection",
        "marca": "The English Whisky Co.",
        "categoria": "whisky",
        "descripcion": "Selección de whisky inglés de malta.",
        "marca_historica": "Niebla Alta",
        "imagen_historica": "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?auto=format&fit=crop&w=800&q=80",
        "stock": 9,
        "precio": 112000,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a5/English_Whisky_bottles.webp/960px-English_Whisky_bottles.webp",
    },
    {
        "nombre_anterior": "Ron Caña Morena Añejo",
        "nombre": "Captain Morgan Rum",
        "marca": "Captain Morgan",
        "categoria": "ron",
        "descripcion": "Ron especiado de origen caribeño.",
        "stock": 32,
        "precio": 38900,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c2/Bottle_of_Captain_Morgan_Rum_01.jpg/960px-Bottle_of_Captain_Morgan_Rum_01.jpg",
    },
    {
        "nombre_anterior": "Ron Reserva Isla Clara",
        "nombre": "Ron Zacapa XO",
        "marca": "Zacapa",
        "categoria": "ron",
        "descripcion": "Ron guatemalteco de reserva extra añeja.",
        "stock": 18,
        "precio": 59700,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/76/Ron-Zacapa-XO.jpg/960px-Ron-Zacapa-XO.jpg",
    },
    {
        "nombre_anterior": "Ginebra Botánica del Valle",
        "nombre": "Hendrick's Gin",
        "marca": "Hendrick's",
        "categoria": "ginebra",
        "descripcion": "Ginebra escocesa con notas de pepino y rosa.",
        "stock": 21,
        "precio": 52900,
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/9/9c/Hendrick%27s_Gin_-_Bottle.png",
    },
    {
        "nombre_anterior": "Ginebra Cítrica Bruma",
        "nombre": "Gordon's London Dry Gin",
        "marca": "Gordon's",
        "categoria": "ginebra",
        "descripcion": "Ginebra London Dry de perfil clásico y enebro.",
        "stock": 12,
        "precio": 63400,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/87/Vintage_Gordon%E2%80%99s_Gin_bottle.jpg/960px-Vintage_Gordon%E2%80%99s_Gin_bottle.jpg",
    },
    {
        "nombre_anterior": "Vodka Cristal Norte",
        "nombre": "Crystal Head Vodka",
        "marca": "Crystal Head",
        "categoria": "vodka",
        "descripcion": "Vodka canadiense en su característica botella de cristal.",
        "stock": 28,
        "precio": 31500,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/54/Crystal_Head_Vodka.jpg/960px-Crystal_Head_Vodka.jpg",
    },
    {
        "nombre_anterior": "Vodka Trigo Blanco",
        "nombre": "Tito's Handmade Vodka 1.75 L",
        "marca": "Tito's",
        "categoria": "vodka",
        "descripcion": "Vodka artesanal de maíz en presentación de 1.75 litros.",
        "stock": 16,
        "precio": 47800,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/30/Tito%27s_Vodka_bottle_1.75L_size.jpg/960px-Tito%27s_Vodka_bottle_1.75L_size.jpg",
    },
    {
        "nombre_anterior": "Tequila Agave del Sol Blanco",
        "nombre": "Tequila Corralejo Blanco 100 ml",
        "marca": "Corralejo",
        "categoria": "tequila",
        "descripcion": "Tequila blanco de agave azul en botella de 100 ml.",
        "stock": 20,
        "precio": 55400,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e8/Tequila_Corralejo_100ml_%28Blanco%29%2C_Mexico%2C_2026-03-30.jpg/960px-Tequila_Corralejo_100ml_%28Blanco%29%2C_Mexico%2C_2026-03-30.jpg",
    },
    {
        "nombre_anterior": "Tequila Agave del Sol Reposado",
        "nombre": "Tequila Corralejo Reposado 100 ml",
        "marca": "Corralejo",
        "categoria": "tequila",
        "descripcion": "Tequila reposado en barrica en botella de 100 ml.",
        "stock": 11,
        "precio": 72900,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/47/Tequila_Corralejo_100ml_%28Reposado%29%2C_Mexico%2C_2026-03-30.jpg/960px-Tequila_Corralejo_100ml_%28Reposado%29%2C_Mexico%2C_2026-03-30.jpg",
    },
    {
        "nombre_anterior": "Vino Tinto Monte Sereno",
        "nombre": "Barefoot White Zinfandel",
        "marca": "Barefoot",
        "categoria": "vinos",
        "descripcion": "Vino rosado White Zinfandel de perfil frutal.",
        "marca_historica": "Monte Sereno",
        "imagen_historica": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=800&q=80",
        "stock": 36,
        "precio": 36200,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f9/Bottle_and_glass_of_Barefoot_white_zinfandel_wine%2C_2012.jpg/960px-Bottle_and_glass_of_Barefoot_white_zinfandel_wine%2C_2012.jpg",
    },
    {
        "nombre_anterior": "Vino Blanco Ladera Fresca",
        "nombre": "Tsimlyansk Red Wine",
        "marca": "Tsimlyansk",
        "categoria": "vinos",
        "descripcion": "Vino tinto de la región vinícola de Tsimlyansk.",
        "stock": 27,
        "precio": 33800,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b8/Tsimlyansk_wines%2C_Rostov-on-Don%2C_Russia.jpg/960px-Tsimlyansk_wines%2C_Rostov-on-Don%2C_Russia.jpg",
    },
    {
        "nombre_anterior": "Vino Rosado Jardín de Abril",
        "nombre": "Tsimlyansk Wine Collection",
        "marca": "Tsimlyansk",
        "categoria": "vinos",
        "descripcion": "Selección de vinos de la región de Tsimlyansk.",
        "stock": 19,
        "precio": 34700,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9a/Tsimlyansk_wines%2C_Wine_bottles%2C_Rostov-on-Don%2C_Russia.jpg/960px-Tsimlyansk_wines%2C_Wine_bottles%2C_Rostov-on-Don%2C_Russia.jpg",
    },
    {
        "nombre_anterior": "Cerveza Artesanal Lúpulo Claro",
        "nombre": "Angkor Premium Beer",
        "marca": "Angkor",
        "categoria": "cervezas",
        "descripcion": "Cerveza lager camboyana de sabor equilibrado.",
        "stock": 48,
        "precio": 8900,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/99/Angkor_beer_bottle_%26_glass.jpg/960px-Angkor_beer_bottle_%26_glass.jpg",
    },
    {
        "nombre_anterior": "Cerveza Trigo Dorado",
        "nombre": "Grolsch Premium Lager",
        "marca": "Grolsch",
        "categoria": "cervezas",
        "descripcion": "Cerveza lager neerlandesa de fermentación baja.",
        "stock": 42,
        "precio": 7900,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/20/Grolsch_Beer_Bottles.jpg/960px-Grolsch_Beer_Bottles.jpg",
    },
    {
        "nombre_anterior": "Espumante Brisa de Oro",
        "nombre": "Cointreau Orange Liqueur",
        "marca": "Cointreau",
        "categoria": "otros-licores",
        "descripcion": "Licor de naranja francés para coctelería y sobremesa.",
        "stock": 14,
        "precio": 61900,
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/b/b6/Cointreau.jpg",
    },
    {
        "nombre_anterior": "Licor de Café Noche Serena",
        "nombre": "Baileys Original Irish Cream",
        "marca": "Baileys",
        "categoria": "otros-licores",
        "descripcion": "Licor de crema irlandesa con whiskey.",
        "stock": 13,
        "precio": 41800,
        "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0d/Baileys_Original_Irish_Cream_Bottle.jpg/960px-Baileys_Original_Irish_Cream_Bottle.jpg",
    },
]


class Command(BaseCommand):
    help = (
        "Carga productos de demostración sin modificar los existentes. "
        "La actualización de los registros demo antiguos es explícita."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--actualizar-productos-demo-existentes",
            action="store_true",
            help=(
                "Actualiza únicamente nombre, marca, categoría e imagen de los "
                "18 productos demo originales reconocidos por su nombre exacto."
            ),
        )

    def handle(self, *args, **options):
        categorias = {
            slug: Categoria.objects.get_or_create(
                slug=slug,
                defaults={"nombre": nombre},
            )[0]
            for nombre, slug in (
                ("Cervezas", "cervezas"),
                ("Ginebra", "ginebra"),
                ("Otros licores", "otros-licores"),
                ("Ron", "ron"),
                ("Tequila", "tequila"),
                ("Vodka", "vodka"),
                ("Whisky", "whisky"),
                ("Vinos", "vinos"),
            )
        }
        created_count = 0
        existing_count = 0
        updated_count = 0
        order_linked_count = 0

        for producto_data in PRODUCTOS_DEMO:
            data = {
                **producto_data,
                "categoria": categorias[producto_data["categoria"]],
            }
            nombre_anterior = data.pop("nombre_anterior")
            marca_historica = data.pop("marca_historica", data["marca"])
            imagen_historica = data.pop("imagen_historica", data["imagen"])
            producto_existente = Productos.objects.filter(
                nombre=data["nombre"]
            ).first()
            producto_anterior = Productos.objects.filter(
                nombre=nombre_anterior
            ).order_by("id").first()

            if producto_existente:
                existing_count += 1
                continue

            if producto_anterior:
                existing_count += 1
                if options["actualizar_productos_demo_existentes"]:
                    relacionado_con_pedido = producto_anterior.detallepedido_set.exists()
                    if relacionado_con_pedido:
                        order_linked_count += 1
                    cambios = {
                        campo: valor
                        for campo, valor in {
                            "nombre": data["nombre"],
                            "marca": data["marca"],
                            "categoria": data["categoria"],
                            "imagen": data["imagen"],
                            "descripcion": data["descripcion"],
                            **(
                                {
                                    "marca": marca_historica,
                                    "imagen": imagen_historica,
                                }
                                if relacionado_con_pedido
                                else {}
                            ),
                        }.items()
                        if getattr(producto_anterior, campo) != valor
                    }
                    if relacionado_con_pedido:
                        cambios.pop("nombre", None)
                        cambios.pop("descripcion", None)
                    if cambios:
                        for campo, valor in cambios.items():
                            setattr(producto_anterior, campo, valor)
                        producto_anterior.save(update_fields=list(cambios))
                        updated_count += 1
                continue

            Productos.objects.create(**data)
            created_count += 1

        summary = (
            f"Carga completada: {created_count} creados, "
            f"{existing_count} existentes, {updated_count} actualizados, "
            f"{order_linked_count} ligados a pedidos protegidos."
        )
        self.stdout.write(self.style.SUCCESS(summary))
        if existing_count and not options["actualizar_productos_demo_existentes"]:
            self.stdout.write(
                "Los productos existentes se conservaron. Para actualizar solo "
                "los registros demo originales identificados por su nombre exacto, "
                "ejecuta el comando con --actualizar-productos-demo-existentes."
            )
