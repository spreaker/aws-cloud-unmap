# How to publish a new version

**Release python package**:

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. [Release new version on GitHub](https://github.com/spreaker/aws-cloud-unmap/releases)
4. Build package `python3 setup.py sdist`
5. Publish package `twine upload dist/*`

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
