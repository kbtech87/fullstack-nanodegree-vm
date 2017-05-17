import sys #provides functions/vars
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base() #lets sqlalchemy know that these are special sqlalchemy classes

class Categories(Base): #corresponds to table
  __tablename__ = 'categories'
  name = Column(
  String(80), nullable = False
  )
  id = Column(
  Integer, primary_key = True
  )

class Items(Base): #corresponds to table
    __tablename__ = 'items'
    name = Column(
    String(80), nullable = False
    )
    id = Column(
    Integer, primary_key = True
    )
    description = Column(
    String(250)
    )
    category_id = Column(
    Integer, ForeignKey('categories.id')
    )
    categories = relationship(Categories)

    @property
    def serialize(self):
        #Returns object data in easily serializable format
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
        }










#### insert at end of file ####
engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
