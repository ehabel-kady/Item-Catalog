import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()
class User(Base):
    __tablename__='user'
    id=Column(Integer,primary_key=True)
    name=Column(String(80),nullable=False)
    email=Column(String(250),nullable=False)
    picture=Column(String(350))
    @property
    def serialize(self):
         return {
            'id': self.id,
            'name': self.name,
            'email':self.email,
            'picture':self.picture
        }
class Categories(Base):
    __tablename__='categories'
    id=Column(Integer,primary_key=True)
    name=Column(String(80),nullable=False)
    user_id = Column(Integer,ForeignKey('user.id'))
    User=relationship(User)
    @property
    def serialize(self):
         return {
            'id': self.id,
            'name': self.name,
            'user_id':self.user_id
        }
class Items(Base):
    __tablename__='items'
    id=Column(Integer,primary_key=True)
    name=Column(String(80),nullable=False)
    description=Column(String(250),nullable=False)
    cat_id=Column(Integer,ForeignKey('categories.id'))
    Categories = relationship(Categories)
    user_id = Column(Integer,ForeignKey('user.id'))
    User=relationship(User)
    @property
    def serialize(self):
        return {
            'name':self.name,
            'id':self.id,
            'description':self.description,
            'cat_id':self.cat_id,
            'user_id':self.user_id
        }
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)