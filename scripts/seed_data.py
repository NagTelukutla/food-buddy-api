"""Seed JSON platform data and SQLite sample orders (development only)."""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.database.sqlite import get_session_factory, init_db
from app.models.order import Order, OrderItem
from app.utils.json_store import write_json_file

BASE = Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    return get_settings().data_path

CATEGORIES = [
    "Starters",
    "Soups",
    "Main Course",
    "Biryani",
    "Beverages",
    "Desserts",
]

MENU_ITEMS = [
    {"id": 1, "name": "Paneer Tikka", "description": "Grilled cottage cheese with spices", "price": 180, "image": "paneer-tikka.jpg", "available": True, "category": "Starters", "restaurant_id": 1},
    {"id": 2, "name": "Chicken 65", "description": "Spicy deep-fried chicken bites", "price": 220, "image": "chicken-65.jpg", "available": True, "category": "Starters", "restaurant_id": 1},
    {"id": 3, "name": "Veg Spring Rolls", "description": "Crispy rolls with vegetable filling", "price": 150, "image": "spring-rolls.jpg", "available": True, "category": "Starters", "restaurant_id": 1},
    {"id": 4, "name": "Fish Amritsari", "description": "Batter-fried fish with tangy spices", "price": 260, "image": "fish-amritsari.jpg", "available": True, "category": "Starters", "restaurant_id": 1},
    {"id": 5, "name": "Mushroom Pepper Fry", "description": "Sautéed mushrooms with black pepper", "price": 170, "image": "mushroom-pepper.jpg", "available": True, "category": "Starters", "restaurant_id": 1},
    {"id": 6, "name": "Tomato Soup", "description": "Classic creamy tomato soup", "price": 90, "image": "tomato-soup.jpg", "available": True, "category": "Soups", "restaurant_id": 1},
    {"id": 7, "name": "Sweet Corn Soup", "description": "Velvety sweet corn soup", "price": 95, "image": "corn-soup.jpg", "available": True, "category": "Soups", "restaurant_id": 1},
    {"id": 8, "name": "Hot & Sour Soup", "description": "Tangy Indo-Chinese soup", "price": 100, "image": "hot-sour-soup.jpg", "available": True, "category": "Soups", "restaurant_id": 1},
    {"id": 9, "name": "Mutton Bone Soup", "description": "Slow-cooked mutton broth", "price": 140, "image": "mutton-soup.jpg", "available": True, "category": "Soups", "restaurant_id": 1},
    {"id": 10, "name": "Dal Palak", "description": "Lentils cooked with spinach", "price": 160, "image": "dal-palak.jpg", "available": True, "category": "Main Course", "restaurant_id": 1},
    {"id": 11, "name": "Butter Chicken", "description": "Creamy tomato-based chicken curry", "price": 280, "image": "butter-chicken.jpg", "available": True, "category": "Main Course", "restaurant_id": 1},
    {"id": 12, "name": "Veg Kolhapuri", "description": "Spicy mixed vegetable curry", "price": 200, "image": "veg-kolhapuri.jpg", "available": True, "category": "Main Course", "restaurant_id": 1},
    {"id": 13, "name": "Fish Curry", "description": "Coastal style fish in coconut gravy", "price": 300, "image": "fish-curry.jpg", "available": True, "category": "Main Course", "restaurant_id": 1},
    {"id": 14, "name": "Paneer Butter Masala", "description": "Rich paneer in buttery gravy", "price": 240, "image": "paneer-butter.jpg", "available": True, "category": "Main Course", "restaurant_id": 1},
    {"id": 15, "name": "Egg Curry", "description": "Boiled eggs in spiced onion gravy", "price": 180, "image": "egg-curry.jpg", "available": True, "category": "Main Course", "restaurant_id": 1},
    {"id": 16, "name": "Chicken Biryani", "description": "Traditional Dum Biryani", "price": 220, "image": "chicken-biryani.jpg", "available": True, "category": "Biryani", "restaurant_id": 2},
    {"id": 17, "name": "Mutton Biryani", "description": "Aromatic mutton layered biryani", "price": 320, "image": "mutton-biryani.jpg", "available": True, "category": "Biryani", "restaurant_id": 2},
    {"id": 18, "name": "Veg Biryani", "description": "Fragrant vegetable biryani", "price": 180, "image": "veg-biryani.jpg", "available": True, "category": "Biryani", "restaurant_id": 2},
    {"id": 19, "name": "Egg Biryani", "description": "Spiced rice with boiled eggs", "price": 160, "image": "egg-biryani.jpg", "available": True, "category": "Biryani", "restaurant_id": 2},
    {"id": 20, "name": "Paneer Biryani", "description": "Cottage cheese dum biryani", "price": 200, "image": "paneer-biryani.jpg", "available": True, "category": "Biryani", "restaurant_id": 2},
    {"id": 21, "name": "Fresh Lime Soda", "description": "Chilled sweet or salted lime soda", "price": 60, "image": "lime-soda.jpg", "available": True, "category": "Beverages", "restaurant_id": 2},
    {"id": 22, "name": "Mango Lassi", "description": "Thick yogurt mango drink", "price": 80, "image": "mango-lassi.jpg", "available": True, "category": "Beverages", "restaurant_id": 2},
    {"id": 23, "name": "Masala Chai", "description": "Indian spiced tea", "price": 40, "image": "masala-chai.jpg", "available": True, "category": "Beverages", "restaurant_id": 2},
    {"id": 24, "name": "Cold Coffee", "description": "Blended iced coffee", "price": 90, "image": "cold-coffee.jpg", "available": True, "category": "Beverages", "restaurant_id": 2},
    {"id": 25, "name": "Mineral Water", "description": "500ml packaged water", "price": 30, "image": "water.jpg", "available": True, "category": "Beverages", "restaurant_id": 2},
    {"id": 26, "name": "Gulab Jamun", "description": "Milk dumplings in sugar syrup", "price": 80, "image": "gulab-jamun.jpg", "available": True, "category": "Desserts", "restaurant_id": 2},
    {"id": 27, "name": "Rasmalai", "description": "Soft cheese patties in saffron milk", "price": 100, "image": "rasmalai.jpg", "available": True, "category": "Desserts", "restaurant_id": 2},
    {"id": 28, "name": "Ice Cream Scoop", "description": "Choice of vanilla or chocolate", "price": 70, "image": "ice-cream.jpg", "available": True, "category": "Desserts", "restaurant_id": 2},
    {"id": 29, "name": "Brownie with Ice Cream", "description": "Warm brownie topped with ice cream", "price": 150, "image": "brownie.jpg", "available": True, "category": "Desserts", "restaurant_id": 2},
    {"id": 30, "name": "Fruit Salad", "description": "Seasonal fresh fruit bowl", "price": 90, "image": "fruit-salad.jpg", "available": True, "category": "Desserts", "restaurant_id": 2},
]

