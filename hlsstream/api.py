import uvicorn
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/video/{fileName}")
async def video(response: Response, fileName: str):
    response.headers["Content-Type"] = "application/x-mpegURL"
    return FileResponse("static/video/" + fileName, filename=fileName)


if __name__ == "__main__":
    uvicorn.run(
        "hlsstream.api:app",
        host="127.0.0.1",
        port=5000,
        log_level="info",
        reload=True,
        debug=True,
    )
