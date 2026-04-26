#!/usr/bin/env python3

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models import User, Vehicle, VehicleImage, VehicleStatus, KYCStatus


def uid():
    return str(uuid4())


def now_utc():
    return datetime.now(timezone.utc)


# Popular Indian car data
CARS_DATA = [
    # Hyderabad - Maruti Swift variants
    {
        "make": "Maruti",
        "model": "Swift",
        "variant": "LXi",
        "year": 2024,
        "color": "White",
        "seating": 5,
        "fuel_type": "petrol",
        "transmission": "manual",
        "mileage_kmpl": 19.2,
        "city": "Hyderabad",
        "state": "Telangana",
        "address": "Kondapur, Hyderabad",
        "price_per_hour": 299,
        "price_per_day": 1999,
        "security_deposit": 5000,
        "registration_number": "TS09AB0001",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": False,
            "Climate Control": False
        },
        "images": [
            "https://images.unsplash.com/photo-1552820728-8ac41f1ce891?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1527524330007-3348d2fb7d3c?w=800&h=600&fit=crop",
        ]
    },
    {
        "make": "Maruti",
        "model": "Swift",
        "variant": "VXi",
        "year": 2023,
        "color": "Silver",
        "seating": 5,
        "fuel_type": "petrol",
        "transmission": "automatic",
        "mileage_kmpl": 18.5,
        "city": "Hyderabad",
        "state": "Telangana",
        "address": "Jubilee Hills, Hyderabad",
        "price_per_hour": 399,
        "price_per_day": 2499,
        "security_deposit": 7000,
        "registration_number": "TS09AB0002",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1619405399517-d4af42fc2eec?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1489824904134-891ab64532f1?w=800&h=600&fit=crop",
        ]
    },
    # Bangalore - Hyundai i20
    {
        "make": "Hyundai",
        "model": "i20",
        "variant": "Sportz",
        "year": 2024,
        "color": "Red",
        "seating": 5,
        "fuel_type": "petrol",
        "transmission": "manual",
        "mileage_kmpl": 20.5,
        "city": "Bangalore",
        "state": "Karnataka",
        "address": "Indiranagar, Bangalore",
        "price_per_hour": 349,
        "price_per_day": 2299,
        "security_deposit": 6000,
        "registration_number": "KA05AB0003",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1609687552384-f87e74c87b98?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1616048424556-0d0f29e6a84f?w=800&h=600&fit=crop",
        ]
    },
    # Bangalore - Tata Nexon
    {
        "make": "Tata",
        "model": "Nexon",
        "variant": "XE",
        "year": 2023,
        "color": "Black",
        "seating": 5,
        "fuel_type": "diesel",
        "transmission": "manual",
        "mileage_kmpl": 17.3,
        "city": "Bangalore",
        "state": "Karnataka",
        "address": "Whitefield, Bangalore",
        "price_per_hour": 449,
        "price_per_day": 2899,
        "security_deposit": 8000,
        "registration_number": "KA05AB0004",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1517654711202-7a8ca3a50d60?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1619405399517-d4af42fc2eec?w=800&h=600&fit=crop",
        ]
    },
    # Mumbai - Honda City
    {
        "make": "Honda",
        "model": "City",
        "variant": "SV",
        "year": 2024,
        "color": "Blue",
        "seating": 5,
        "fuel_type": "petrol",
        "transmission": "manual",
        "mileage_kmpl": 18.2,
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Andheri, Mumbai",
        "price_per_hour": 399,
        "price_per_day": 2599,
        "security_deposit": 7000,
        "registration_number": "MH02AB0005",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1485123899351-287201d5d01d?w=800&h=600&fit=crop",
        ]
    },
    # Mumbai - Hyundai Creta
    {
        "make": "Hyundai",
        "model": "Creta",
        "variant": "SX",
        "year": 2023,
        "color": "White",
        "seating": 5,
        "fuel_type": "diesel",
        "transmission": "automatic",
        "mileage_kmpl": 15.8,
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Bandra, Mumbai",
        "price_per_hour": 599,
        "price_per_day": 3999,
        "security_deposit": 10000,
        "registration_number": "MH02AB0006",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1609687552384-f87e74c87b98?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1617654711202-7a8ca3a50d60?w=800&h=600&fit=crop",
        ]
    },
    # Delhi - Mahindra XUV500
    {
        "make": "Mahindra",
        "model": "XUV500",
        "variant": "W4",
        "year": 2022,
        "color": "Silver",
        "seating": 5,
        "fuel_type": "diesel",
        "transmission": "manual",
        "mileage_kmpl": 14.5,
        "city": "Delhi",
        "state": "Delhi",
        "address": "Gurgaon, Delhi NCR",
        "price_per_hour": 649,
        "price_per_day": 4299,
        "security_deposit": 12000,
        "registration_number": "DL01AB0007",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1611095461589-cc0e61d8bbb6?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1609687552384-f87e74c87b98?w=800&h=600&fit=crop",
        ]
    },
    # Delhi - Toyota Fortuner
    {
        "make": "Toyota",
        "model": "Fortuner",
        "variant": "4x2 MT",
        "year": 2023,
        "color": "Black",
        "seating": 7,
        "fuel_type": "diesel",
        "transmission": "manual",
        "mileage_kmpl": 11.8,
        "city": "Delhi",
        "state": "Delhi",
        "address": "Noida, Delhi NCR",
        "price_per_hour": 999,
        "price_per_day": 5999,
        "security_deposit": 15000,
        "registration_number": "DL01AB0008",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1619405399517-d4af42fc2eec?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1517654711202-7a8ca3a50d60?w=800&h=600&fit=crop",
        ]
    },
    # Chennai - Kia Seltos
    {
        "make": "Kia",
        "model": "Seltos",
        "variant": "HT",
        "year": 2024,
        "color": "Red",
        "seating": 5,
        "fuel_type": "petrol",
        "transmission": "automatic",
        "mileage_kmpl": 16.5,
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": "T. Nagar, Chennai",
        "price_per_hour": 549,
        "price_per_day": 3599,
        "security_deposit": 9000,
        "registration_number": "TN07AB0009",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1609687552384-f87e74c87b98?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1517654711202-7a8ca3a50d60?w=800&h=600&fit=crop",
        ]
    },
    # Chennai - Maruti Ertiga
    {
        "make": "Maruti",
        "model": "Ertiga",
        "variant": "VXi",
        "year": 2023,
        "color": "Silver",
        "seating": 7,
        "fuel_type": "petrol",
        "transmission": "manual",
        "mileage_kmpl": 16.3,
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": "Kodambakkam, Chennai",
        "price_per_hour": 349,
        "price_per_day": 2299,
        "security_deposit": 6000,
        "registration_number": "TN07AB0010",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": False,
            "Parking Sensors": True,
            "Climate Control": False
        },
        "images": [
            "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1616048424556-0d0f29e6a84f?w=800&h=600&fit=crop",
        ]
    },
    # Pune - Maruti Baleno
    {
        "make": "Maruti",
        "model": "Baleno",
        "variant": "Sigma",
        "year": 2024,
        "color": "Orange",
        "seating": 5,
        "fuel_type": "petrol",
        "transmission": "manual",
        "mileage_kmpl": 19.0,
        "city": "Pune",
        "state": "Maharashtra",
        "address": "Baner, Pune",
        "price_per_hour": 299,
        "price_per_day": 1999,
        "security_deposit": 5000,
        "registration_number": "MH14AB0011",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1552820728-8ac41f1ce891?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1609687552384-f87e74c87b98?w=800&h=600&fit=crop",
        ]
    },
    # Pune - MG Hector
    {
        "make": "MG",
        "model": "Hector",
        "variant": "Style",
        "year": 2023,
        "color": "Pearl White",
        "seating": 5,
        "fuel_type": "petrol",
        "transmission": "automatic",
        "mileage_kmpl": 12.7,
        "city": "Pune",
        "state": "Maharashtra",
        "address": "Viman Nagar, Pune",
        "price_per_hour": 749,
        "price_per_day": 4899,
        "security_deposit": 11000,
        "registration_number": "MH14AB0012",
        "features": {
            "Power Steering": True,
            "Power Windows": True,
            "Air Conditioning": True,
            "ABS": True,
            "Airbags": True,
            "Bluetooth": True,
            "USB Charging": True,
            "Touchscreen": True,
            "Parking Sensors": True,
            "Climate Control": True
        },
        "images": [
            "https://images.unsplash.com/photo-1619405399517-d4af42fc2eec?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1611095461589-cc0e61d8bbb6?w=800&h=600&fit=crop",
        ]
    },
]


