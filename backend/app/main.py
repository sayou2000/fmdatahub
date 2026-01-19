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
        "api-key": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    # 3. Wir fragen die OpenSpace API (Beispiel-Endpunkt für Projekte)
    url = "https://api.eu.openspace.ai/api/external/v1/reports/field-notes" 
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            
            # Wir geben genau zurück, was OpenSpace uns sagt (zum Debuggen)
            return {
                "http_status": response.status_code,
                "data": response.json() if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {"error": str(e)}
