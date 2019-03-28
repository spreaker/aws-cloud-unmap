import argparse
import boto3
import botocore
import logging
import time
from pythonjsonlogger import jsonlogger
from typing import List
from .aws import listServiceInstances, listEC2InstancesById


def matchServiceInstanceInRunningInstances(serviceInstance, runningInstances):
    serviceInstanceId = serviceInstance["Id"]
    serviceInstanceIp = serviceInstance["Attributes"]["AWS_INSTANCE_IPV4"]

    for runningInstance in runningInstances:
        # The instance ID must match
        if runningInstance["InstanceId"] != serviceInstanceId:
            continue

        # The service IP must match any of the instance IPs
        if "PublicIpAddress" in runningInstance and runningInstance["PublicIpAddress"] == serviceInstanceIp:
            return True
        elif "PrivateIpAddress" in runningInstance and runningInstance["PrivateIpAddress"] == serviceInstanceIp:
            return True

    return False


def reconcile(serviceId: str, serviceRegion: str, instancesRegions: List[str]):
    logger = logging.getLogger()
    logger.info(f"Checking EC2 instances registered to service {serviceId} in {serviceRegion}")

    # Customize the boto client config
    botoConfig = botocore.client.Config(connect_timeout=5, read_timeout=15, retries={"max_attempts": 2})
    botoSession = boto3.Session()

    # Instance Cloud Map client
    sdClient = botoSession.client("servicediscovery", config=botoConfig, region_name=serviceRegion)

    # Instance EC2 clients
    ec2Clients = [botoSession.client("ec2", config=botoConfig, region_name=region) for region in instancesRegions]

    # List registered instances on CloudMap
    serviceInstances = listServiceInstances(serviceId, sdClient)

    # Filter out service instances without the AWS_INSTANCE_IPV4 attribute
    # and extract instance ids
    serviceInstances = list(filter(lambda i: "AWS_INSTANCE_IPV4" in i["Attributes"], serviceInstances))
    serviceInstancesId = list(map(lambda i: i["Id"], serviceInstances))

    # List EC2 instances in all expected regions
    runningInstances = []

    for ec2Client in ec2Clients:
        instances = listEC2InstancesById(serviceInstancesId, ec2Client)

        # Filter out terminated instances
        instances = list(filter(lambda i: i["State"]["Name"] != "shutting-down" and i["State"]["Name"] != "terminated", instances))

        runningInstances += instances

    # Find the list of unmatching instances. The match is done both by
    # instance ID and IP, to avoid edge cases with recycled IPs on different
    # instance IDs
    unmatchingInstances = list(filter(lambda i: not matchServiceInstanceInRunningInstances(i, runningInstances), serviceInstances))

    # Circuit breaker: ensure that we're not going to remove ALL instances
    # from the service
    if len(unmatchingInstances) >= len(serviceInstances):
        logger.warning(f"All instances registered to service {serviceId} appear to not match any running EC2 instance in {instancesRegions}, but skipping deregistering as safe protection")
        return

    # Remove all unmatching instances from the service
    logger.info(f"Found {len(unmatchingInstances)} in service {serviceId} not matching any running EC2 instance in {instancesRegions}")

    for unmatchingInstance in unmatchingInstances:
        logger.warning(f"Deregistering instance {unmatchingInstance['Id']} from service {serviceId} because not matching any running EC2 instance in {instancesRegions}")
        sdClient.deregister_instance(ServiceId=serviceId, InstanceId=unmatchingInstance["Id"])

    logger.info(f"Checked EC2 instances registered to service {serviceId} in {serviceRegion}")


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

        reconcile(args.service_id, args.service_region, args.instances_region)

        elapsedTime = time.monotonic() - startTime

        # Honor frequency
        if elapsedTime < frequencySec:
            time.sleep(frequencySec - elapsedTime)


if __name__ == '__main__':
    main()
