import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import httpx

# Importiere unsere neuen Module
from .database import engine, Base, get_db
from .models import ImportedIssue

# Erstelle die Tabellen in der Datenbank (falls sie noch nicht existieren)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CAFM Connector Hub")

@app.get("/")
def read_root():
    return {"Status": "Connector mit Datenbank verbunden!", "Version": "0.3.0"}

@app.post("/openspace/sync")
async def sync_openspace_data(project_id: str = None, db: Session = Depends(get_db)):
    """
    Holt Daten von OpenSpace und speichert sie in der DB.
    """
    token = os.getenv("OPENSPACE_API_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Kein OPENSPACE_API_TOKEN konfiguriert")

    # Header genau so, wie wir es getestet haben (api-key)
    headers = {"api-key": token, "Accept": "application/json"}
    
    # URL für Field Notes
    url = "https://api.eu.openspace.ai/api/external/v1/reports/field-notes"
    
    # Wir holen testweise 5 Einträge
    params = {"page": 1, "limit": 5}
    if project_id:
        params["projectId"] = project_id

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=15.0)
            
            if response.status_code != 200:
                return {"error": "OpenSpace API Error", "details": response.text}
            
            data = response.json()
            # Hinweis: Die genaue Struktur der API-Antwort musst du evtl. prüfen. 
            # Wir gehen davon aus, dass 'fieldNotes' eine Liste ist.
            items = data.get("fieldNotes", []) 
            
            saved_count = 0
            
            for item in items:
                # Deduplizierung: Prüfen, ob wir dieses Issue schon haben
                os_id = item.get("id")
                existing = db.query(ImportedIssue).filter(ImportedIssue.openspace_id == os_id).first()
                
                if not existing:
                    # Neu anlegen
                    new_issue = ImportedIssue(
                        openspace_id=os_id,
                        project_id=item.get("projectId"), 
                        title=item.get("description", "Kein Titel"), 
                        status=item.get("status"),
                        image_url=None, # Hier müssten wir später die URL aus attachments parsen
                        raw_data=item
                    )
                    db.add(new_issue)
                    saved_count += 1
            
            db.commit()
            
            return {
                "status": "success", 
                "total_fetched": len(items), 
                "newly_saved_in_db": saved_count
            }
            
        except Exception as e:
            return {"error": str(e)}

@app.get("/db/check")
def check_db_content(db: Session = Depends(get_db)):
    # Kleiner Helfer, um zu sehen, was in der DB liegt
    issues = db.query(ImportedIssue).limit(20).all()
    return issues
