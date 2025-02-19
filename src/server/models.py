from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..utils.database import Base 

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    images = relationship("Image", back_populates="user")

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=func.now())
    user = relationship("User", back_populates="images")
    predictions = relationship("Prediction", back_populates="image")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    result = Column(String(100), nullable=False)
    confidence = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    image = relationship("Image", back_populates="predictions")
