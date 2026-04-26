"""
app/models/models.py
────────────────────
Central re-export of all ORM models.

Car / CarStatus / CarImage are legacy aliases for Vehicle / VehicleStatus /
VehicleImage — used throughout services until a full rename is done.
"""

from app.models.booking import Booking, BookingStatus, Review
from app.models.checklist import ChecklistItem, ChecklistType
from app.models.driver import Driver, DriverStatus, LicenseClass
from app.models.kyc import (
    DamageReport,
    DamageReportStatus,
    DamageType,
    DocumentStatus,
    DocumentType,
    KYCDocument,
)
from app.models.notification import Notification, NotificationChannel, NotificationStatus, NotificationType
from app.models.payment import Payment, PaymentGateway, PaymentStatus
from app.models.refund import Refund, RefundReason, RefundStatus
from app.models.ride import Ride, RideStatus
from app.models.user import OTPCode, RefreshToken, User, UserRole
from app.models.vehicle import (
    Availability,
    FuelType,
    KYCStatus,
    Transmission,
    Vehicle,
    VehicleImage,
    VehicleStatus,
)

# Legacy aliases — many services still reference these names
Car = Vehicle
CarStatus = VehicleStatus
CarImage = VehicleImage

__all__ = [
    "Availability",
    "Booking",
    "BookingStatus",
    "Car",
    "CarImage",
    "CarStatus",
    "ChecklistItem",
    "ChecklistType",
    "DamageReport",
    "DamageReportStatus",
    "DamageType",
    "DocumentStatus",
    "DocumentType",
    "Driver",
    "DriverStatus",
    "FuelType",
    "KYCDocument",
    "KYCStatus",
    "LicenseClass",
    "Notification",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationType",
    "OTPCode",
    "Payment",
    "PaymentGateway",
    "PaymentStatus",
    "Refund",
    "RefundReason",
    "RefundStatus",
    "RefreshToken",
    "Review",
    "Ride",
    "RideStatus",
    "Transmission",
    "User",
    "UserRole",
    "Vehicle",
    "VehicleImage",
    "VehicleStatus",
]
