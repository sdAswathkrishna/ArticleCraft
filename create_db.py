# create_db.py

from database import engine
from models import Base

# Create all tables
Base.metadata.create_all(bind=engine)
print("✅ All tables created in MySQL database.")


