from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.sqlite import Base


def utc_now():
    return datetime.now(timezone.utc)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(String(32), unique=True, index=True, nullable=False)
    customer_name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    table_number = Column(String(20), nullable=True)
    order_type = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="Pending")
    payment_status = Column(String(20), nullable=False, default="unpaid")
    razorpay_order_id = Column(String(64), nullable=True)
    subtotal = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(Integer, nullable=False)
    name = Column(String(120), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    line_total = Column(Float, nullable=False, default=0.0)

    order = relationship("Order", back_populates="items")
