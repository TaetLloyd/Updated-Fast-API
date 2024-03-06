from sqlalchemy import create_engine, MetaData
from sqlalchemy import MetaData

SQLALCHEMY_DATABASE_URL = "mysql://username:password@localhost:3306/test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
meta =MetaData()
conn = engine.connect()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()