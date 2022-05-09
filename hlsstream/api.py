import uvicorn
import json
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .sync import Cache


cache = Cache()


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/video/{fileName}")
async def video(response: Response, fileName: str):
    response.headers["Content-Type"] = "application/x-mpegURL"
    return FileResponse("video/" + fileName, filename=fileName)


@app.get("/markers")
async def markers(response: Response):
    # response.headers["Content-Type"] = "application/x-mpegURL"
    # return FileResponse("static/video/" + fileName, filename=fileName)
    markers = cache.get("markers")
    return JSONResponse(content=json.dumps({"markers": markers}))


app.mount("/", StaticFiles(directory="static", html=True), name="static")


def main():
    uvicorn.run(
        "hlsstream.api:app",
        host="127.0.0.1",
        port=5000,
        log_level="debug",
        reload=True,
        debug=True,
    )


if __name__ == "__main__":
    main()
