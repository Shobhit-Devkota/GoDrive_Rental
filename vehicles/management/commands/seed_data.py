from django.core.management.base import BaseCommand
from django.utils.text import slugify
from vehicles.models import Brand, Vehicle, VehicleImage, Destination


VEHICLES = [
    ("BYD", "Seal", "electric", "automatic", 5, 6500,
     "A sleek all-electric sedan with fast charging and a spacious cabin, ideal for city commutes and highway trips alike."),
    ("Toyota", "Corolla Cross", "petrol", "automatic", 5, 5500,
     "A reliable compact SUV known for fuel efficiency and comfort, well suited for both city driving and hill trips."),
    ("Hyundai", "Creta", "petrol", "automatic", 5, 5200,
     "A popular family SUV offering a smooth ride, generous boot space and modern safety features."),
    ("Suzuki", "Swift", "petrol", "manual", 5, 3200,
     "A compact hatchback that's easy to drive and park, perfect for solo travelers and small groups exploring the city."),
    ("Tata", "Nexon", "diesel", "manual", 5, 4200,
     "A rugged compact SUV built for Nepal's hill roads, offering a strong diesel engine and confident handling."),
    ("Mahindra", "Scorpio", "diesel", "manual", 7, 6000,
     "A powerful 7-seater SUV ideal for long-distance family trips and rough mountain terrain."),
    ("Kia", "Seltos", "petrol", "automatic", 5, 5400,
     "A stylish crossover SUV with a comfortable interior, great for both daily use and weekend getaways."),
    ("Honda", "City", "petrol", "automatic", 5, 4800,
     "A well-balanced sedan offering a smooth automatic drive, popular for airport transfers and city tours."),
    ("Ford", "EcoSport", "petrol", "manual", 5, 4000,
     "A compact SUV with a raised ground clearance, suited for both city streets and unpaved roads."),
    ("Nissan", "X-Trail", "petrol", "automatic", 7, 6800,
     "A spacious 7-seater SUV with all-wheel drive capability, excellent for group travel across varied terrain."),
]

ANGLE_COLORS = {
    "front": "1D4ED8",
    "side": "0D9488",
    "rear": "111827",
}

DESTINATIONS = [
    ("Kathmandu Valley", 0),
    ("Pokhara", 800),
    ("Chitwan", 500),
    ("Nagarkot", -300),
    ("Lumbini", 1200),
]


class Command(BaseCommand):
    help = "Seed the database with sample brands, vehicles, images and destinations."

    def handle(self, *args, **options):
        for name, extra in DESTINATIONS:
            Destination.objects.update_or_create(
                slug=slugify(name),
                defaults={"name": name, "extra_charge_per_day": extra}
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(DESTINATIONS)} destinations."))

        total_images = 0
        for i, (brand_name, model_name, fuel, transmission, seats, price, desc) in enumerate(VEHICLES):
            brand, _ = Brand.objects.get_or_create(
                name=brand_name, defaults={"slug": slugify(brand_name)}
            )
            vehicle, created = Vehicle.objects.update_or_create(
                brand=brand, model_name=model_name,
                defaults={
                    "description": desc,
                    "seats": seats,
                    "transmission": transmission,
                    "fuel_type": fuel,
                    "price_per_day": price,
                    "is_active": True,
                    "is_featured": True,
                }
            )
            if created or vehicle.images.count() == 0:
                for order, angle in enumerate(["front", "side", "rear"]):
                    label = f"{brand_name}+{model_name.replace(' ', '+')}+{angle.capitalize()}"
                    color = ANGLE_COLORS[angle]
                    text_color = "FFFFFF" if angle != "side" else "FFFFFF"
                    url = f"https://placehold.co/900x650/{color}/FFFFFF?text={label}"
                    VehicleImage.objects.create(
                        vehicle=vehicle, image_url=url, angle=angle, order=order
                    )
                    total_images += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(VEHICLES)} vehicles with {total_images} images."))
        self.stdout.write(self.style.SUCCESS("Done. Create a superuser with 'python manage.py createsuperuser' to manage data from /admin/."))