HERO_SLIDES = [
    {
        "title": "Welcome to Hotel Abhi ruchi",
        "subtitle": "Real taste of andhra — spices, soul, and tradition on every plate.",
        "cta_label": "Order Now",
        "cta_link": "/menu",
        "accent": "from-brand-900 to-brand-600",
        "image": "/slides/slide-1.svg",
    },
    {
        "title": "Signature Dum Biryani",
        "subtitle": "Slow-cooked layers of fragrant rice and authentic Andhra masala.",
        "cta_label": "Order Now",
        "cta_link": "/menu",
        "accent": "from-brand-800 to-amber-400",
        "image": "/slides/slide-2.svg",
    },
    {
        "title": "Dine In or Pickup",
        "subtitle": "Enjoy at our restaurant or order fresh food ready for pickup.",
        "cta_label": "Order Now",
        "cta_link": "/menu",
        "accent": "from-stone-800 to-brand-700",
        "image": "/slides/slide-3.svg",
    },
    {
        "title": "Fresh. Hot. Homestyle.",
        "subtitle": "Starters, biryanis, curries, and desserts made the Andhra way.",
        "cta_label": "View Menu",
        "cta_link": "/menu",
        "accent": "from-brand-900 to-dark-900",
        "image": "/slides/slide-4.svg",
    },
]

NOW = datetime.now(timezone.utc).isoformat()

SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin123")
SEED_SUPERADMIN_PASSWORD = os.getenv("SEED_SUPERADMIN_PASSWORD", "superadmin123")
SEED_DRIVER_PASSWORD = os.getenv("SEED_DRIVER_PASSWORD", "driver123")


