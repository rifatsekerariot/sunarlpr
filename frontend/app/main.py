import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="SUNAR HTML Frontend")

# Mount media shared root if exists
media_path = "/app/media"
if os.path.exists(media_path):
    app.mount("/media", StaticFiles(directory=media_path), name="media")

# Serve index.html globally on root path
@app.get("/")
async def serve_index():
    return FileResponse("/app/app/static/index.html")

# Ensure static files mount does not collide
app.mount("/", StaticFiles(directory="/app/app/static"), name="static")
