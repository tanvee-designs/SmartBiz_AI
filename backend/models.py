from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import datetime

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    source = Column(String, default="website")
    status = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)