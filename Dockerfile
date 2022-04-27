FROM python:3.9-alpine

ARG USER=demo
ARG GROUP=demo
ARG UID=1000
ARG GID=1000
ARG PORT=8080
ARG PROXY_SERVER=localhost:8080

# Set enviroment variable for Flask
ENV PORT=${PORT}
ENV PROXY_SERVER=${PROXY_SERVER}

# Expose the server port
EXPOSE ${PORT}

# Update and Upgrade Packages for Alpine
RUN apk -U upgrade

# Copy in requirements file for demo
COPY . /demo

# Add a group and user to not use root
# Then set permissions to the demo files
RUN addgroup --gid ${GID} ${GROUP} \
  && adduser --disabled-password --no-create-home --home "/demo" --uid ${UID} --ingroup ${GROUP} ${USER} \
  && chown -R ${UID}:${GID} /demo

# Set Working Directory
WORKDIR /demo

# Use the production requirements file to install needed Python Packages
# Then delete requirements and tests folder as they are not needed
RUN pip install --no-cache-dir -r production.txt \
    && rm -rf production.txt

# Switch to non-root user
USER demo

# Set Python3 as entrypoint
# Using -u for unbuffered ouput
ENTRYPOINT ["python3", "-u"]

# Run the Flask Demo
CMD ["app.py"]