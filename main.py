from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from anthropic import Anthropic
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import zipfile
import subprocess
from pathlib import Path
import tempfile

class UserInput(BaseModel):
    message: str

class GeneratedProblems(BaseModel):
    problems: str

GENERATE_PROMPT = Path("generate.txt").read_text()
FORMAT_PROMPT = Path("format.txt").read_text()

MODEL = "claude-sonnet-4-5"

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
app = FastAPI()

# Serve CSS, JS, images from the "static" folder
app.mount("/static", StaticFiles(directory="static"), name="static")
# Serve HTML templates from the "templates" folder
templates = Jinja2Templates(directory="templates")

# Serve the index.html file
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_model=GeneratedProblems)
async def generate_problems(input: UserInput):
    response = client.messages.create(
        model=MODEL,
        system=GENERATE_PROMPT,
        max_tokens=8000,
        messages=[
            {
                "role": "user",
                "content": input.message
            }
        ]
    )

    assert len(response.content) == 1
    reply = response.content[0].text

    return GeneratedProblems(problems=reply)

@app.post("/format", response_model=GeneratedProblems)
async def format_problems(input: GeneratedProblems):
    response = client.messages.create(
        model=MODEL,
        system=FORMAT_PROMPT,
        max_tokens=8000,
        messages=[
            {
                "role": "user",
                "content": input.problems
            }
        ]
    )

    assert len(response.content) == 1
    reply = response.content[0].text

    return GeneratedProblems(problems=reply)

@app.post("/convert")
async def convert_problems(input: GeneratedProblems, background_tasks: BackgroundTasks):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp:
        tmp.write(input.problems)
        tmp.flush()
        input_file = Path(tmp.name)
        
    try:
        subprocess.run(["text2qti", str(input_file)], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        error_message = e.stderr
        formatted_error_message = error_message.split('.txt" on ')[-1].strip()
        if "Question must specify only one correct choice" in formatted_error_message:
            formatted_error_message += "\nIf you want to allow multiple correct choices, use [] and [*] instead."
        if "Question must specify a response type" in formatted_error_message:
            formatted_error_message += " \nSee formatting instructions at https://github.com/gpoore/text2qti"
        print("formatted error message: ", formatted_error_message)
        raise HTTPException(status_code=400, detail=formatted_error_message)

    zip_path = Path(input_file).with_suffix(".zip")
    if not zip_path.exists():
        input_file.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Zip not found")
    # Clean up the temporary files after the response is sent
    background_tasks.add_task(input_file.unlink, missing_ok=True)
    background_tasks.add_task(zip_path.unlink, missing_ok=True)

    return FileResponse(
        path=zip_path,
        filename=zip_path.name,
        media_type="application/zip",
        background=background_tasks
    )