def seed_json_files() -> None:
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    write_json_file(data_dir / "menu.json", {"items": MENU_ITEMS, "categories": CATEGORIES})

    write_json_file(
        data_dir / "users.json",
        {
            "users": [
                {
                    "id": 1,
                    "username": "admin",
                    "password_hash": get_password_hash(SEED_ADMIN_PASSWORD),
                    "full_name": "Restaurant Admin",
                    "email": "admin@spicegarden.com",
                    "phone": "+919876543210",
                    "role": "admin",
                    "restaurant_id": 1,
                    "branch_id": 1,
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                },
                {
                    "id": 2,
                    "username": "superadmin",
                    "password_hash": get_password_hash(SEED_SUPERADMIN_PASSWORD),
                    "full_name": "Super Admin",
                    "email": "superadmin@restaurant-platform.com",
                    "role": "platform",
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                },
                {
                    "id": 4,
                    "username": "admin2",
                    "password_hash": get_password_hash(SEED_ADMIN_PASSWORD),
                    "full_name": "Hotel TNR Grand Admin",
                    "email": "admin2@hoteltnrgrand.com",
                    "phone": "+919876543212",
                    "role": "admin",
                    "restaurant_id": 2,
                    "branch_id": 2,
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                },
                {
                    "id": 3,
                    "username": "driver1",
                    "password_hash": get_password_hash(SEED_DRIVER_PASSWORD),
                    "full_name": "Driver One",
                    "email": "driver1@spicegarden.com",
                    "phone": "+919876543211",
                    "role": "driver",
                    "restaurant_id": 1,
                    "branch_id": 1,
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                },
            ]
        },
    )

    write_json_file(
        data_dir / "settings.json",
        {
            "name": "Hotel Abhi ruchi",
            "tagline": "Real taste of andhra",
            "logo": "/logo.svg",
            "hero_image": "/hero.jpg",
            "about": "Hotel Abhi ruchi serves authentic Andhra cuisine with traditional recipes, fresh ingredients, and the real flavors of the region—every meal crafted to taste like home.",
            "address": "103, Sri Sai Enclave, PJR Nagar, Gachibowli, Hyderabad, Telangana 500032, India",
            "phone": "+919876543210",
            "email": "contact@hotelabhiruchi.com",
            "working_hours": "Tuesday – Sunday: 11 AM – 11 PM\nMonday: First half closed (5 PM – 11 PM)",
            "featured_dish_ids": [16, 11, 2, 26],
            "hero_slides": HERO_SLIDES,
            "restaurant_id": 1,
        },
    )

    write_json_file(
        data_dir / "restaurants.json",
        {
            "restaurants": [
                {
                    "id": 1,
                    "name": "Hotel Abhi ruchi",
                    "slug": "hotel-abhi-ruchi",
                    "tagline": "Real taste of andhra",
                    "description": "Hotel Abhi ruchi serves authentic Andhra cuisine with traditional recipes.",
                    "logo": "/logo.svg",
                    "hero_image": "/hero.jpg",
                    "hero_slides": HERO_SLIDES,
                    "email": "contact@hotelabhiruchi.com",
                    "phone": "+919876543210",
                    "address": "103, Sri Sai Enclave, PJR Nagar, Gachibowli, Hyderabad, Telangana 500032, India",
                    "latitude": 17.435886,
                    "longitude": 78.3618,
                    "cuisine_type": "Andhra",
                    "working_hours": "Tuesday – Sunday: 11 AM – 11 PM",
                    "owner_user_id": 1,
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                },
                {
                    "id": 2,
                    "name": "Hotel TNR Grand",
                    "slug": "hotel-tnr-grand",
                    "tagline": "Grand flavors, grand experience",
                    "description": "Hotel TNR Grand serves premium South Indian cuisine with exceptional hospitality.",
                    "logo": "/logo.svg",
                    "hero_image": "/hero.jpg",
                    "hero_slides": HERO_SLIDES,
                    "email": "contact@hoteltnrgrand.com",
                    "phone": "+919876543212",
                    "address": "12 MG Road, Hyderabad, Telangana 500001, India",
                    "latitude": 17.4401,
                    "longitude": 78.3489,
                    "cuisine_type": "South Indian",
                    "working_hours": "Daily: 11 AM – 11 PM",
                    "owner_user_id": 4,
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                },
            ]
        },
    )

    write_json_file(
        data_dir / "branches.json",
        {
            "branches": [
                {
                    "id": 1,
                    "restaurant_id": 1,
                    "name": "Gachibowli Main",
                    "address": "103, Sri Sai Enclave, PJR Nagar, Gachibowli, Hyderabad, Telangana 500032, India",
                    "phone": "+919876543210",
                    "email": "contact@hotelabhiruchi.com",
                    "working_hours": "Tuesday – Sunday: 11 AM – 11 PM",
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                },
                {
                    "id": 2,
                    "restaurant_id": 2,
                    "name": "TNR Grand Main",
                    "address": "12 MG Road, Hyderabad, Telangana 500001, India",
                    "phone": "+919876543212",
                    "email": "contact@hoteltnrgrand.com",
                    "working_hours": "Daily: 11 AM – 11 PM",
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                },
            ]
        },
    )

    write_json_file(data_dir / "customers.json", {"customers": []})
    write_json_file(
        data_dir / "delivery.json",
        {
            "partners": [
                {
                    "id": 1,
                    "restaurant_id": 1,
                    "name": "Driver One",
                    "phone": "+919876543211",
                    "user_id": 3,
                    "vehicle_type": "bike",
                    "vehicle_number": "KA-01-DR-001",
                    "status": "available",
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                }
            ],
            "assignments": [],
            "driver_locations": [],
        },
    )
    write_json_file(data_dir / "loyalty_points.json", {"transactions": []})
    write_json_file(data_dir / "campaigns.json", {"campaigns": []})
    write_json_file(
        data_dir / "reviews.json",
        {
            "reviews": [
                {
                    "id": 1,
                    "order_id": "ORD-TENANT-2",
                    "restaurant_id": 2,
                    "customer_id": None,
                    "rating": 5,
                    "comment": "Excellent biryani at Hotel TNR Grand.",
                    "owner_response": None,
                    "created_at": NOW,
                    "updated_at": NOW,
                }
            ]
        },
    )
    write_json_file(data_dir / "order_metadata.json", {"metadata": []})
    write_json_file(
        data_dir / "platform_settings.json",
        {
            "platform_name": "Restaurant Direct Ordering Platform",
            "default_tax_rate": 0.05,
            "loyalty_points_per_rupee": 0.1,
            "order_id_prefix": "ORD",
            "featured_restaurant_ids": [1],
            "maintenance_mode": False,
            "updated_at": NOW,
        },
    )
    write_json_file(data_dir / "payments.json", {"payments": []})


