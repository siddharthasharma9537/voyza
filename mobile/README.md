# Voyza Mobile App

React Native mobile application for the Voyza car rental platform, built with **Expo** and **TypeScript**.

## Tech Stack

- **Expo SDK 52** - React Native framework with managed workflow
- **TypeScript** - Type-safe development
- **React Navigation 7** - Stack + Bottom Tab navigators
- **AsyncStorage** - Local token persistence
- **Expo Image Picker** - KYC document upload from photo library

## Features

### Authentication
- Phone OTP login & registration
- Automatic token refresh on 401 responses
- Secure token storage with AsyncStorage

### Car Rental Flow
- Browse cars by city with filterable listings
- Car detail with specs, features, and reviews
- Checkout with promo code and pricing breakdown
- Payment simulation (Razorpay integration ready)
- Booking history with status tracking
- Post-trip reviews

### KYC Verification (Phase 3)
- Document upload (Driving License, Aadhar, Selfie)
- Upload via photo library using Expo Image Picker
- View verification status
- Admin review workflow via backend API

### Tracking
- Live GPS tracking via WebSocket (placeholder map)

## Project Structure

```
mobile/
├── App.tsx                       # Entry point with SafeAreaProvider
├── app.json                      # Expo configuration
├── src/
│   ├── navigation/
│   │   └── AppNavigator.tsx     # Stack + Bottom Tab navigators
│   ├── screens/
│   │   ├── SplashScreen.tsx     # Animated splash with auth check
│   │   ├── LoginScreen.tsx      # Phone OTP login
│   │   ├── RegisterScreen.tsx   # Phone OTP registration
│   │   ├── HomeScreen.tsx       # Featured cars by city
│   │   ├── BrowseScreen.tsx     # Filterable car listings
│   │   ├── CarDetailScreen.tsx  # Car specs, reviews, book CTA
│   │   ├── CheckoutScreen.tsx   # Date/promo/pricing
│   │   ├── PaymentScreen.tsx    # Razorpay payment simulation
│   │   ├── BookingSuccessScreen.tsx
│   │   ├── BookingsScreen.tsx   # Trip history
│   │   ├── ReviewScreen.tsx     # Rate & comment
│   │   ├── TrackingScreen.tsx   # Live GPS via WebSocket
│   │   ├── ProfileScreen.tsx    # User info, KYC, logout
│   │   ├── KycUploadScreen.tsx  # Document photo upload
│   │   └── KycStatusScreen.tsx  # Verification status
│   ├── components/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── CarCard.tsx          # Reusable car browse card
│   │   ├── Tag.tsx              # Filter chip
│   │   ├── Card.tsx
│   │   ├── StatusBadge.tsx      # Booking status badge
│   │   └── StarRow.tsx          # Rating stars
│   ├── api/
│   │   └── client.ts             # Typed API client with auto-refresh
│   ├── constants/
│   │   └── theme.ts              # Colors & typography tokens
│   ├── types/
│   │   └── index.ts              # Shared TypeScript interfaces
│   └── utils/
│       └── storage.ts            # AsyncStorage wrapper
```

## Getting Started

### Prerequisites
- Node.js 18+
- Expo Go app on iOS/Android device (for physical testing)
- Or iOS Simulator / Android Emulator

### Installation

```bash
# From the repo root
npm install
```

### Running the App

```bash
# Start the Expo development server
npx expo start

# Press `i` for iOS Simulator
# Press `a` for Android Emulator
# Or scan the QR code with Expo Go on your phone
```

### Connecting to Backend

The API client defaults to `http://localhost:8000`. To point at a deployed backend, set:

```bash
EXPO_PUBLIC_API_URL=https://api.yourdomain.com npx expo start
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EXPO_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

## Navigation Flow

```
Splash → (token check) → Login/Register → Main Tabs
                                    |
                                    └→ Home (featured cars)
                                    └→ Browse (filterable list) → CarDetail → Checkout → Payment → BookingSuccess
                                    └→ Bookings (history) → Review / Tracking
                                    └→ Profile → KycUpload / KycStatus
```

## Out of Scope

- Owner dashboard (business-facing, web-only)
- Admin KYC review panel (web-only)
- Razorpay native SDK (requires development build; simulated now)
- Real-time map rendering (react-native-maps placeholder ready)
