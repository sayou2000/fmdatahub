from fastapi import FastAPI
import httpx

app = FastAPI(title="CAFM Connector Hub")

@app.get("/")
def read_root():
    return {"Status": "Connector läuft auf Coolify!", "Version": "0.1.0"}

@app.get("/test-openspace")
async def test_openspace_connectivity():
    # Wir pingen einfach Google an, um zu sehen, ob der Server Internet hat
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.google.com")
        return {"internet_check": response.status_code}
