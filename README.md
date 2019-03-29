# AWS Cloud (un)Map

External controller to remove terminated EC2 instances from AWS Cloud Map service.


## How it works

This application scans - at a regular interval - the instances registered to a Cloud Map service and match them with the EC2 instances running in 1+ region: it will then deregister any instance registered in the service which doesn't match a running EC2 instance.

Requisites:
- The instance must be registered in the Cloud Map service with Cloud Map instance id equal to the EC2 instance id
- The instance must be registered in the Cloud Map service with `AWS_INSTANCE_IPV4` attribute (can be the private or public IP address)

How the matching is done:
- A registered instance is considered valid if **both** the instance id and the `AWS_INSTANCE_IPV4` address match a running EC2 instance
- A registered instance is skipped (left untouched) if registered without `AWS_INSTANCE_IPV4` attribute

Safety countermeasures:
- The application logs a warning and do **not** deregister the unmatching instances, in case that would leave the service without registered instance
- The application handles graceful shutdown on `SIGINT` and `SIGTERM`. If such signals are received during a reconciling, it would complete the on-going reconcile before exiting

## How to run it

You have two options to run it:

1. Manually install and run the [`aws-cloud-unmap` Python package](https://pypi.org/project/aws-cloud-unmap/)
   ```
   pip3 install aws-cloud-unmap

   aws-cloud-unmap --service-id srv-12345 --service-region us-east-1 --instances-region us-east-1
   ```

2. Use the [Docker image available on Docker hub](https://hub.docker.com/u/spreaker/aws-cloud-unmap/)
   ```
   docker run --env AWS_ACCESS_KEY_ID="id" --env AWS_SECRET_ACCESS_KEY="secret" spreaker/aws-cloud-unmap --service-id srv-12345 --service-region us-east-1 --instances-region us-east-1
   ```


The cli supports the following arguments:

| Argument                                 | Required | Description |
| ---------------------------------------- | -------- | ----------- |
| `--service-id ID`                        | yes      | AWS CloudMap service ID |
| `--service-region REGION`                | yes      | AWS CloudMap service region |
| `--instances-region REGION [REGION ...]` | yes      | AWS regions where EC2 instances should be checked |
| `--frequency N`                          |          | How frequently the service should be reconciled (in seconds). Defaults to `300` sec |
| `--single-run`                           |          | Run a single reconcile and then exit |
| `--log-level LOG_LEVEL`                  |          | Minimum log level. Accepted values are: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Defaults to `INFO` |


## Development

Run the development environment:

```
docker-compose build dev && docker-compose run --rm dev
```

Run tests in the dev environment:

```
python3 -m unittest
```


## License

This software is released under the [MIT license](LICENSE.txt).

