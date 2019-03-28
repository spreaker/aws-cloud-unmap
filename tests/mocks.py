from unittest.mock import MagicMock


def mockBotoSession(clients):
    sessionMock = MagicMock()
    sessionMock.client.side_effect = lambda name, **kwargs: clients[name]

    return sessionMock


def mockServiceInstance(instanceId, ipv4=None):
    instance = {"Id": instanceId, "Attributes": {"AWS_INSTANCE_PORT": "80"}}

    if ipv4:
        instance["Attributes"]["AWS_INSTANCE_IPV4"] = ipv4

    return instance


def mockEC2Instance(instanceId, privateIp=None, publicIp=None, state="running"):
    instance = {"InstanceId": instanceId, "State": {"Name": state}}

    if privateIp:
        instance["PrivateIpAddress"] = privateIp

    if publicIp:
        instance["PublicIpAddress"] = publicIp

    return instance
