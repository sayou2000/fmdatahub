import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Wir holen die URL aus Coolify
DATABASE_URL = os.getenv("DATABASE_URL")

# --- DER FIX: Autokorrektur für den falschen Link-Namen ---
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
# ----------------------------------------------------------

if not DATABASE_URL:
    print("ACHTUNG: DATABASE_URL nicht gesetzt. Nutze SQLite als Fallback für lokale Tests.")
    DATABASE_URL = "sqlite:///./test.db"

# Engine erstellen
engine = create_engine(DATABASE_URL)

# Session-Fabrik
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Basis-Klasse für unsere Modelle
Base = declarative_base()

# Hilfsfunktion
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
