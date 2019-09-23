#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Item, Category

engine = create_engine(
    'sqlite:///catalog.db',
    connect_args={
        'check_same_thread': False
    }
)

Session = sessionmaker(bind=engine)
session = Session()

# Add default User
default_user = User(
    name='John',
    email='Johndoe@example.com',
    picture='https://example.com'
)

session.add(default_user)
session.commit()

# Add default Category
default_category = Category(
    name='Snowboarding',
    user=default_user
)

session.add(default_category)
session.commit()

# Add default item
default_item = Item(
    name='Snowboard',
    description='Best for any terrain and conditions. All-mountain snowboards perform anywhere on a mountain--groomed runs, backcountry, even park and pipe',
    category=default_category,
    user=default_user
)

session.add(default_item)
session.commit()

print('Initial Database populated')
print('exiting...')
