"""Initial schema — all tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",              postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("full_name",       sa.String(120), nullable=False),
        sa.Column("email",           sa.String(255), unique=True, nullable=True),
        sa.Column("phone",           sa.String(20),  unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("role",            sa.Enum("customer","owner","admin", name="userrole"), nullable=False, server_default="customer"),
        sa.Column("is_active",       sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified",     sa.Boolean, nullable=False, server_default="false"),
        sa.Column("avatar_url",      sa.String(500), nullable=True),
        sa.Column("date_of_birth",   sa.DateTime(timezone=True), nullable=True),
        sa.Column("city",            sa.String(100), nullable=True),
        sa.Column("licence_number",  sa.String(50), nullable=True),
        sa.Column("licence_verified",sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at",      sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",      sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",      sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_phone", "users", ["phone"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role",  "users", ["role"])

    # ── refresh_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id",          postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id",     postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash",  sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at",  sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked",     sa.Boolean, nullable=False, server_default="false"),
        sa.Column("device_info", sa.String(255), nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── otp_codes ─────────────────────────────────────────────────────────────
    op.create_table(
        "otp_codes",
        sa.Column("id",         postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("phone",      sa.String(20),  nullable=False),
        sa.Column("code_hash",  sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used",    sa.Boolean, nullable=False, server_default="false"),
        sa.Column("purpose",    sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_otp_phone_expires", "otp_codes", ["phone", "expires_at"])

    # ── vehicles ──────────────────────────────────────────────────────────────
    op.create_table(
        "vehicles",
        sa.Column("id",                  postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("owner_id",            postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("make",                sa.String(80),  nullable=False),
        sa.Column("model",               sa.String(80),  nullable=False),
        sa.Column("variant",             sa.String(80),  nullable=True),
        sa.Column("year",                sa.Integer,     nullable=False),
        sa.Column("color",               sa.String(40),  nullable=False),
        sa.Column("seating",             sa.Integer,     nullable=False),
        sa.Column("fuel_type",           sa.Enum("petrol","diesel","electric","hybrid","cng", name="fueltype"), nullable=False),
        sa.Column("transmission",        sa.Enum("manual","automatic", name="transmission"), nullable=False),
        sa.Column("mileage_kmpl",        sa.Numeric(5,2), nullable=True),
        sa.Column("city",                sa.String(100), nullable=False),
        sa.Column("state",               sa.String(100), nullable=False),
        sa.Column("latitude",            sa.Numeric(9,6), nullable=True),
        sa.Column("longitude",           sa.Numeric(9,6), nullable=True),
        sa.Column("address",             sa.Text,        nullable=True),
        sa.Column("price_per_hour",      sa.Integer,     nullable=False),
        sa.Column("price_per_day",       sa.Integer,     nullable=False),
        sa.Column("security_deposit",    sa.Integer,     nullable=False, server_default="0"),
        sa.Column("registration_number", sa.String(20),  unique=True, nullable=False),
        sa.Column("rc_document_url",     sa.String(500), nullable=True),
        sa.Column("insurance_url",       sa.String(500), nullable=True),
        sa.Column("insurance_expiry",    sa.DateTime(timezone=True), nullable=True),
        sa.Column("status",              sa.Enum("draft","pending","active","suspended", name="carstatus"), nullable=False, server_default="draft"),
        sa.Column("kyc_status",          sa.Enum("pending","approved","rejected", name="kycstatus"), nullable=False, server_default="pending"),
        sa.Column("kyc_notes",           sa.Text, nullable=True),
        sa.Column("features",            postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("deleted_at",          sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("price_per_hour > 0",        name="ck_vehicles_price_per_hour_positive"),
        sa.CheckConstraint("price_per_day > 0",         name="ck_vehicles_price_per_day_positive"),
        sa.CheckConstraint("year >= 2000 AND year <= 2030", name="ck_vehicles_year_range"),
    )
    op.create_index("ix_vehicles_owner_id",           "vehicles", ["owner_id"])
    op.create_index("ix_vehicles_city_status",        "vehicles", ["city", "status"])
    op.create_index("ix_vehicles_fuel_transmission",  "vehicles", ["fuel_type", "transmission"])

    # ── vehicle_images ────────────────────────────────────────────────────────
    op.create_table(
        "vehicle_images",
        sa.Column("id",         postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url",        sa.String(500), nullable=False),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vehicle_images_vehicle_id", "vehicle_images", ["vehicle_id"])

    # ── bookings ──────────────────────────────────────────────────────────────
    op.create_table(
        "bookings",
        sa.Column("id",               postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("customer_id",      postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vehicle_id",       postgresql.UUID(as_uuid=False), sa.ForeignKey("vehicles.id"),  nullable=False),
        sa.Column("owner_id",         postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pickup_time",      sa.DateTime(timezone=True), nullable=False),
        sa.Column("dropoff_time",     sa.DateTime(timezone=True), nullable=False),
        sa.Column("pickup_address",   sa.Text, nullable=True),
        sa.Column("pickup_latitude",  sa.Numeric(9,6), nullable=True),
        sa.Column("pickup_longitude", sa.Numeric(9,6), nullable=True),
        sa.Column("base_amount",      sa.Integer, nullable=False),
        sa.Column("discount_amount",  sa.Integer, nullable=False, server_default="0"),
        sa.Column("tax_amount",       sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_amount",     sa.Integer, nullable=False),
        sa.Column("security_deposit", sa.Integer, nullable=False, server_default="0"),
        sa.Column("promo_code",       sa.String(30), nullable=True),
        sa.Column("status",           sa.Enum("pending","confirmed","active","completed","cancelled","disputed", name="bookingstatus"), nullable=False, server_default="pending"),
        sa.Column("odometer_start",   sa.Integer, nullable=True),
        sa.Column("odometer_end",     sa.Integer, nullable=True),
        sa.Column("cancelled_by",     sa.String(30), nullable=True),
        sa.Column("cancel_reason",    sa.Text, nullable=True),
        sa.Column("cancelled_at",     sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",       sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("dropoff_time > pickup_time", name="ck_bookings_time_order"),
        sa.CheckConstraint("total_amount >= 0",          name="ck_bookings_total_positive"),
    )
    op.create_index("ix_bookings_customer_id",    "bookings", ["customer_id"])
    op.create_index("ix_bookings_vehicle_id",     "bookings", ["vehicle_id"])
    op.create_index("ix_bookings_owner_id",       "bookings", ["owner_id"])
    op.create_index("ix_bookings_status",         "bookings", ["status"])
    op.create_index("ix_bookings_pickup_dropoff", "bookings", ["vehicle_id","pickup_time","dropoff_time"])

    # ── availability ──────────────────────────────────────────────────────────
    op.create_table(
        "availability",
        sa.Column("id",         postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time",   sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason",     sa.String(30), nullable=False, server_default="blocked"),
        sa.Column("booking_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("bookings.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="ck_availability_time_order"),
    )
    op.create_index("ix_availability_vehicle_time", "availability", ["vehicle_id","start_time","end_time"])

    # ── payments ──────────────────────────────────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("id",                  postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("booking_id",          postgresql.UUID(as_uuid=False), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gateway",             sa.Enum("razorpay","stripe", name="paymentgateway"), nullable=False),
        sa.Column("gateway_order_id",    sa.String(100), nullable=False),
        sa.Column("gateway_payment_id",  sa.String(100), unique=True, nullable=True),
        sa.Column("gateway_signature",   sa.String(500), nullable=True),
        sa.Column("amount",              sa.Integer, nullable=False),
        sa.Column("currency",            sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status",              sa.Enum("created","captured","failed","refunded", name="paymentstatus"), nullable=False, server_default="created"),
        sa.Column("refund_id",           sa.String(100), nullable=True),
        sa.Column("refunded_at",         sa.DateTime(timezone=True), nullable=True),
        sa.Column("refund_amount",       sa.Integer, nullable=False, server_default="0"),
        sa.Column("gateway_response",    postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at",          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_payments_booking_id",       "payments", ["booking_id"])
    op.create_index("ix_payments_gateway_order_id", "payments", ["gateway_order_id"])

    # ── reviews ───────────────────────────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id",          postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("booking_id",  postgresql.UUID(as_uuid=False), sa.ForeignKey("bookings.id"), unique=True, nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vehicle_id",  postgresql.UUID(as_uuid=False), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("rating",      sa.Integer, nullable=False),
        sa.Column("comment",     sa.Text, nullable=True),
        sa.Column("owner_reply", sa.Text, nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )
    op.create_index("ix_reviews_vehicle_id", "reviews", ["vehicle_id"])


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("payments")
    op.drop_table("availability")
    op.drop_table("bookings")
    op.drop_table("vehicle_images")
    op.drop_table("vehicles")
    op.drop_table("otp_codes")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    for enum in ["userrole","fueltype","transmission","carstatus","kycstatus","bookingstatus","paymentgateway","paymentstatus"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
