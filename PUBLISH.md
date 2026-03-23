# How to publish a new version

**Release python package**:

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. [Release new version on GitHub](https://github.com/spreaker/aws-cloud-unmap/releases)
4. Build package `rm -f dist/* && python3 setup.py sdist`
5. Publish package `twine upload dist/*`

**Release Docker image**:

1. Update package version in `Dockerfile`
2. Login to `Public ECR` (infrastructure prod account, profile `infra-prod`)
   ```
   aws ecr-public get-login-password --profile infra-prod --region us-east-1 \
     | docker login --username AWS --password-stdin public.ecr.aws/spreaker
   ```
3. Build image
   ```
   docker build -t aws-cloud-unmap:REPLACE-VERSION .
   ```

4. Tag image for `Public ECR`
   ```
   docker tag aws-cloud-unmap:REPLACE-VERSION \
     public.ecr.aws/spreaker/aws-cloud-unmap:REPLACE-VERSION
   ```

5. Push image to `Public ECR`
   ```
   docker push public.ecr.aws/spreaker/aws-cloud-unmap:REPLACE-VERSION
   ```
