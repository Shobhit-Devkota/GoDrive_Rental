from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from django.utils.text import slugify
from vehicles.models import Brand, Vehicle, VehicleImage, Destination

import os


# Each entry: (brand, model_name, folder_name_under_seed_images, fuel, transmission, seats, price, description)
VEHICLES = [
    ("BYD", "Atto 3", "byd_atto_3", "electric", "automatic", 5, 6500,
     "An all-electric SUV with a spacious cabin and long range, ideal for both city driving and longer trips."),
    ("Honda", "City", "honda_city", "petrol", "automatic", 5, 4800,
     "A well-balanced sedan offering a smooth automatic drive, popular for airport transfers and city tours."),
    ("Hyundai", "Creta", "hyundai_creta", "petrol", "automatic", 5, 5200,
     "A popular family SUV offering a smooth ride, generous boot space and modern safety features."),
    ("Kia", "Seltos", "kia_seltos", "petrol", "automatic", 5, 5400,
     "A stylish crossover SUV with a comfortable interior, great for both daily use and weekend getaways."),
    ("MG", "ZS", "mg_zs", "petrol", "automatic", 5, 5300,
     "A modern compact SUV with a feature-packed interior and a comfortable ride for city and highway driving."),
    ("Mahindra", "XUV300", "mahindra_xuv300", "diesel", "manual", 5, 4600,
     "The compact SUV with strong build quality and a punchy diesel engine, well suited to Nepal's hill roads."),
    ("Tata", "Nexon", "tata_nexon", "diesel", "manual", 5, 4200,
     "A rugged compact SUV built for Nepal's hill roads, offering a strong diesel engine and confident handling."),
    ("Tata", "Tiago", "tata_tiago", "petrol", "manual", 5, 3000,
     "A compact, fuel-efficient hatchback that's easy to park and drive around the city."),
    ("Toyota", "Hilux", "toyota_hilux", "diesel", "manual", 5, 7000,
     "A rugged double-cab pickup built for tough terrain, ideal for adventurous long-distance trips."),
    ("Suzuki", "Alto 800", "alto_800", "petrol", "manual", 4, 2500,
     "A compact, budget-friendly comfortable hatchback perfect for solo travelers and short city trips."),
]

# Each entry: (destination_name, extra_charge_per_day)
DESTINATIONS = [
    ("Kathmandu", 0),
    ("Pokhara", 1500),
    ("Chitwan", 1200),
    ("Lumbini", 1800),
    ("Bandipur", 1000),
    ("Nagarkot", 500),
    ("Dhulikhel", 700),
    ("Butwal", 1500),
]


class Command(BaseCommand):
    help = "Seed the database with real sample vehicles, photos, and destinations."
    ...  # rest of the file stays exactly the same

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help="Delete all existing vehicles/images before seeding fresh ones."
        )

    def handle(self, *args, **options):
        if options['reset']:
            VehicleImage.objects.all().delete()
            Vehicle.objects.all().delete()
            Brand.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing vehicles, images, and brands."))

        for name, extra in DESTINATIONS:
            Destination.objects.update_or_create(
                slug=slugify(name),
                defaults={"name": name, "extra_charge_per_day": extra}
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(DESTINATIONS)} destinations."))

        seed_images_dir = os.path.join(settings.BASE_DIR, 'vehicles', 'seed_images')
        total_images = 0

        for brand_name, model_name, folder, fuel, transmission, seats, price, desc in VEHICLES:
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
                folder_path = os.path.join(seed_images_dir, folder)
                if not os.path.isdir(folder_path):
                    self.stdout.write(self.style.WARNING(
                        f"No image folder found for {brand_name} {model_name} at {folder_path} — skipping images."
                    ))
                    continue

                image_files = sorted(os.listdir(folder_path))
                angles = ['front', 'side', 'rear', 'interior']

                for order, filename in enumerate(image_files):
                    file_path = os.path.join(folder_path, filename)
                    angle = angles[order] if order < len(angles) else 'front'
                    with open(file_path, 'rb') as f:
                        vehicle_image = VehicleImage(vehicle=vehicle, angle=angle, order=order)
                        vehicle_image.image.save(filename, File(f), save=True)
                    total_images += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(VEHICLES)} vehicles with {total_images} real photos."))
        self.stdout.write(self.style.SUCCESS("Done. Create a superuser with 'python manage.py createsuperuser' to manage data from /admin/."))
