import argparse
import logging
import time
from pythonjsonlogger import jsonlogger
from .unmap import reconcile


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-id", metavar="ID", required=True, help="AWS CloudMap service ID")
    parser.add_argument("--service-region", metavar="REGION", required=True, help="AWS CloudMap service region")
    parser.add_argument("--instances-region", metavar="REGION", required=True, nargs='+', help="AWS region where EC2 instances should be checked")
    parser.add_argument("--frequency-sec", metavar="N", required=False, default=300, help="How frequently the service should be reconciled (in seconds)")
    parser.add_argument("--log-level", help="Minimum log level. Accepted values are: DEBUG, INFO, WARNING, ERROR, CRITICAL", default="INFO")
    args = parser.parse_args()

    frequencySec = float(args.frequency_sec)

    # Init logger
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("(asctime) (levelname) (message)", datefmt="%Y-%m-%d %H:%M:%S")
    logHandler.setFormatter(formatter)
    logging.getLogger().addHandler(logHandler)
    logging.getLogger().setLevel(args.log_level)

    # Reconcile
    while True:
        startTime = time.monotonic()
        # TODO try/except + tests
        reconcile(args.service_id, args.service_region, args.instances_region)
        elapsedTime = time.monotonic() - startTime

        # Honor frequency
        if elapsedTime < frequencySec:
            time.sleep(frequencySec - elapsedTime)


if __name__ == '__main__':
    main()
