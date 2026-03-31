from scheduler import process_papers
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🌱 Seeding database...")
    try:
        process_papers()
        print("✅ Database seeded successfully!")
    except Exception as e:
        print(f"❌ Failed to seed database: {e}")
