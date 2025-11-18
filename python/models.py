from sqlalchemy import Column, Integer, String
from database import Base


class User(Base):
    __tablename__ = "User"

    id_user = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(255))
    password = Column(String(255))
    email = Column(String(255))
