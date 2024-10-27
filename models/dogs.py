# models/dog.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from database import Base

class DogDB(Base):
    __tablename__ = "dogs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    birth_date = Column(Date)
    date_of_visit = Column(Date)
    procedure_id = Column(Integer, ForeignKey("procedures.id"))
