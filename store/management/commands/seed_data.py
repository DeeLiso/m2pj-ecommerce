import random
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify

from store.models import Category, Order, OrderItem, Product

CATEGORIES = {
    "Smartphones": {
        "emoji": "📱",
        "products": [
            ("T-MAX Phone 15 Pro 256GB", 1_450_000, 1_690_000, 25),
            ("T-MAX Phone 14 128GB", 1_050_000, 1_190_000, 18),
            ("Aurora S24 Ultra", 1_380_000, 1_550_000, 9),
            ("Nova X Play", 320_000, None, 40),
        ],
    },
    "Laptops": {
        "emoji": "💻",
        "products": [
            ("T-MAX Book Air M3 13\"", 2_950_000, 3_350_000, 12),
            ("T-MAX Book Pro 16\"", 4_290_000, None, 7),
            ("SwiftCore i7 16GB/512GB", 1_650_000, 1_890_000, 15),
            ("UltraBook E14 2026", 980_000, None, 30),
        ],
    },
    "Audio": {
        "emoji": "🎧",
        "products": [
            ("T-MAX Sound Pro Headphones", 290_000, 350_000, 50),
            ("BassBuds Wireless Earbuds", 85_000, 120_000, 80),
            ("Studio Monitor 6\"", 180_000, None, 22),
            ("Portable Speaker GO+", 140_000, 160_000, 35),
        ],
    },
    "Wearables": {
        "emoji": "⌚",
        "products": [
            ("T-MAX Watch Ultra 2", 680_000, 800_000, 14),
            ("FitBand Smart Bracelet", 120_000, 150_000, 60),
            ("PulseRun GPS Watch", 260_000, None, 19),
        ],
    },
    "Gaming": {
        "emoji": "🎮",
        "products": [
            ("T-MAX GamePad Elite", 210_000, 250_000, 28),
            ("Gaming Keyboard RGB", 160_000, None, 33),
            ("Pro Mouse 4000 DPI", 95_000, 120_000, 45),
            ("Console Station X7", 890_000, 990_000, 11),
        ],
    },
    "Lifestyle": {
        "emoji": "🕶️",
        "products": [
            ("Urban Backpack USB 20L", 150_000, None, 26),
            ("Smart Water Bottle", 60_000, 80_000, 70),
            ("Travel Organizer Set", 45_000, None, 55),
            ("Desk Lamp Pro LED", 75_000, 90_000, 38),
            ("Mechanical Keyboard 75%", 185_000, 210_000, 20),
        ],
    },
}

PALETTES = [
    ("#0f172a", "#f59e0b"),
    ("#1e3a5f", "#38bdf8"),
    ("#365314", "#a3e635"),
    ("#4a044e", "#e879f9"),
    ("#581c87", "#c084fc"),
    ("#7c2d12", "#fb923c"),
    ("#14532d", "#34d399"),
    ("#881337", "#fb7185"),
]


def _make_svg_image(name, color_a, color_b, emoji):
    center = "50%" if len(name) % 2 else "40%"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{color_a}"/>
      <stop offset="100%" stop-color="{color_b}"/>
    </linearGradient>
  </defs>
  <rect width="600" height="600" fill="url(#g)"/>
  <circle cx="{center}" cy="40%" r="150" fill="rgba(255,255,255,.08)"/>
  <text x="50%" y="50%" font-size="140" text-anchor="middle" dominant-baseline="middle">{emoji}</text>
  <text x="50%" y="80%" font-size="34" fill="rgba(255,255,255,.9)" font-family="Arial" font-weight="bold" text-anchor="middle">{name[:28]}</text>
</svg>"""
    return ContentFile(svg.encode("utf-8"))


class Command(BaseCommand):
    help = "Seed the database with demo categories, products, users and a sample order."

    def handle(self, *args, **options):
        self.stdout.write("Seeding database for T-MAX-OS...\n")

        # --- Users ----------------------------------------------------
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "email": "admin@tmax-os.com"},
        )
        if created:
            admin.set_password("admin12345")
            admin.save()
            self.stdout.write("  + Admin user created (admin / admin12345)")

        customer, _ = User.objects.get_or_create(
            username="demo", defaults={"email": "demo@tmax-os.com", "first_name": "Demo"}
        )
        customer.set_password("demo12345")
        customer.save()
        self.stdout.write("  + Demo customer created (demo / demo12345)")

        # --- Categories + products -------------------------------------
        random.seed(42)
        palette_index = 0
        for cat_name, data in CATEGORIES.items():
            category, _ = Category.objects.get_or_create(
                name=cat_name, defaults={"slug": slugify(cat_name), "description": f"{cat_name} collection at T-MAX-OS."}
            )
            for name, price, compare, stock in data["products"]:
                if Product.objects.filter(name=name).exists():
                    continue
                color_a, color_b = PALETTES[palette_index % len(PALETTES)]
                palette_index += 1
                image_name = f"{slugify(name)[:40]}.svg"
                product = Product.objects.create(
                    name=name,
                    category=category,
                    sku=f"{slugify(cat_name).upper()[:4]}-{random.randint(1000, 9999)}",
                    description=(
                        f"Premium {name} from the {cat_name} range at T-MAX-OS. "
                        "Engineered for performance, backed by a 12-month warranty "
                        "and guaranteed authentic. Fast delivery across Myanmar."
                    ),
                    price=Decimal(price),
                    compare_at_price=Decimal(compare) if compare else None,
                    stock=stock,
                    featured=random.random() < 0.4,
                    is_active=True,
                )
                product.image.save(image_name, _make_svg_image(name, color_a, color_b, data["emoji"]), save=True)
            self.stdout.write(f"  + Category: {cat_name}")
        self.stdout.write(f"  + Total products: {Product.objects.count()}")

        # --- Sample order for demo customer ----------------------------
        if not Order.objects.filter(user=customer).exists():
            products = list(Product.objects.filter(is_active=True)[:3])
            subtotal = sum(p.price for p in products)
            shipping = Decimal("0") if subtotal >= Decimal("100000") else Decimal("3000")
            tax = subtotal * Decimal("0.05")
            order = Order.objects.create(
                user=customer,
                full_name="Demo Customer",
                email="demo@tmax-os.com",
                phone="09123456789",
                address_line1="No. 12, Pyay Road",
                city="Yangon",
                country="Myanmar",
                subtotal=subtotal,
                shipping=shipping,
                tax=tax,
                total=subtotal + shipping + tax,
                status="delivered",
                payment_method="demo",
                payment_id="DEMO-SAMPLE",
            )
            for p in products:
                OrderItem.objects.create(
                    order=order,
                    product=p,
                    product_name=p.name,
                    price=p.price,
                    quantity=1,
                    image=p.image,
                )
            self.stdout.write(f"  + Sample order created: {order.reference}")

        self.stdout.write(self.style.SUCCESS("\nDone! Run  python manage.py runserver  and log in with admin/admin12345"))