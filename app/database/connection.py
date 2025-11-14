import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

CORE_DB_URL = (
    f"mysql+pymysql://{os.getenv('CORE_BANK_USER')}:{os.getenv('CORE_BANK_PW')}"
    f"@{os.getenv('CORE_BANK_HOST')}:{os.getenv('CORE_BANK_PORT')}/"
    f"{os.getenv('CORE_BANK_DB')}?charset=utf8mb4"
)

core_engine = create_engine(
    CORE_DB_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

CoreSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=core_engine
)

def get_core_db():
    db = CoreSessionLocal()
    try:
        yield db
    finally:
        db.close()

FEATURE_DB_URL = (
    f"mysql+pymysql://{os.getenv('FEATURE_DB_USER')}:{os.getenv('FEATURE_DB_PW')}"
    f"@{os.getenv('FEATURE_DB_HOST')}:{os.getenv('FEATURE_DB_PORT')}/"
    f"{os.getenv('FEATURE_DB_NAME')}?charset=utf8mb4"
)

feature_engine = create_engine(
    FEATURE_DB_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

FeatureSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=feature_engine
)

def get_feature_db():
    db = FeatureSessionLocal()
    try:
        yield db
    finally:
        db.close()
