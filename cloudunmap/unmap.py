import boto3
import botocore
import logging
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


def unmapTerminatedInstancesFromService(serviceId: str, serviceRegion: str, instancesRegions: List[str]):
    logger = logging.getLogger()
    logger.info(f"Checking EC2 instances registered to service {serviceId} in {serviceRegion}")

    # Customize the boto client config
    botoConfig = botocore.client.Config(connect_timeout=5, read_timeout=15, retries={"max_attempts": 2})

    # Instance Cloud Map client
    sdClient = boto3.client("servicediscovery", config=botoConfig, region_name=serviceRegion)

    # Instance EC2 clients
    ec2Clients = [boto3.client("ec2", config=botoConfig, region_name=region) for region in instancesRegions]

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
    logger.info(f"Found {len(unmatchingInstances)} instances in service {serviceId} not matching any running EC2 instance in {instancesRegions}")

    for unmatchingInstance in unmatchingInstances:
        logger.warning(f"Deregistering instance {unmatchingInstance['Id']} from service {serviceId} because not matching any running EC2 instance in {instancesRegions}")
        sdClient.deregister_instance(ServiceId=serviceId, InstanceId=unmatchingInstance["Id"])

    logger.info(f"Checked EC2 instances registered to service {serviceId} in {serviceRegion}")
