# Voyza Host (Owner) Mobile App

React Native mobile application for **car owners** on the Voyza platform. Built with **Expo** and **TypeScript**.

## Tech Stack

- **Expo SDK 52** - Managed React Native workflow
- **TypeScript** - Type-safe development
- **React Navigation 7** - Stack + Bottom Tab navigators
- **AsyncStorage** - Token persistence
- **Expo Image Picker** - Document & car image upload

## Features

### Authentication
- Phone OTP login & registration
- Automatic token refresh on 401
- Secure token storage

### Car Management
- List all cars with status badges (Draft, Pending, Active, Suspended)
- Create new car listings (starts as Draft)
- Upload car images via photo library
- Submit cars for admin KYC review
- Delete cars (if no active bookings)
- Block/unblock availability time slots

### Booking Management
- View all bookings across your fleet
- Filter by status: Pending, Confirmed, Active, Completed, Cancelled
- Accept pending bookings
- View customer details and earnings breakdown
- Platform fee shown (20%)

### Earnings
- Aggregated dashboard: Total, This Month, Pending Payout, Completed Bookings
- Monthly breakdown table

### KYC (Owner-specific)
- Upload Vehicle RC and Insurance
- View verification status
- Required before cars can be submitted for listing

## Project Structure

```
mobile-owner/
├── App.tsx
├── app.json                    # Expo config (bundle ID: com.voyza.owner)
├── src/
│   ├── navigation/
│   │   └── AppNavigator.tsx   # Auth stack + 5-tab bottom nav
│   ├── screens/
│   │   ├── SplashScreen.tsx
│   │   ├── LoginScreen.tsx
│   │   ├── RegisterScreen.tsx
│   │   ├── DashboardScreen.tsx     # Earnings summary + quick actions
│   │   ├── CarsScreen.tsx          # Car inventory + add/delete/submit
│   │   ├── AddCarScreen.tsx        # Full car creation form
│   │   ├── CarDetailScreen.tsx     # Details, images, availability
│   │   ├── AvailabilityScreen.tsx  # Block/unblock time slots
│   │   ├── BookingsScreen.tsx      # Filtered booking list
│   │   ├── BookingDetailScreen.tsx # Accept, customer info, earnings
│   │   ├── EarningsScreen.tsx      # Dashboard + monthly table
│   │   ├── ProfileScreen.tsx
│   │   ├── KycUploadScreen.tsx     # RC + Insurance upload
│   │   └── KycStatusScreen.tsx     # Verification status
│   ├── components/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   ├── StatusBadge.tsx
│   │   └── StatCard.tsx
│   ├── api/
│   │   └── client.ts               # Owner API endpoints
│   ├── constants/
│   │   └── theme.ts
│   ├── types/
│   │   └── index.ts
│   └── utils/
│       └── storage.ts
```

## Getting Started

```bash
cd mobile-owner
npm install
npx expo start
```

Press `i` for iOS Simulator, `a` for Android Emulator, or scan QR with **Expo Go**.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EXPO_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |

## Navigation Flow

```
Splash → Login/Register → Main Tabs
                              ├── Dashboard (stats + quick actions)
                              ├── Cars (list + add + manage)
                              ├── Bookings (filter + accept)
                              ├── Earnings (monthly breakdown)
                              └── Profile (KYC + logout)
```

## Key Owner API Endpoints Used

- `GET /owner/cars` — List cars
- `POST /owner/cars` — Create car
- `POST /owner/cars/{id}/submit` — Submit for review
- `POST /owner/cars/{id}/images` — Upload images
- `GET /owner/bookings` — List bookings
- `POST /owner/bookings/{id}/accept` — Accept booking
- `GET /owner/earnings` — Earnings summary
- `GET /owner/earnings/monthly` — Monthly breakdown
- `POST /owner/availability` — Block slots
- `POST /kyc/documents` — Upload KYC docs
