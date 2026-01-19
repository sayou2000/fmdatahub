import os
from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI(title="CAFM Connector Hub")

@app.get("/")
def read_root():
    return {
        "Status": "Connector läuft!", 
        "Version": "0.2.0 - OpenSpace Integration"
    }

@app.get("/openspace/test-connection")
async def test_openspace_connection():
    # 1. Wir holen den Token sicher aus der Umgebung
    token = os.getenv("OPENSPACE_API_TOKEN")
    
    if not token:
        raise HTTPException(status_code=500, detail="FEHLER: Kein OPENSPACE_API_TOKEN in Coolify hinterlegt!")

    # 2. Wir bauen die Anfrage (Header)
    headers = {
        "api-key": token,
        "Accept": "application/json"
    }
    
    # 3. Wir fragen die OpenSpace API (Beispiel-Endpunkt für Projekte)
    url = "https://api.eu.openspace.ai/api/external/v1/reports/field-notes" 
    
    async with httpx.AsyncClient() as client:
        try:
            # Wir fragen testweise nur 1 Ergebnis ab (?page=1&limit=1), um die Antwort klein zu halten
            response = await client.get(f"{url}?page=1&limit=1", headers=headers, timeout=10.0)
            
            return {
                "http_status": response.status_code,
                "data": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {"error": str(e)}
