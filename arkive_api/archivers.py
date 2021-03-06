from waybackpy import WaybackMachineSaveAPI

from .logging import logger
from .db import update_url

USER_AGENT = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"


async def submit_to_internet_archive(url_stripped: str, db_conn):
    logger.info("(submit_to_internet_archive) => submitting " + url_stripped  + " to Archive.org ..")
    save_api = WaybackMachineSaveAPI(url_stripped, USER_AGENT)
    internet_archive_url: str = save_api.save()

    logger.info("(submit_to_internet_archive) => saving ia url to db.. ")
    await update_url(url_stripped, internet_archive_url, db_conn)

    return internet_archive_url

