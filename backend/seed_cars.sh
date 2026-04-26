#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"

echo "🌱 Seeding cars via API..."
echo

# Owner credentials
OWNERS=(
    "owner1@test.com:Owner@1234"
    "owner2@test.com:Owner@1234"
    "owner3@test.com:Owner@1234"
)

# Get owner tokens
TOKENS=()
for OWNER_CRED in "${OWNERS[@]}"; do
    EMAIL=$(echo $OWNER_CRED | cut -d: -f1)
    PASSWORD=$(echo $OWNER_CRED | cut -d: -f2)

    TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
        | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

    if [ -z "$TOKEN" ]; then
        echo "❌ Failed to login $EMAIL"
    else
        echo "✅ Logged in as $EMAIL"
        TOKENS+=("$TOKEN")
    fi
done

echo
echo "Creating cars..."
echo

OWNER_IDX=0

# Car data in JSON format
create_car() {
    local TOKEN=$1
    local CAR_JSON=$2
    local INDEX=$3

    RESPONSE=$(curl -s -X POST "$BASE_URL/owner/cars" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$CAR_JSON")

    MAKE=$(echo $CAR_JSON | grep -o '"make":"[^"]*' | cut -d'"' -f4)
    MODEL=$(echo $CAR_JSON | grep -o '"model":"[^"]*' | cut -d'"' -f4)
    COLOR=$(echo $CAR_JSON | grep -o '"color":"[^"]*' | cut -d'"' -f4)
    CITY=$(echo $CAR_JSON | grep -o '"city":"[^"]*' | cut -d'"' -f4)

    if echo "$RESPONSE" | grep -q '"id"'; then
        echo "✅ Created $MAKE $MODEL ($COLOR) - $CITY"
    else
        echo "❌ Failed to create car: $RESPONSE"
    fi
}

# Cars array
cars=(
    '{"make":"Maruti","model":"Swift","variant":"LXi","year":2024,"color":"White","seating":5,"fuel_type":"petrol","transmission":"manual","mileage_kmpl":19.2,"city":"Hyderabad","state":"Telangana","address":"Kondapur, Hyderabad","price_per_hour":299,"price_per_day":1999,"security_deposit":5000,"registration_number":"TS09AB0001","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":false,"Climate Control":false}}'
    '{"make":"Maruti","model":"Swift","variant":"VXi","year":2023,"color":"Silver","seating":5,"fuel_type":"petrol","transmission":"automatic","mileage_kmpl":18.5,"city":"Hyderabad","state":"Telangana","address":"Jubilee Hills, Hyderabad","price_per_hour":399,"price_per_day":2499,"security_deposit":7000,"registration_number":"TS09AB0002","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
    '{"make":"Hyundai","model":"i20","variant":"Sportz","year":2024,"color":"Red","seating":5,"fuel_type":"petrol","transmission":"manual","mileage_kmpl":20.5,"city":"Bangalore","state":"Karnataka","address":"Indiranagar, Bangalore","price_per_hour":349,"price_per_day":2299,"security_deposit":6000,"registration_number":"KA05AB0003","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
    '{"make":"Tata","model":"Nexon","variant":"XE","year":2023,"color":"Black","seating":5,"fuel_type":"diesel","transmission":"manual","mileage_kmpl":17.3,"city":"Bangalore","state":"Karnataka","address":"Whitefield, Bangalore","price_per_hour":449,"price_per_day":2899,"security_deposit":8000,"registration_number":"KA05AB0004","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
    '{"make":"Honda","model":"City","variant":"SV","year":2024,"color":"Blue","seating":5,"fuel_type":"petrol","transmission":"manual","mileage_kmpl":18.2,"city":"Mumbai","state":"Maharashtra","address":"Andheri, Mumbai","price_per_hour":399,"price_per_day":2599,"security_deposit":7000,"registration_number":"MH02AB0005","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
    '{"make":"Hyundai","model":"Creta","variant":"SX","year":2023,"color":"White","seating":5,"fuel_type":"diesel","transmission":"automatic","mileage_kmpl":15.8,"city":"Mumbai","state":"Maharashtra","address":"Bandra, Mumbai","price_per_hour":599,"price_per_day":3999,"security_deposit":10000,"registration_number":"MH02AB0006","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
    '{"make":"Mahindra","model":"XUV500","variant":"W4","year":2022,"color":"Silver","seating":5,"fuel_type":"diesel","transmission":"manual","mileage_kmpl":14.5,"city":"Delhi","state":"Delhi","address":"Gurgaon, Delhi NCR","price_per_hour":649,"price_per_day":4299,"security_deposit":12000,"registration_number":"DL01AB0007","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
    '{"make":"Toyota","model":"Fortuner","variant":"4x2 MT","year":2023,"color":"Black","seating":7,"fuel_type":"diesel","transmission":"manual","mileage_kmpl":11.8,"city":"Delhi","state":"Delhi","address":"Noida, Delhi NCR","price_per_hour":999,"price_per_day":5999,"security_deposit":15000,"registration_number":"DL01AB0008","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
    '{"make":"Kia","model":"Seltos","variant":"HT","year":2024,"color":"Red","seating":5,"fuel_type":"petrol","transmission":"automatic","mileage_kmpl":16.5,"city":"Chennai","state":"Tamil Nadu","address":"T. Nagar, Chennai","price_per_hour":549,"price_per_day":3599,"security_deposit":9000,"registration_number":"TN07AB0009","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
    '{"make":"Maruti","model":"Ertiga","variant":"VXi","year":2023,"color":"Silver","seating":7,"fuel_type":"petrol","transmission":"manual","mileage_kmpl":16.3,"city":"Chennai","state":"Tamil Nadu","address":"Kodambakkam, Chennai","price_per_hour":349,"price_per_day":2299,"security_deposit":6000,"registration_number":"TN07AB0010","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":false,"Parking Sensors":true,"Climate Control":false}}'
    '{"make":"Maruti","model":"Baleno","variant":"Sigma","year":2024,"color":"Orange","seating":5,"fuel_type":"petrol","transmission":"manual","mileage_kmpl":19.0,"city":"Pune","state":"Maharashtra","address":"Baner, Pune","price_per_hour":299,"price_per_day":1999,"security_deposit":5000,"registration_number":"MH14AB0011","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
    '{"make":"MG","model":"Hector","variant":"Style","year":2023,"color":"Pearl White","seating":5,"fuel_type":"petrol","transmission":"automatic","mileage_kmpl":12.7,"city":"Pune","state":"Maharashtra","address":"Viman Nagar, Pune","price_per_hour":749,"price_per_day":4899,"security_deposit":11000,"registration_number":"MH14AB0012","features":{"Power Steering":true,"Power Windows":true,"Air Conditioning":true,"ABS":true,"Airbags":true,"Bluetooth":true,"USB Charging":true,"Touchscreen":true,"Parking Sensors":true,"Climate Control":true}}'
)

# Create cars
for car in "${cars[@]}"; do
    if [ ${#TOKENS[@]} -eq 0 ]; then
        echo "❌ No valid tokens available"
        break
    fi

    TOKEN=${TOKENS[$((OWNER_IDX % ${#TOKENS[@]}))]  }
    create_car "$TOKEN" "$car" "$OWNER_IDX"
    OWNER_IDX=$((OWNER_IDX + 1))
done

echo
echo "✅ Seeding complete!"
