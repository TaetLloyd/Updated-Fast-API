from sqlalchemy import Table,Column
from config.db import Meta 

users = Table(
    'users', Meta,
    Column('id',integer, primary_key=True),
    Column('name',String(255)),
    Column('email',String(255)),
    Column('password',String(255)),

)