import unittest
import boto3
from unittest.mock import patch
from botocore.stub import Stubber
from cloudunmap.unmap import matchServiceInstanceInRunningInstances, unmapTerminatedInstancesFromService
from .mocks import mockBotoClient, mockServiceInstance, mockEC2Instance


class TestUnmap(unittest.TestCase):
    def setUp(self):
        self.ec2Client = boto3.client("ec2")
        self.sdClient = boto3.client("servicediscovery")

        self.sdStubber = Stubber(self.sdClient)
        self.sdStubber.activate()

        self.ec2Stubber = Stubber(self.ec2Client)
        self.ec2Stubber.activate()

        self.botoClientMock = mockBotoClient({"ec2": self.ec2Client, "servicediscovery": self.sdClient})

    #
    # matchServiceInstanceInRunningInstances()
    #

    def testMatchServiceInstanceInRunningInstances(self):
        runningInstances = [
            {"InstanceId": "i-1", "PrivateIpAddress": "172.0.0.1"},
            {"InstanceId": "i-2", "PrivateIpAddress": "172.0.0.2", "PublicIpAddress": "2.2.2.2"}
        ]

        self.assertFalse(matchServiceInstanceInRunningInstances(
            {"Id": "i-1", "Attributes": {"AWS_INSTANCE_IPV4": "172.0.0.1"}}, []))

        self.assertTrue(matchServiceInstanceInRunningInstances(
            {"Id": "i-1", "Attributes": {"AWS_INSTANCE_IPV4": "172.0.0.1"}}, runningInstances))

        self.assertFalse(matchServiceInstanceInRunningInstances(
            {"Id": "i-x", "Attributes": {"AWS_INSTANCE_IPV4": "172.0.0.1"}}, runningInstances))

        self.assertFalse(matchServiceInstanceInRunningInstances(
            {"Id": "i-1", "Attributes": {"AWS_INSTANCE_IPV4": "172.0.0.2"}}, runningInstances))

        self.assertTrue(matchServiceInstanceInRunningInstances(
            {"Id": "i-2", "Attributes": {"AWS_INSTANCE_IPV4": "172.0.0.2"}}, runningInstances))

        self.assertTrue(matchServiceInstanceInRunningInstances(
            {"Id": "i-2", "Attributes": {"AWS_INSTANCE_IPV4": "2.2.2.2"}}, runningInstances))

    #
    # unmapTerminatedInstancesFromService()
    #

    def testUnmapTerminatedInstancesFromServiceShouldDoNothingIfRegisteredInstancesAreRunning(self):
        # Mock Cloud Map client
        self.sdStubber.add_response(
            "list_instances",
            {"Instances": [mockServiceInstance("i-1", "172.0.0.1"), mockServiceInstance("i-2", "2.2.2.2")]},
            {"ServiceId": "srv-1", "MaxResults": 100})

        # Mock EC2 client
        self.ec2Stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [
                mockEC2Instance("i-1", privateIp="172.0.0.1"),
                mockEC2Instance("i-2", privateIp="172.0.0.2", publicIp="2.2.2.2"),
            ]}]},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2"]}], "MaxResults": 1000})

        with patch("boto3.client", side_effect=self.botoClientMock):
            unmapTerminatedInstancesFromService(serviceId="srv-1", serviceRegion="eu-west-1", instancesRegions=["eu-west-1"])

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testUnmapTerminatedInstancesFromServiceShouldDeregisterInstancesNotFound(self):
        # Mock Cloud Map client
        self.sdStubber.add_response(
            "list_instances",
            {"Instances": [mockServiceInstance("i-1", "172.0.0.1"), mockServiceInstance("i-2", "2.2.2.2")]},
            {"ServiceId": "srv-1", "MaxResults": 100})
        self.sdStubber.add_response(
            "deregister_instance",
            {},
            {"ServiceId": "srv-1", "InstanceId": "i-2"})

        # Mock EC2 client
        self.ec2Stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [
                mockEC2Instance("i-1", privateIp="172.0.0.1"),
            ]}]},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2"]}], "MaxResults": 1000})

        with patch("boto3.client", side_effect=self.botoClientMock):
            unmapTerminatedInstancesFromService(serviceId="srv-1", serviceRegion="eu-west-1", instancesRegions=["eu-west-1"])

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testUnmapTerminatedInstancesFromServiceShouldDeregisterInstancesFoundButWithDifferentIp(self):
        # Mock Cloud Map client
        self.sdStubber.add_response(
            "list_instances",
            {"Instances": [mockServiceInstance("i-1", "172.0.0.1"), mockServiceInstance("i-2", "2.2.2.2")]},
            {"ServiceId": "srv-1", "MaxResults": 100})
        self.sdStubber.add_response(
            "deregister_instance",
            {},
            {"ServiceId": "srv-1", "InstanceId": "i-2"})

        # Mock EC2 client
        self.ec2Stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [
                mockEC2Instance("i-1", privateIp="172.0.0.1"),
                mockEC2Instance("i-2", publicIp="1.1.1.1"),
            ]}]},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2"]}], "MaxResults": 1000})

        with patch("boto3.client", side_effect=self.botoClientMock):
            unmapTerminatedInstancesFromService(serviceId="srv-1", serviceRegion="eu-west-1", instancesRegions=["eu-west-1"])

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testUnmapTerminatedInstancesFromServiceShouldDeregisterInstancesFoundButTerminating(self):
        # Mock Cloud Map client
        self.sdStubber.add_response(
            "list_instances",
            {"Instances": [mockServiceInstance("i-1", "172.0.0.1"), mockServiceInstance("i-2", "2.2.2.2")]},
            {"ServiceId": "srv-1", "MaxResults": 100})
        self.sdStubber.add_response(
            "deregister_instance",
            {},
            {"ServiceId": "srv-1", "InstanceId": "i-2"})

        # Mock EC2 client
        self.ec2Stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [
                mockEC2Instance("i-1", privateIp="172.0.0.1"),
                mockEC2Instance("i-2", privateIp="172.0.0.2", publicIp="2.2.2.2", state="shutting-down"),
            ]}]},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2"]}], "MaxResults": 1000})

        with patch("boto3.client", side_effect=self.botoClientMock):
            unmapTerminatedInstancesFromService(serviceId="srv-1", serviceRegion="eu-west-1", instancesRegions=["eu-west-1"])

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testUnmapTerminatedInstancesFromServiceShouldDeregisterInstancesFoundButTerminated(self):
        # Mock Cloud Map client
        self.sdStubber.add_response(
            "list_instances",
            {"Instances": [mockServiceInstance("i-1", "172.0.0.1"), mockServiceInstance("i-2", "2.2.2.2")]},
            {"ServiceId": "srv-1", "MaxResults": 100})
        self.sdStubber.add_response(
            "deregister_instance",
            {},
            {"ServiceId": "srv-1", "InstanceId": "i-2"})

        # Mock EC2 client
        self.ec2Stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [
                mockEC2Instance("i-1", privateIp="172.0.0.1"),
                mockEC2Instance("i-2", privateIp="172.0.0.2", publicIp="2.2.2.2", state="terminated"),
            ]}]},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2"]}], "MaxResults": 1000})

        with patch("boto3.client", side_effect=self.botoClientMock):
            unmapTerminatedInstancesFromService(serviceId="srv-1", serviceRegion="eu-west-1", instancesRegions=["eu-west-1"])

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testUnmapTerminatedInstancesFromServiceShouldSkipRegisteredInstancesWithoutIpv4Attribute(self):
        # Mock Cloud Map client
        self.sdStubber.add_response(
            "list_instances",
            {"Instances": [mockServiceInstance("i-1", "172.0.0.1"), mockServiceInstance("i-2", ipv4=None)]},
            {"ServiceId": "srv-1", "MaxResults": 100})

        # Mock EC2 client
        self.ec2Stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [
                mockEC2Instance("i-1", privateIp="172.0.0.1"),
            ]}]},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1"]}], "MaxResults": 1000})

        with patch("boto3.client", side_effect=self.botoClientMock):
            unmapTerminatedInstancesFromService(serviceId="srv-1", serviceRegion="eu-west-1", instancesRegions=["eu-west-1"])

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testUnmapTerminatedInstancesFromServiceShouldDoNothingIfAllRegisteredInstancesWouldBeDeregistered(self):
        # Mock Cloud Map client
        self.sdStubber.add_response(
            "list_instances",
            {"Instances": [mockServiceInstance("i-1", "172.0.0.1"), mockServiceInstance("i-2", "2.2.2.2")]},
            {"ServiceId": "srv-1", "MaxResults": 100})

        # Mock EC2 client
        self.ec2Stubber.add_response(
            "describe_instances",
            {"Reservations": []},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2"]}], "MaxResults": 1000})

        with patch("boto3.client", side_effect=self.botoClientMock):
            unmapTerminatedInstancesFromService(serviceId="srv-1", serviceRegion="eu-west-1", instancesRegions=["eu-west-1"])

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testUnmapTerminatedInstancesFromServiceShouldSupportMultipleInstancesRegions(self):
        # Mock Cloud Map client
        self.sdStubber.add_response(
            "list_instances",
            {"Instances": [mockServiceInstance("i-1", "172.0.0.1"), mockServiceInstance("i-2", "2.2.2.2"), mockServiceInstance("i-3", "3.3.3.3")]},
            {"ServiceId": "srv-1", "MaxResults": 100})
        self.sdStubber.add_response(
            "deregister_instance",
            {},
            {"ServiceId": "srv-1", "InstanceId": "i-3"})

        # Mock EC2 client
        self.ec2Stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [mockEC2Instance("i-1", privateIp="172.0.0.1")]}]},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2", "i-3"]}], "MaxResults": 1000})
        self.ec2Stubber.add_response(
            "describe_instances",
            {"Reservations": [{"Instances": [mockEC2Instance("i-2", publicIp="2.2.2.2")]}]},
            {"Filters": [{"Name": "instance-id", "Values": ["i-1", "i-2", "i-3"]}], "MaxResults": 1000})

        with patch("boto3.client", side_effect=self.botoClientMock):
            unmapTerminatedInstancesFromService(serviceId="srv-1", serviceRegion="eu-west-1", instancesRegions=["eu-west-1", "us-east-1"])

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()
