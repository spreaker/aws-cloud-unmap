import unittest
import boto3
from botocore.stub import Stubber
from cloudunmap.aws import listEC2InstancesById, listServiceInstances
from .mocks import mockEC2Instance, mockServiceInstance


class TestAws(unittest.TestCase):
    #
    # listEC2InstancesById()
    #

    def testListEC2InstancesByIdShouldReturnEc2InstancesFilteredByInputIds(self):
        ec2Client = boto3.client("ec2")

        # Mock EC2 client
        stubber = Stubber(ec2Client)
        stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [mockEC2Instance("i-1", privateIp="172.0.0.1"), mockEC2Instance("i-2", privateIp="172.0.0.2", publicIp="2.2.2.2")]}]},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2"]}], "MaxResults": 1000})
        stubber.activate()

        instances = listEC2InstancesById(["i-1", "i-2"], ec2Client)
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0]["InstanceId"], "i-1")
        self.assertEqual(instances[1]["InstanceId"], "i-2")

        stubber.assert_no_pending_responses()

    def testListEC2InstancesByIdShouldReturnEmptyListOnNoMatchingInstances(self):
        ec2Client = boto3.client("ec2")

        # Mock EC2 client
        stubber = Stubber(ec2Client)
        stubber.add_response(
            "describe_instances",
            {"Reservations": []},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2"]}], "MaxResults": 1000})
        stubber.activate()

        instances = listEC2InstancesById(["i-1", "i-2"], ec2Client)
        self.assertEqual(len(instances), 0)

        stubber.assert_no_pending_responses()

    def testListEC2InstancesByIdShouldRaiseExceptionOnError(self):
        ec2Client = boto3.client("ec2")

        # Mock EC2 client
        stubber = Stubber(ec2Client)
        stubber.add_client_error("describe_instances")
        stubber.activate()

        with self.assertRaises(Exception):
            listEC2InstancesById(["i-1", "i-2"], ec2Client)

        stubber.assert_no_pending_responses()

    #
    # listServiceInstances()
    #

    def testListServiceInstancesShouldReturnInstancesRegisteredToCloudMapService(self):
        sdClient = boto3.client("servicediscovery")

        # Mock Cloud Map client
        stubber = Stubber(sdClient)
        stubber.add_response(
            "list_instances",
            {"Instances": [mockServiceInstance("i-1", ipv4="172.0.0.1"), mockServiceInstance("i-2", ipv4="2.2.2.2")]},
            {"ServiceId": "srv-1", "MaxResults": 100})
        stubber.activate()

        instances = listServiceInstances("srv-1", sdClient)
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0]["Id"], "i-1")
        self.assertEqual(instances[1]["Id"], "i-2")

        stubber.assert_no_pending_responses()

    def testListServiceInstancesShouldRaiseExceptionOnError(self):
        sdClient = boto3.client("servicediscovery")

        # Mock Cloud Map client
        stubber = Stubber(sdClient)
        stubber.add_client_error("list_instances")
        stubber.activate()

        with self.assertRaises(Exception):
            listServiceInstances("srv-1", sdClient)

        stubber.assert_no_pending_responses()
