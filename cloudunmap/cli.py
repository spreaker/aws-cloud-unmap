import argparse
import logging
import time
import sys
import signal
from typing import List
from pythonjsonlogger import jsonlogger
from .unmap import unmapTerminatedInstancesFromService


def parseArguments(argv: List[str]):
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-id", metavar="ID", required=True, help="AWS CloudMap service ID")
    parser.add_argument("--service-region", metavar="REGION", required=True, help="AWS CloudMap service region")
    parser.add_argument("--instances-region", metavar="REGION", required=True, nargs='+', help="AWS region where EC2 instances should be checked")
    parser.add_argument("--frequency", metavar="N", required=False, type=int, default=300, help="How frequently the service should be reconciled (in seconds)")
    parser.add_argument("--single-run", required=False, default=False, action="store_true", help="Run a single reconcile and then exit")
    parser.add_argument("--log-level", help="Minimum log level. Accepted values are: DEBUG, INFO, WARNING, ERROR, CRITICAL", default="INFO")

    return parser.parse_args(argv)


def reconcile(serviceId: str, serviceRegion: str, instancesRegion: List[str]):
    logger = logging.getLogger()

    try:
        unmapTerminatedInstancesFromService(serviceId, serviceRegion, instancesRegion)
    except Exception as error:
        logger.error(f"An error occurred while reconciling service {serviceId}: {str(error)}")


def main(args):
    shutdown = False

    # Init logger
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("(asctime) (levelname) (message)", datefmt="%Y-%m-%d %H:%M:%S")
    logHandler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(args.log_level)

    # Register signal handler
    def _on_sigterm(signal, frame):
        logger.info("Shutting down")
        nonlocal shutdown
        shutdown = True

    signal.signal(signal.SIGINT, _on_sigterm)
    signal.signal(signal.SIGTERM, _on_sigterm)

    # Reconcile
    if args.single_run:
        reconcile(args.service_id, args.service_region, args.instances_region)
    else:
        while not shutdown:
            startTime = time.monotonic()
            reconcile(args.service_id, args.service_region, args.instances_region)

            # Honor frequency
            while not shutdown:
                elapsedTime = time.monotonic() - startTime

                if elapsedTime < args.frequency:
                    time.sleep(min(1, args.frequency - elapsedTime))
                else:
                    break


def run():
    main(parseArguments(sys.argv[1:]))


if __name__ == '__main__':
    run()
