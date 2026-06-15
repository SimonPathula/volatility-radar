from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os

ROOT_DIR = Path(__file__).resolve().parents[3]

load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)