FROM alpine:3.9

# Installing required packages
RUN apk add --update --no-cache \
    python3~=3.6

# Install app deps
RUN mkdir /app
ADD ./requirements.txt /app
RUN cd /app && pip3 install -r requirements.txt

# Install app
ADD cloudunmap    /app/cloudunmap
ADD tests         /app/tests
ADD setup.cfg     /app/

# Run as non-root
RUN adduser app -S -u 1000
USER app

# Switch the cwd to /app so that running app and tests is easier
WORKDIR /app

CMD [ "python3", "-m", "cloudunmap.cli" ]
