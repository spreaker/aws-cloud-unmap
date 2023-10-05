import argparse
import logging
import time
import sys
import signal
from typing import List
from pythonjsonlogger import jsonlogger
from .unmap import unmapTerminatedInstancesFromService
from prometheus_client import start_http_server, Gauge


# Prometheus metrics
upMetric = Gauge(
    "aws_cloud_unmap_up",
    "Always 1 - can by used to check if it's running",
    labelnames=["service_id"])

lastReconcileTimestampMetric = Gauge(
    "aws_cloud_unmap_last_reconcile_success_timestamp_seconds",
    "The timestamp (in seconds) of the last successful reconciliation",
    labelnames=["service_id"])


def parseArguments(argv: List[str]):
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-id", metavar="ID", required=True, help="AWS CloudMap service ID")
    parser.add_argument("--service-region", metavar="REGION", required=True, help="AWS CloudMap service region")
    parser.add_argument("--instances-region", metavar="REGION", required=True, nargs='+', help="AWS region where EC2 instances should be checked")
    parser.add_argument("--frequency", metavar="N", required=False, type=int, default=300, help="How frequently the service should be reconciled (in seconds)")
    parser.add_argument("--single-run", required=False, default=False, action="store_true", help="Run a single reconcile and then exit")
    parser.add_argument("--enable-prometheus", required=False, default=False, action="store_true", help="Enable the Prometheus exporter")
    parser.add_argument("--prometheus-host", required=False, default="127.0.0.1", help="The host at which the Prometheus exporter should listen to")
    parser.add_argument("--prometheus-port", required=False, default="9100", type=int, help="The port at which the Prometheus exporter should listen to")
    parser.add_argument("--log-level", help="Minimum log level. Accepted values are: DEBUG, INFO, WARNING, ERROR, CRITICAL", default="INFO")

    return parser.parse_args(argv)


def reconcile(serviceId: str, serviceRegion: str, instancesRegion: List[str]):
    logger = logging.getLogger()

    try:
        success = unmapTerminatedInstancesFromService(serviceId, serviceRegion, instancesRegion)
    except Exception as error:
        logger.error(f"An error occurred while reconciling service {serviceId}: {str(error)}")
        success = False

    if success:
        lastReconcileTimestampMetric.labels(serviceId).set(int(time.time()))


def main(args):
    shutdown = False

    # Init logger
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
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

    # Start Prometheus exporter
    if args.enable_prometheus:
        start_http_server(args.prometheus_port, args.prometheus_host)
        logger.info("Prometheus exporter listening on {host}:{port}".format(port=args.prometheus_port, host=args.prometheus_host))

    # Set the up metric value, which will be steady to 1 for the entire app lifecycle
    upMetric.labels(args.service_id).set(1)

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
