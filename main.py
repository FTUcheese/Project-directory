from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess, os, base64, requests

# Optional: CAD libraries (SolidPython)
try:
    from solid import scad_render_to_file
    from solid.objects import cube, sphere
    SOLIDPYTHON_AVAILABLE = True
except ImportError:
    SOLIDPYTHON_AVAILABLE = False

# --- Configuration ---
PROJECTS_DIR = "/tmp/projects"
os.makedirs(PROJECTS_DIR, exist_ok=True)

def safe_join(base, filename):
    return os.path.join(base, os.path.normpath(filename).replace("..", ""))

app = FastAPI(
    openapi_url="/openapi.json",
    servers=[{"url": "https://codepilotx.onrender.com", "description": "Render Public API"}]
)

# --- GitHub Upload ---
def upload_to_github(local_path, remote_path):
    github_token = os.environ.get("GITHUB_TOKEN")
    github_repo = os.environ.get("GITHUB_REPO")
    if not github_token or not github_repo:
        return {"status": "skipped", "reason": "GitHub credentials not set"}

    with open(local_path, "rb") as f:
        b64_content = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{github_repo}/contents/{remote_path}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    get_resp = requests.get(url, headers=headers)
    data = {
        "message": f"{'Update' if get_resp.status_code == 200 else 'Add'} {remote_path} via API",
        "content": b64_content
    }
    if get_resp.status_code == 200:
        data["sha"] = get_resp.json()["sha"]

    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code in [200, 201]:
        return {"status": "success", "url": resp.json().get("content", {}).get("html_url")}
    return {"status": "error", "detail": resp.text}

# --- File Models ---
class RunCommand(BaseModel):
    cmd: str

class UploadPayload(BaseModel):
    filename: str
    content_b64: str = None
    content: str = None
    file: str = None

# --- Run Command ---
@app.post("/project/run")
async def run_project(command: RunCommand):
    try:
        result = subprocess.run(
            command.cmd, shell=True, cwd=PROJECTS_DIR,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- File Upload (raw) ---
@app.post("/project/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = safe_join(PROJECTS_DIR, file.filename)
        content = await file.read()
        if file.filename.endswith((".py", ".txt", ".scad")):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.decode("utf-8", errors="replace"))
        else:
            with open(file_path, "wb") as f:
                f.write(content)
        github_result = upload_to_github(file_path, file.filename)
        return {
            "message": f"Uploaded '{file.filename}' successfully.",
            "filepath": file_path,
            "github": github_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- File Upload (JSON) ---
@app.post("/project/uploadjson")
async def upload_file_json(payload: UploadPayload):
    file_path = safe_join(PROJECTS_DIR, payload.filename)

    if payload.content_b64:
        try:
            content_raw = base64.b64decode(payload.content_b64)
            decode_type = "base64 decoded"
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid base64 in content_b64.")
    elif payload.content:
        content_raw = payload.content.encode("utf-8")
        decode_type = "UTF-8 text"
    elif payload.file:
        content_raw = payload.file.encode("utf-8")
        decode_type = "UTF-8 text"
    else:
        raise HTTPException(status_code=400, detail="No content provided.")

    if payload.filename.endswith((".py", ".txt", ".scad")):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_raw.decode("utf-8", errors="replace"))
    else:
        with open(file_path, "wb") as f:
            f.write(content_raw)

    github_result = upload_to_github(file_path, payload.filename)
    return {
        "message": f"File '{payload.filename}' uploaded ({decode_type}).",
        "filepath": file_path,
        "github": github_result
    }

# --- File Retrieval ---
@app.get("/project/getfile/{filename}")
async def get_file_contents(filename: str):
    file_path = safe_join(PROJECTS_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return {"filename": filename, "content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/project/download/{filename}")
async def download_file(filename: str):
    file_path = safe_join(PROJECTS_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, filename=filename)

# --- CAD Rendering (SolidPython) ---
@app.get("/project/render_sample")
async def render_sample_scad():
    if not SOLIDPYTHON_AVAILABLE:
        raise HTTPException(status_code=501, detail="SolidPython not installed.")
    try:
        scad_file = safe_join(PROJECTS_DIR, "sample.scad")
        scad_render_to_file(cube(10) + sphere(5), scad_file)
        return {"message": "Sample SCAD file created.", "path": scad_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"msg": "CodePilotX API is running. See /docs"}