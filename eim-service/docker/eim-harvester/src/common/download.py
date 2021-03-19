
import os
from pathlib import Path

import requests
from requests.exceptions import HTTPError, ConnectionError, ConnectTimeout

from common.logger import harvester_logger

logger = harvester_logger("download")


def downloadable(url: str, max_size_bytes: int = 20e6) -> bool:
    """
    check whether file is not containing HTML or TEXT or exceeds
    filesize limits
    """
    h = requests.head(url, allow_redirects=True)
    header = h.headers
    try:
        content_type = header.get('content-type')
    except (HTTPError, ConnectionError, ConnectTimeout) as error:
        logger.error(f"Unable to download header information for {url}")
        return False

    content_length = int(header.get('content-length', 0))
    if content_type.lower() in ['text', 'html']:
        logger.debug(f"{url} not downloadable, {content_type.lower()}")
        return False
    elif content_length > max_size_bytes:
        logger.debug(f"{url} not downloadable, size: {content_length} > {max_size_bytes}")
        return False
    logger.debug(f"{url} downloadable, size: {content_length} bytes")
    return True


def download_2_file(url: str, target_path: Path) -> Path:
    """
    Download a file and replace the content of target_path with it
    """
    if target_path.exists():
        os.remove(target_path)
        logger.debug(f"file {target_path} exists, remove it")

    with requests.get(url, stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)

    logger.info(f"successfully downloaded: {url} => {target_path}")
    return target_path
