import os
from ftplib import FTP, error_perm
from utils.scraper import logger
from config import FTP_HOST, FTP_USER, FTP_PASS, FTP_PORT, FTP_DIR, ENABLE_FTP_UPLOAD


def _ensure_remote_dir(ftp: FTP, remote_dir: str):
    """
    Recursively create directories on the FTP server if they don't exist.
    """
    # Normalize and split path
    path = remote_dir.replace("\\", "/").strip("/")
    if not path:
        return
    parts = path.split("/")
    cwd = ""
    for part in parts:
        cwd = f"{cwd}/{part}" if cwd else f"/{part}"
        try:
            ftp.mkd(cwd)
        except error_perm:
            # Directory probably exists
            pass


def upload_files(file_paths):
    """
    Upload a list of local files to FTP_DIR.
    """
    if not ENABLE_FTP_UPLOAD:
        logger.info("FTP upload disabled by config.")
        return False

    if not all([FTP_HOST, FTP_USER, FTP_PASS, FTP_DIR]):
        logger.error("FTP config is incomplete. Please set FTP_HOST/FTP_USER/FTP_PASS/FTP_DIR.")
        return False

    try:
        with FTP() as ftp:
            ftp.connect(FTP_HOST, FTP_PORT, timeout=30)
            ftp.login(FTP_USER, FTP_PASS)
            _ensure_remote_dir(ftp, FTP_DIR)
            ftp.cwd(FTP_DIR)

            for path in file_paths:
                if not os.path.exists(path):
                    logger.warning("File not found for FTP upload: %s", path)
                    continue
                name = os.path.basename(path)
                with open(path, "rb") as f:
                    ftp.storbinary(f"STOR {name}", f)
                logger.info("Uploaded %s to FTP.", name)
        return True
    except Exception as e:
        logger.error("FTP upload failed: %s", e)
        return False