async def seed():
    engine = create_async_engine(settings.async_database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        print("🌱 Seeding database...")

        # Create users
        admin = User(
            id=uid(),
            full_name="Admin",
            phone="+919000000001",
            email="admin@test.com",
            hashed_password=hash_password("Admin@1234"),
            role="admin",
            is_active=True,
            is_verified=True,
        )

        owner1 = User(
            id=uid(),
            full_name="Rajesh Kumar",
            phone="+919876543210",
            email="owner1@test.com",
            hashed_password=hash_password("Owner@1234"),
            role="owner",
            is_active=True,
            is_verified=True,
        )

        owner2 = User(
            id=uid(),
            full_name="Priya Sharma",
            phone="+919876543211",
            email="owner2@test.com",
            hashed_password=hash_password("Owner@1234"),
            role="owner",
            is_active=True,
            is_verified=True,
        )

        owner3 = User(
            id=uid(),
            full_name="Amit Patel",
            phone="+919876543212",
            email="owner3@test.com",
            hashed_password=hash_password("Owner@1234"),
            role="owner",
            is_active=True,
            is_verified=True,
        )

        customer = User(
            id=uid(),
            full_name="Customer",
            phone="+919834567890",
            email="customer@test.com",
            hashed_password=hash_password("Customer@1234"),
            role="customer",
            is_active=True,
            is_verified=True,
        )

        db.add_all([admin, owner1, owner2, owner3, customer])
        await db.commit()

        # Create vehicles
        owners = [owner1, owner2, owner3]
        owner_index = 0

        for car_data in CARS_DATA:
            owner = owners[owner_index % len(owners)]
            owner_index += 1

            vehicle = Vehicle(
                id=uid(),
                owner_id=owner.id,
                make=car_data["make"],
                model=car_data["model"],
                variant=car_data.get("variant"),
                year=car_data["year"],
                color=car_data["color"],
                seating=car_data["seating"],
                fuel_type=car_data["fuel_type"],
                transmission=car_data["transmission"],
                mileage_kmpl=car_data.get("mileage_kmpl"),
                city=car_data["city"],
                state=car_data["state"],
                address=car_data.get("address"),
                price_per_hour=car_data["price_per_hour"],
                price_per_day=car_data["price_per_day"],
                security_deposit=car_data["security_deposit"],
                registration_number=car_data["registration_number"],
                status=VehicleStatus.ACTIVE,
                kyc_status=KYCStatus.APPROVED,
                features=car_data["features"],
            )

            # Add images
            for idx, image_url in enumerate(car_data.get("images", [])):
                image = VehicleImage(
                    id=uid(),
                    vehicle_id=vehicle.id,
                    url=image_url,
                    is_primary=(idx == 0),
                    sort_order=idx,
                )
                vehicle.images.append(image)

            db.add(vehicle)

        await db.commit()

        print(f"✅ Seeded {len(CARS_DATA)} vehicles with 4 owners!")
        print("✅ Seeding complete!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
