from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class Customer(db.Model):
    __tablename__ = 'customers'
    id: Mapped[int] = mapped_column(primary_key=True)
    mobile_number: Mapped[str] = mapped_column(db.String(10), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    address: Mapped[str] = mapped_column(db.Text, nullable=False)
    facebook_completed: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    instagram_completed: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    whatsapp_completed: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow, nullable=False)
    spin: Mapped['Spin | None'] = relationship(back_populates='customer', uselist=False, cascade='all, delete-orphan')


class Prize(db.Model):
    __tablename__ = 'prizes'
    id: Mapped[str] = mapped_column(db.String(64), primary_key=True)
    title: Mapped[str] = mapped_column(db.String(160), nullable=False)
    description: Mapped[str] = mapped_column(db.String(500), nullable=False)
    image_url: Mapped[str] = mapped_column(db.String(255), nullable=False)
    weight: Mapped[int] = mapped_column(db.Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    __table_args__ = (CheckConstraint('weight > 0', name='ck_prizes_positive_weight'),)


class Spin(db.Model):
    __tablename__ = 'spins'
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id', ondelete='CASCADE'), unique=True, nullable=False)
    prize_id: Mapped[str] = mapped_column(ForeignKey('prizes.id'), nullable=False)
    mobile_number: Mapped[str] = mapped_column(db.String(10), unique=True, nullable=False)
    spin_time: Mapped[datetime] = mapped_column(default=utcnow, nullable=False, index=True)
    status: Mapped[str] = mapped_column(db.String(32), default='completed', nullable=False)
    customer: Mapped[Customer] = relationship(back_populates='spin')
    prize: Mapped[Prize] = relationship()
    __table_args__ = (
        UniqueConstraint('customer_id', name='uq_spins_customer'),
        UniqueConstraint('mobile_number', name='uq_spins_mobile'),
        Index('ix_spins_customer_id', 'customer_id'),
    )
