import os

import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from handler import get_package_path, get_package_versions

os.environ['PROOT'] = os.path.dirname(__file__)
os.chdir("../nixpkgs")
app = FastAPI()


@app.get("/{package}")
def read_versions(package: str):
    package = package.lower()
    if not (path := get_package_path(package)):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "Not Found"})
    result = get_package_versions(package, path)
    return JSONResponse(status_code=status.HTTP_200_OK, content={k: v for k, v in result})


if __name__ == "__main__":
    uvicorn.run(
        "server:app", host="127.0.0.1", port=5000, log_level="info", reload=True
    )
