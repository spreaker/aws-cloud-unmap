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


### How to publish a new version

**Release python package**:

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. [Release new version on GitHub](https://github.com/spreaker/aws-cloud-unmap/releases)
4. Run `python3 setup.py sdist upload -r pypi`

**Release Docker image**:

1. Update package version in `Dockerfile`
2. Build image
   ```
   docker rmi -f aws-cloud-unmap && \
   docker build -t aws-cloud-unmap .
   ```
3. Tag the image and push it to Docker Hub
   ```
   docker tag aws-cloud-unmap spreaker/aws-cloud-unmap:latest && \
   docker push spreaker/aws-cloud-unmap:latest

   docker tag aws-cloud-unmap spreaker/aws-cloud-unmap:REPLACE-VERSION && \
   docker push spreaker/aws-cloud-unmap:REPLACE-VERSION
   ```


## License

This software is released under the [MIT license](LICENSE.txt).

