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

# --- 1. Root Check ---
@app.get("/")
def read_root():
    return {"Status": "Connector läuft!", "Version": "0.5.0 (Fixed API Endpoints)"}

# --- 2. Verbindungstest (Sites statt Projects) ---
@app.get("/openspace/test-connection")
async def test_openspace_connection():
    """
    Testet die Verbindung durch Abruf der 'Sites' (Projekte).
    API-Quelle: /api/external/v1/reports/sites
    """
    token = os.getenv("OPENSPACE_API_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Kein Token gesetzt")

    headers = {"api-key": token, "Accept": "application/json"}
    
    # KORREKTUR: Wir nutzen den "Reports Sites" Endpunkt für eine flache Liste
    url = "https://api.eu.openspace.ai/api/external/v1/reports/sites"
    
    async with httpx.AsyncClient() as client:
        try:
            # Wir laden nur 1 Site zum Testen
            response = await client.get(url, headers=headers, params={"page": 0, "size": 1}, timeout=10.0)
            
            return {
                "http_status": response.status_code,
                "data_preview": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {"error": str(e)}

# --- 3. Liste aller Sites (früher Projects) ---
@app.get("/openspace/list-projects")
async def list_projects():
    """
    Listet alle 'Sites' (Projekte) auf, damit du die ID findest.
    """
    token = os.getenv("OPENSPACE_API_TOKEN")
    headers = {"api-key": token, "Accept": "application/json"}
    
    # KORREKTUR: Endpunkt gemäß Doku 
    url = "https://api.eu.openspace.ai/api/external/v1/reports/sites"
    
    async with httpx.AsyncClient() as client:
        # Wir holen bis zu 50 Sites
        response = await client.get(url, headers=headers, params={"size": 50, "sort": "siteCreated,DESC"}, timeout=15.0)
        
        if response.status_code != 200:
             return {"error": response.text}

        data = response.json()
        # API Struktur: { "content": [ { "id": "...", "name": "..." } ], ... }
        sites = data.get("content", [])
        
        # Wir geben eine vereinfachte Liste zurück
        return [
            {"name": site.get("siteName"), "id": site.get("siteId"), "status": site.get("siteStatus")} 
            for site in sites
        ]

# --- 4. Der Sync (Field Notes einer Site) ---
@app.post("/openspace/sync")
async def sync_openspace_data(site_id: str, db: Session = Depends(get_db)):
    """
    Holt Field Notes für eine spezifische Site ID.
    API-Quelle: /api/external/v1/sites/{siteId}/field-notes
    """
    token = os.getenv("OPENSPACE_API_TOKEN")
    
    headers = {"api-key": token, "Accept": "application/json"}
    
    # KORREKTUR: Site-spezifischer Endpunkt 
    # URL Format: /sites/{siteId}/field-notes
    url = f"https://api.eu.openspace.ai/api/external/v1/sites/{site_id}/field-notes"
    
    # KORREKTUR: Parameter heißt 'size' nicht 'limit' 
    params = {
        "page": 0, 
        "size": 10,
        "sort": "modifiedAt,DESC" # Neueste zuerst
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=20.0)
            
            if response.status_code != 200:
                return {"error": "API Fehler", "code": response.status_code, "msg": response.text}
            
            data = response.json()
            # KORREKTUR: Die Liste steckt in 'content', nicht 'fieldNotes' 
            items = data.get("content", [])
            
            saved_count = 0
            
            for item in items:
                os_id = item.get("id")
                existing = db.query(ImportedIssue).filter(ImportedIssue.openspace_id == os_id).first()
                
                if not existing:
                    new_issue = ImportedIssue(
                        openspace_id=os_id,
                        project_id=site_id, # Wir speichern die Site ID als Project ID
                        title=item.get("description", "Keine Beschreibung"),
                        status=item.get("status"),
                        image_url=None, # Bildlogik kommt später (Attachments sind separate Calls)
                        raw_data=item
                    )
                    db.add(new_issue)
                    saved_count += 1
            
            db.commit()
            
            return {
                "status": "success", 
                "total_found_in_api": len(items), 
                "saved_to_db": saved_count,
                "site_id_used": site_id
            }
            
        except Exception as e:
            return {"error": str(e)}

@app.get("/db/check")
def check_db_content(db: Session = Depends(get_db)):
    return db.query(ImportedIssue).all()
