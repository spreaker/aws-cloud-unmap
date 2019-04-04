import unittest
import boto3
import time
from unittest.mock import patch
from botocore.stub import Stubber
from cloudunmap.cli import main, parseArguments, upMetric, lastReconcileTimestampMetric
from .mocks import mockBotoClient, mockServiceInstance, mockEC2Instance
from prometheus_client.registry import REGISTRY as prometheusDefaultRegistry


class TestCli(unittest.TestCase):
    def setUp(self):
        self.ec2Client = boto3.client("ec2")
        self.sdClient = boto3.client("servicediscovery")

        self.sdStubber = Stubber(self.sdClient)
        self.sdStubber.activate()

        self.ec2Stubber = Stubber(self.ec2Client)
        self.ec2Stubber.activate()

        self.botoClientMock = mockBotoClient({"ec2": self.ec2Client, "servicediscovery": self.sdClient})

        try:
            lastReconcileTimestampMetric.remove("srv-1")
            upMetric.remove("srv-1")
        except KeyError:
            pass
    #
    # main()
    #

    def testMainShouldReconcileService(self):
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
            main(parseArguments(["--service-id", "srv-1", "--service-region", "eu-west-1", "--instances-region", "eu-west-1", "--single-run"]))

        # Check exported metrics
        self.assertEqual(prometheusDefaultRegistry.get_sample_value("aws_cloud_unmap_up", labels={"service_id": "srv-1"}), 1)
        self.assertAlmostEqual(prometheusDefaultRegistry.get_sample_value("aws_cloud_unmap_last_reconcile_success_timestamp_seconds", labels={"service_id": "srv-1"}), time.time(), delta=2)

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testMainShouldGracefullyHandleAnErrorWhileCallingAwsAPI(self):
        # Mock Cloud Map client
        self.sdStubber.add_client_error("list_instances")

        with patch("boto3.client", side_effect=self.botoClientMock):
            main(parseArguments(["--service-id", "srv-1", "--service-region", "eu-west-1", "--instances-region", "eu-west-1", "--single-run"]))

        # Check exported metrics
        self.assertEqual(prometheusDefaultRegistry.get_sample_value("aws_cloud_unmap_up", labels={"service_id": "srv-1"}), 1)
        self.assertIsNone(prometheusDefaultRegistry.get_sample_value("aws_cloud_unmap_last_reconcile_success_timestamp_seconds", labels={"service_id": "srv-1"}))

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testMainShouldDoNotDeregisterInstancesIfAllRegisteredInstancesWouldBeDeregistered(self):
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
            main(parseArguments(["--service-id", "srv-1", "--service-region", "eu-west-1", "--instances-region", "eu-west-1", "--single-run"]))

        # Check exported metrics
        self.assertEqual(prometheusDefaultRegistry.get_sample_value("aws_cloud_unmap_up", labels={"service_id": "srv-1"}), 1)
        self.assertIsNone(prometheusDefaultRegistry.get_sample_value("aws_cloud_unmap_last_reconcile_success_timestamp_seconds", labels={"service_id": "srv-1"}))

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()

    def testMainShouldDoNotDeregisterInstancesIfThereAreNoRegisteredInstances(self):
        # Mock Cloud Map client
        self.sdStubber.add_response(
            "list_instances",
            {"Instances": []},
            {"ServiceId": "srv-1", "MaxResults": 100})

        with patch("boto3.client", side_effect=self.botoClientMock):
            main(parseArguments(["--service-id", "srv-1", "--service-region", "eu-west-1", "--instances-region", "eu-west-1", "--single-run"]))

        # Check exported metrics
        self.assertEqual(prometheusDefaultRegistry.get_sample_value("aws_cloud_unmap_up", labels={"service_id": "srv-1"}), 1)
        self.assertAlmostEqual(prometheusDefaultRegistry.get_sample_value("aws_cloud_unmap_last_reconcile_success_timestamp_seconds", labels={"service_id": "srv-1"}), time.time(), delta=2)

        self.ec2Stubber.assert_no_pending_responses()
        self.sdStubber.assert_no_pending_responses()
