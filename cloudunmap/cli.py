import argparse
import logging
import time
from pythonjsonlogger import jsonlogger
from .unmap import unmapTerminatedInstancesFromService


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-id", metavar="ID", required=True, help="AWS CloudMap service ID")
    parser.add_argument("--service-region", metavar="REGION", required=True, help="AWS CloudMap service region")
    parser.add_argument("--instances-region", metavar="REGION", required=True, nargs='+', help="AWS region where EC2 instances should be checked")
    parser.add_argument("--frequency-sec", metavar="N", required=False, type=int, default=300, help="How frequently the service should be reconciled (in seconds)")
    parser.add_argument("--single-run", required=False, default=False, action="store_true", help="Run a single reconcile and then exit")
    parser.add_argument("--log-level", help="Minimum log level. Accepted values are: DEBUG, INFO, WARNING, ERROR, CRITICAL", default="INFO")
    args = parser.parse_args()

    # Init logger
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("(asctime) (levelname) (message)", datefmt="%Y-%m-%d %H:%M:%S")
    logHandler.setFormatter(formatter)
    logging.getLogger().addHandler(logHandler)
    logging.getLogger().setLevel(args.log_level)

    # Reconcile
    if args.single_run:
        unmapTerminatedInstancesFromService(args.service_id, args.service_region, args.instances_region)
    else:
        while True:
            startTime = time.monotonic()
            # TODO try/except + tests
            unmapTerminatedInstancesFromService(args.service_id, args.service_region, args.instances_region)
            elapsedTime = time.monotonic() - startTime

            # Honor frequency
            if elapsedTime < args.frequency_sec:
                time.sleep(args.frequency_sec - elapsedTime)


if __name__ == '__main__':
    main()
