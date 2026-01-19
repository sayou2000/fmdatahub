import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import httpx

# Importiere unsere Module
from .database import engine, Base, get_db
from .models import ImportedIssue

# DB Tabellen erstellen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CAFM Connector Hub")

# --- 1. Der einfache Check (Root) ---
@app.get("/")
def read_root():
    return {"Status": "Connector läuft!", "Version": "0.4.0 (Full Features)"}

# --- 2. Der Verbindungstest (Wieder da!) ---
@app.get("/openspace/test-connection")
async def test_openspace_connection():
    token = os.getenv("OPENSPACE_API_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Kein Token gesetzt")

    headers = {"api-key": token, "Accept": "application/json"}
    
    # Wir pingen einfach die User-Info oder Projekte an
    url = "https://api.eu.openspace.ai/v2/projects" 
    
    async with httpx.AsyncClient() as client:
        try:
            # Versuch mit api-key Header
            response = await client.get(url, headers=headers, params={"page": 1, "limit": 1}, timeout=10.0)
            
            # Falls 401/403: Versuch mit Bearer (OpenSpace ist hier manchmal eigen)
            if response.status_code in [401, 403]:
                headers["Authorization"] = f"Bearer {token}"
                del headers["api-key"]
                response = await client.get(url, headers=headers, params={"page": 1, "limit": 1}, timeout=10.0)

            return {
                "http_status": response.status_code,
                "data_preview": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {"error": str(e)}

# --- 3. Hilfs-Endpunkt: Zeig mir meine Projekt-IDs ---
@app.get("/openspace/list-projects")
async def list_projects():
    """Nutze dies, um deine project_id zu finden!"""
    token = os.getenv("OPENSPACE_API_TOKEN")
    headers = {"api-key": token, "Accept": "application/json"}
    url = "https://api.eu.openspace.ai/v2/projects" 
    
    async with httpx.AsyncClient() as client:
        # Wir versuchen es robust mit beiden Auth-Methoden
        response = await client.get(url, headers=headers, timeout=10.0)
        if response.status_code in [401, 403]:
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            response = await client.get(url, headers=headers, timeout=10.0)
            
        return response.json()

# --- 4. Der Sync (Daten holen & Speichern) ---
@app.post("/openspace/sync")
async def sync_openspace_data(project_id: str, db: Session = Depends(get_db)):
    """
    project_id ist jetzt PFLICHT, damit wir nicht 0 Ergebnisse bekommen.
    """
    token = os.getenv("OPENSPACE_API_TOKEN")
    
    # Auth Header für External API (meist api-key)
    headers = {"api-key": token, "Accept": "application/json"}
    
    # URL für Field Notes
    url = "https://api.eu.openspace.ai/api/external/v1/reports/field-notes"
    
    params = {
        "page": 1, 
        "limit": 5,
        "projectId": project_id  # <--- HIER ist der Schlüssel zum Erfolg
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=15.0)
            
            if response.status_code != 200:
                return {"error": "API Fehler", "code": response.status_code, "msg": response.text}
            
            data = response.json()
            items = data.get("fieldNotes", [])
            
            saved_count = 0
            
            for item in items:
                os_id = item.get("id")
                existing = db.query(ImportedIssue).filter(ImportedIssue.openspace_id == os_id).first()
                
                if not existing:
                    new_issue = ImportedIssue(
                        openspace_id=os_id,
                        project_id=str(item.get("projectId")),
                        title=item.get("description", "Kein Titel"),
                        status=item.get("status"),
                        image_url=None, # Parsen wir später
                        raw_data=item
                    )
                    db.add(new_issue)
                    saved_count += 1
            
            db.commit()
            
            return {
                "status": "success", 
                "total_found_in_api": len(items), 
                "saved_to_db": saved_count,
                "project_used": project_id
            }
            
        except Exception as e:
            return {"error": str(e)}

# --- 5. DB Check ---
@app.get("/db/check")
def check_db_content(db: Session = Depends(get_db)):
    return db.query(ImportedIssue).all()
