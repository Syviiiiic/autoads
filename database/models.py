from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(20))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    ads = relationship("Ad", back_populates="owner", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

class Ad(Base):
    __tablename__ = 'ads'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Основная информация
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    mileage = Column(Integer, default=0)
    engine_capacity = Column(Float, default=0.0)
    engine_type = Column(String(50), default="Не указан")
    transmission = Column(String(50), default="Не указана")
    drive = Column(String(50), default="Не указан")
    color = Column(String(50), default="Не указан")
    description = Column(Text, default="")
    photos = Column(Text, default="[]")  # JSON строка с массивом file_id
    
    # Статус и статистика
    is_active = Column(Boolean, default=True)
    is_moderated = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    owner = relationship("User", back_populates="ads")
    favorites = relationship("Favorite", back_populates="ad", cascade="all, delete-orphan")

class Favorite(Base):
    __tablename__ = 'favorites'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    ad_id = Column(Integer, ForeignKey('ads.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    user = relationship("User", back_populates="favorites")
    ad = relationship("Ad", back_populates="favorites")
    
    __table_args__ = (UniqueConstraint('user_id', 'ad_id', name='unique_user_ad'),)