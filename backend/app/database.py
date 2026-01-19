import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Wir holen die interne URL aus Coolify
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ACHTUNG: DATABASE_URL nicht gesetzt. Nutze SQLite als Fallback für lokale Tests.")
    DATABASE_URL = "sqlite:///./test.db"

# Engine erstellen
engine = create_engine(DATABASE_URL)

# Session-Fabrik (für Datenbank-Sitzungen pro Request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Basis-Klasse für unsere Modelle
Base = declarative_base()

# Hilfsfunktion, die jeder API-Endpunkt nutzen kann
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
