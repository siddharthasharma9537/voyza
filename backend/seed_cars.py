#!/usr/bin/env python3
"""
Direct seeding script using raw SQL via HTTP API calls
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Credentials for owner accounts
OWNERS = [
    {"email": "owner1@test.com", "password": "Owner@1234"},
    {"email": "owner2@test.com", "password": "Owner@1234"},
    {"email": "owner3@test.com", "password": "Owner@1234"},
]

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
    },
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
    },
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
    },
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
    },
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
    },
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
    },
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
    },
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
    },
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
    },
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
    },
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
    },
]


def login_owner(email, password):
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
    )
    if response.status_code != 200:
        print(f"❌ Failed to login {email}: {response.text}")
        return None
    return response.json().get("access_token")


def create_car(token, car_data):
    """Create a car via API"""
    headers = {"Authorization": f"Bearer {token}"}

    # Create vehicle
    car_payload = {
        "make": car_data["make"],
        "model": car_data["model"],
        "variant": car_data.get("variant"),
        "year": car_data["year"],
        "color": car_data["color"],
        "seating": car_data["seating"],
        "fuel_type": car_data["fuel_type"],
        "transmission": car_data["transmission"],
        "mileage_kmpl": car_data.get("mileage_kmpl"),
        "city": car_data["city"],
        "state": car_data["state"],
        "address": car_data.get("address"),
        "price_per_hour": car_data["price_per_hour"],
        "price_per_day": car_data["price_per_day"],
        "security_deposit": car_data["security_deposit"],
        "registration_number": car_data["registration_number"],
        "features": car_data.get("features", {}),
    }

    response = requests.post(
        f"{BASE_URL}/owner/cars",
        headers=headers,
        json=car_payload,
    )

    if response.status_code != 201:
        print(f"❌ Failed to create {car_data['make']} {car_data['model']}: {response.text}")
        return None

    car_id = response.json().get("id")
    print(f"✅ Created {car_data['make']} {car_data['model']} ({car_data['color']}) - {car_data['city']}")
    return car_id


def main():
    print("🌱 Seeding cars via API...")
    print()

    # Get owner tokens
    owner_tokens = []
    for owner_cred in OWNERS:
        token = login_owner(owner_cred["email"], owner_cred["password"])
        if token:
            owner_tokens.append(token)
            print(f"✅ Logged in as {owner_cred['email']}")

    if not owner_tokens:
        print("❌ Failed to login to any owner account")
        return

    print()
    print("Creating cars...")

    # Create cars
    owner_idx = 0
    for car_data in CARS_DATA:
        token = owner_tokens[owner_idx % len(owner_tokens)]
        create_car(token, car_data)
        owner_idx += 1

    print()
    print(f"✅ Seeding complete! Added {len(CARS_DATA)} cars")


if __name__ == "__main__":
    main()
