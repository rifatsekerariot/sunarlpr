import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

app = FastAPI(title="SUNAR HTML Frontend")

# Mount media shared root if exists
media_path = "/app/media"
if os.path.exists(media_path):
    app.mount("/media", StaticFiles(directory=media_path), name="media")

# Serve static directory containing assets
app.mount("/assets", StaticFiles(directory="/app/app/static/assets"), name="assets")

# Route root to login page
@app.get("/")
async def serve_login():
    return FileResponse("/app/app/static/login.html")

# Route /dashboard to main app dashboard
@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse("/app/app/static/index.html")