def seed_sqlite_orders() -> None:
    data_dir = get_data_dir()
    init_db()
    session = get_session_factory()()
    try:
        if session.query(Order).count() > 0:
            return
        now = datetime.now(timezone.utc)
        samples = [
            {
                "order_id": "ORD-20260001",
                "customer_name": "Rahul Sharma",
                "phone": "9876543210",
                "table_number": "T5",
                "order_type": "Dine In",
                "notes": "Less spicy",
                "status": "Delivered",
                "items": [(16, 2), (21, 2)],
                "offset_hours": 5,
            },
            {
                "order_id": "ORD-20260002",
                "customer_name": "Priya Nair",
                "phone": "9123456780",
                "table_number": None,
                "order_type": "Pickup",
                "notes": None,
                "status": "Preparing",
                "items": [(11, 1), (22, 1), (26, 2)],
                "offset_hours": 2,
            },
            {
                "order_id": "ORD-20260003",
                "customer_name": "Amit Patel",
                "phone": "9988776655",
                "table_number": "T12",
                "order_type": "Dine In",
                "notes": "Extra napkins",
                "status": "Pending",
                "items": [(17, 1), (6, 2)],
                "offset_hours": 0,
            },
            {
                "order_id": "ORD-20260004",
                "customer_name": "Sneha Reddy",
                "phone": "9012345678",
                "table_number": None,
                "order_type": "Pickup",
                "notes": None,
                "status": "Accepted",
                "items": [(18, 2), (23, 2)],
                "offset_hours": 1,
            },
            {
                "order_id": "ORD-20260005",
                "customer_name": "Vikram Singh",
                "phone": "9876501234",
                "table_number": "T3",
                "order_type": "Dine In",
                "notes": None,
                "status": "Ready",
                "items": [(2, 1), (16, 1), (24, 1)],
                "offset_hours": 3,
            },
        ]
        menu_map = {item["id"]: item for item in MENU_ITEMS}
        tax_rate = 0.05
        for sample in samples:
            created_at = now - timedelta(hours=sample["offset_hours"])
            subtotal = 0.0
            order_items = []
            for menu_id, qty in sample["items"]:
                menu = menu_map[menu_id]
                line_total = menu["price"] * qty
                subtotal += line_total
                order_items.append(
                    OrderItem(
                        menu_item_id=menu_id,
                        name=menu["name"],
                        price=menu["price"],
                        quantity=qty,
                        line_total=line_total,
                    )
                )
            tax = round(subtotal * tax_rate, 2)
            total = round(subtotal + tax, 2)
            order = Order(
                order_id=sample["order_id"],
                customer_name=sample["customer_name"],
                phone=sample["phone"],
                table_number=sample["table_number"],
                order_type=sample["order_type"],
                notes=sample["notes"],
                status=sample["status"],
                subtotal=subtotal,
                tax=tax,
                total=total,
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(order)
            session.flush()
            for item in order_items:
                item.order_id = order.id
                session.add(item)
        session.commit()
        metadata_entries = [
            {"order_id": sample["order_id"], "restaurant_id": 1}
            for sample in samples
        ]
        write_json_file(
            data_dir / "order_metadata.json",
            {
                "metadata": [
                    {
                        "id": idx + 1,
                        "order_id": entry["order_id"],
                        "restaurant_id": entry["restaurant_id"],
                        "created_at": NOW,
                        "updated_at": NOW,
                    }
                    for idx, entry in enumerate(metadata_entries)
                ]
            },
        )
    finally:
        session.close()


if __name__ == "__main__":
    if get_settings().is_production:
        print("Refusing to seed in production. Run locally with APP_ENV=development.")
        sys.exit(1)
    seed_json_files()
    seed_sqlite_orders()
    print("Seed data created successfully.")
