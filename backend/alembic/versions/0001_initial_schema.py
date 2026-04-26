"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-26

Esta es la migración baseline. Crea todas las tablas del modelo actual.

Si ya tienes una BD existente con datos, no apliques esta migración: en su lugar
marca la BD como ya migrada con:

    alembic stamp 0001

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(150), nullable=True, index=True),
        sa.Column("full_name", sa.String(150), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="cashier"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
        sa.Column("last_login", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── membership_plans ─────────────────────────────────────────────────────
    op.create_table(
        "membership_plans",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("duration_days", sa.Integer, nullable=False),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("max_entries_per_day", sa.Integer, nullable=True),
        sa.Column("allows_guest", sa.Boolean, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
        sa.Column("color", sa.String(7), server_default="#4CAF50"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── members ──────────────────────────────────────────────────────────────
    op.create_table(
        "members",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("member_number", sa.String(20), unique=True, index=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), nullable=True, index=True, unique=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("birth_date", sa.DateTime, nullable=True),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("emergency_contact", sa.String(150), nullable=True),
        sa.Column("emergency_phone", sa.String(20), nullable=True),
        sa.Column("photo_path", sa.String(255), nullable=True),
        sa.Column("face_enrolled", sa.Boolean, server_default=sa.text("0")),
        sa.Column("hikvision_card_no", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── product_categories ───────────────────────────────────────────────────
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
    )

    # ── products ─────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("sku", sa.String(50), unique=True, nullable=True),
        sa.Column("barcode", sa.String(50), nullable=True),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("cost", sa.Float, nullable=True),
        sa.Column("stock", sa.Integer, server_default="0"),
        sa.Column("min_stock", sa.Integer, server_default="5"),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("product_categories.id"), nullable=True),
        sa.Column("is_service", sa.Boolean, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
        sa.Column("image_path", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── hikvision_devices ────────────────────────────────────────────────────
    op.create_table(
        "hikvision_devices",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=False),
        sa.Column("port", sa.Integer, server_default="80"),
        sa.Column("username", sa.String(50), server_default="admin"),
        sa.Column("password", sa.String(100), nullable=False),
        sa.Column("device_type", sa.String(50), server_default="access_control"),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("direction", sa.String(10), server_default="both"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
        sa.Column("last_heartbeat", sa.DateTime, nullable=True),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("firmware", sa.String(50), nullable=True),
        sa.Column("face_lib_id", sa.String(50), server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── sales ────────────────────────────────────────────────────────────────
    op.create_table(
        "sales",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("sale_number", sa.String(20), unique=True, index=True),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=True),
        sa.Column("cashier", sa.String(100), nullable=True),
        sa.Column("subtotal", sa.Float, server_default="0"),
        sa.Column("discount", sa.Float, server_default="0"),
        sa.Column("tax", sa.Float, server_default="0"),
        sa.Column("total", sa.Float, server_default="0"),
        sa.Column("payment_method", sa.String(50), server_default="cash"),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), server_default="completed"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )

    # ── sale_items ───────────────────────────────────────────────────────────
    op.create_table(
        "sale_items",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("sale_id", sa.Integer, sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id"), nullable=True),
        sa.Column("product_name", sa.String(150), nullable=False),
        sa.Column("quantity", sa.Integer, server_default="1"),
        sa.Column("unit_price", sa.Float, nullable=False),
        sa.Column("discount", sa.Float, server_default="0"),
        sa.Column("total", sa.Float, nullable=False),
    )

    # ── member_memberships ───────────────────────────────────────────────────
    op.create_table(
        "member_memberships",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=False),
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("membership_plans.id"), nullable=False),
        sa.Column("start_date", sa.DateTime, nullable=False),
        sa.Column("end_date", sa.DateTime, nullable=False),
        sa.Column("price_paid", sa.Float, nullable=False),
        sa.Column("payment_method", sa.String(50), server_default="cash"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("sale_id", sa.Integer, sa.ForeignKey("sales.id"), nullable=True),
    )

    # ── access_logs ──────────────────────────────────────────────────────────
    op.create_table(
        "access_logs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("members.id"), nullable=True),
        sa.Column("device_id", sa.Integer, sa.ForeignKey("hikvision_devices.id"), nullable=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column("direction", sa.String(10), server_default="in"),
        sa.Column("access_type", sa.String(30), server_default="face"),
        sa.Column("result", sa.String(20), server_default="granted"),
        sa.Column("temperature", sa.Float, nullable=True),
        sa.Column("raw_event", sa.Text, nullable=True),
        sa.Column("capture_path", sa.String(255), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
    )

    # ── audit_logs ───────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("username", sa.String(50), nullable=True, index=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=True, index=True),
        sa.Column("entity_id", sa.String(50), nullable=True),
        sa.Column("summary", sa.String(255), nullable=True),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    for table in [
        "audit_logs", "access_logs", "member_memberships", "sale_items", "sales",
        "hikvision_devices", "products", "product_categories", "members",
        "membership_plans", "users",
    ]:
        op.drop_table(table)
