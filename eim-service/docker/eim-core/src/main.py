import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from routers import repeater
from routers import hotspot
from routers import dmr
from routers import info
from routers import user


from common.logger import config_root_logger


eim_git_hash = os.environ['EIM_GIT_HASH']
dmr_release = os.environ['DMR_RELEASE_NAME']
github_ref = "https://github.com/sm7eca/dmr-dreambox"

config_root_logger()

app = FastAPI(
    title="DMR Dreambox - EIM",
    description=f'External Information Management for DMR dreambox<br>'
                f'DMR version: <a target="_blank" href={github_ref}/releases>{dmr_release}</a><br>'
                f'Commit at Github: <a target="_blank" href="{github_ref}/commit/{eim_git_hash}">{eim_git_hash[:6]}</a>',
    version=f"0.1.{eim_git_hash[:6]}",
    root_path="/api/v1"
)


@app.get("/", include_in_schema=False)
def redirect_docs(request: Request):
    """Redirect ROOT to docs, so that a user by default end up reading something."""
    response = RedirectResponse(url=f"{request.scope.get('root_path')}/docs")
    return response


@app.get("/app", include_in_schema=False)
def read_main(request: Request):
    return {"message": "Hello world", "root_path": request.scope.get("root_path")}


app.include_router(repeater.router)
app.include_router(hotspot.router)
app.include_router(dmr.router)
app.include_router(user.router)
app.include_router(info.router)

