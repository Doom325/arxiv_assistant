from database import SessionLocal, engine
import models
import bcrypt

# Create tables
models.Base.metadata.create_all(bind=engine)

def init_db():
    db = SessionLocal()
    try:
        # Check if default user exists
        user = db.query(models.User).filter(models.User.email == "user@example.com").first()
        if not user:
            print("Creating default user...")
            hashed = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode('utf-8')
            default_user = models.User(
                email="user@example.com",
                hashed_password=hashed,
                is_active=True
            )
            db.add(default_user)
            db.commit()
            print("Default user created (ID: 1)")
        else:
            print("Default user already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
