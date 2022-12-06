import logging
from datetime import datetime
from logging import Logger
from os import getenv

from cloudshell.api.cloudshell_api import CloudShellAPISession

from discovery.cp_discovery import DiscoverVms
from discovery.cs_api_with_sandbox import CsApiWithSandbox, run_with_sandbox


def main():
    api = CloudShellAPISession(
        getenv("CS_HOST"), getenv("CS_USER"), getenv("CS_PASS"), "Global"
    )
    logger = get_logger()
    with run_with_sandbox(api) as rid:
        api = CsApiWithSandbox.create(api, rid)
        tool = DiscoverVms(
            "vcenter",
            "Generic Static VM 2G",
            "Generic Static VM 2G.GenericVPort",
            api,
            logger,
            max_workers=15,
        )
        logger.info("Clearing")
        tool.clear()
        logger.info("Discovering")
        start = datetime.now()
        tool.discover()
        logger.info(f"Discovered in {datetime.now() - start}")


def get_logger() -> Logger:
    log_level = logging.DEBUG

    new_logger = logging.getLogger(__name__)
    new_logger.setLevel(log_level)

    std_handler = logging.StreamHandler()
    std_handler.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
    )
    std_handler.setFormatter(formatter)

    new_logger.addHandler(std_handler)

    return new_logger


if __name__ == "__main__":
    main()
