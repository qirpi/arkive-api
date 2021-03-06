#!python3

from os import getenv

from waybackpy.exceptions import TooManyRequestsError

import uvicorn
from fastapi import FastAPI, Depends


from .logging import logger
from .utils import is_path_url
from .db import Db, is_url_in_db, save_url, unhide_url
from .archivers import submit_to_internet_archive


async def get_db():
    with Db(getenv('ARKIVE_DB_PATH', "arkive.db"), "db_schema.sql") as db:
        yield db


app = FastAPI()


@app.get("/")
async def read_root():
    return {"status": "success"}


@app.get("/{url:path}")
async def read_url(url: str, db=Depends(get_db)):

    # Abort if 'url' turns out to be a path
    if not await is_path_url(url):
        return {"status": "error"}


    # Abort if URL already in database with the requested archive provider's
    # column filled out.
    url_in_db = await is_url_in_db(url, db)
    if url_in_db:
        if url_in_db[8] == 1:
            await unhide_url(url, db)
            return {"status": "unhidden"}
        
        if url_in_db[2]:
            return {"status": "duplicate"}
        else:
            logger.info(
                "(read_url) => url_in_db => No archive url found though, so submitting..")

    try:
        url_stripped = await save_url(url, db)
        internet_archive_url = await submit_to_internet_archive(url_stripped, db)
        # TODO: deal w/ updating database with internet_archive_url
        return {
            "status": "success",
            "internet_archive_url": internet_archive_url
        }
    except TooManyRequestsError as e:
        logger.info("(read_url) => TooManyRequestsError: " + str(e))
        return {
            "status": "error"
        }


def run():
    """Launched with `poetry run dev` at root level"""
    reload = getenv("ARKIVE_RELOAD", 'False').lower() in ('true', '1', 't')
    uvicorn.run(
        "arkive_api.api:app",
        port=int(getenv("ARKIVE_PORT", 3000)),
        reload=reload
    )
