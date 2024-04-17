from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base  # Ensure Base has all the metadata
from pathlib import Path

def reset_database():
    # Path to the database file
    database_path = Path("database/main.db")
    
    # Check if the database file exists and remove it
    if database_path.exists():
        database_path.unlink()
    
    # Recreate the database directory if not exists
    database_path.parent.mkdir(exist_ok=True)
    
    # Create a new database engine instance
    engine = create_engine(f"sqlite:///{database_path}", echo=False)
    
    # Drop all data and recreate the tables
    Base.metadata.drop_all(engine)  # This is not strictly necessary as we delete the file
    Base.metadata.create_all(engine)

    print("Database has been reset.")


if __name__ == "__main__":
    reset_database()