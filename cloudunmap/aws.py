from typing import List


def listEC2InstancesById(instanceIds: List[str], ec2Client):
    instances = []

    # Create a paginator
    paginator = ec2Client.get_paginator("describe_instances")

    # Filter instances by instance id, without breaking if
    # an instance ID is missing or invalid
    filters = [{"Name": "instance-id", "Values": instanceIds}]

    # Pick instances from all pages
    for page in paginator.paginate(Filters=filters, PaginationConfig={"PageSize": 1000}):
        if "Reservations" not in page:
            continue

        for reservation in page["Reservations"]:
            if "Instances" in reservation:
                instances += reservation["Instances"]

    return instances


def listServiceInstances(serviceId: str, sdClient):
    instances = []

    # Create a paginator
    paginator = sdClient.get_paginator("list_instances")

    # Pick instances from all pages
    for page in paginator.paginate(ServiceId=serviceId, PaginationConfig={"PageSize": 100}):
        instances += page["Instances"]

    return instances
