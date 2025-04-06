from app import app, db
import models  # This imports the models so they are registered

with app.app_context():
    db.create_all()
    print("✅ Tables created successfully!")
