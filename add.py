from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items,User

engine = create_engine('sqlite:///itemcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

newcat = Categories(name='hockey',user_id=1)
newcat2 = Categories(name='skate boards',user_id=2)
session.add(newcat)
session.add(newcat2)
session.commit()

User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

item1 = Items(name='pad',description='this hockey pad is very powerful and has high hit power',user_id=1,cat_id=1)
item2 = Items(name='suit',description='this hockey suit is very uniqe',user_id=1,cat_id=1)
item3 = Items(name='pants',description='this hockey pad is very powerful and has high hit power',user_id=1,cat_id=1)
item4 = Items(name='shoes',description='this hockey pad is very powerful and has high hit power',user_id=1,cat_id=1)
session.add(item1)
session.add(item2)
session.add(item3)
session.add(item4)
session.commit()