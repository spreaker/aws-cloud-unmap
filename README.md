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
- The application logs a warning and do **not** deregister the unmatching instances, if after the deregistering the service would have been left with no instances registered
- The application handle graceful shutdown on `SIGINT` and `SIGTERM`. If such signals are received during a reconciling, it completed the on-going reconcile before exiting


## How to run it

Available arguments:

```
--service-id ID       AWS CloudMap service ID
--service-region REGION
                      AWS CloudMap service region
--instances-region REGION [REGION ...]
                      AWS region where EC2 instances should be checked
--frequency-sec N     How frequently the service should be reconciled (in seconds)
--single-run          Run a single reconcile and then exit
--log-level LOG_LEVEL
                      Minimum log level. Accepted values are: DEBUG, INFO,
                      WARNING, ERROR, CRITICAL
```


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

