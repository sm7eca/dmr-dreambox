import os
from fastapi import FastAPI

from routers import repeater
from routers import hotspot
from routers import info

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
    version=f"0.1.{eim_git_hash[:6]}"
)

app.include_router(repeater.router)
app.include_router(hotspot.router)
app.include_router(info.router)
