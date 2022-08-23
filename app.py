from flask import Flask, redirect, request, make_response, Response, jsonify, send_file
import requests
import logging
import os
import hashlib


# Setting up Basic Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)


# Perform a SHA256 Checksum
def sha256sum(filename):
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()

# Proxy Request
def _proxy(*args, **kwargs):
    resp = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, 'https://runner.circleci.com/'),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = []
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response

# Release Endpoint
@app.route('/circleci-launch-agent/release.txt', methods=["GET"])
def release():
    # Print out User Agent
    logging.info("User Agent Information: " + request.user_agent.string)

    logging.info("Printing Headers we got from servers: ")
    logging.info(request.headers)

    resp = requests.request(
            method=request.method,
            url=request.url.replace(request.host_url, 'https://circleci-binary-releases.s3.amazonaws.com/'),
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

    excluded_headers = []
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
            if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)

    return response


@app.route('/circleci-agent/release.txt', methods=["GET"])
def release():
    # Print out User Agent
    logging.info("User Agent Information: " + request.user_agent.string)

    logging.info("Printing Headers we got from servers: ")
    logging.info(request.headers)

    resp = requests.request(
            method=request.method,
            url=request.url.replace(request.host_url, 'https://circleci-binary-releases.s3.amazonaws.com/'),
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

    excluded_headers = []
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
            if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)

    return response


# Checksum Endpoint
@app.route('/circleci-launch-agent/<version>/checksums.txt', methods=["GET"])
def checksum(version):
    # Print out User Agent
    logging.info("User Agent Information: " + request.user_agent.string)

    logging.info("Printing Headers we got from servers: ")
    logging.info(request.headers)

    resp = requests.request(
            method=request.method,
            url=request.url.replace(request.host_url, 'https://circleci-binary-releases.s3.amazonaws.com/'),
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

    excluded_headers = []
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
            if name.lower() not in excluded_headers]

    # Generate Checksums and add them to the official checksums
    s390x_checksum = sha256sum("binaries/s390x/circleci-launch-agent")
    ppc64le_checksum = sha256sum("binaries/ppc64le/circleci-launch-agent")

    s390x_string = s390x_checksum + " *linux/s390x/circleci-launch-agent\n"
    ppc64le_string = ppc64le_checksum + " *linux/ppc64le/circleci-launch-agent\n"
    context_string = resp.content.decode("utf-8") + s390x_string + ppc64le_string

    response = Response(str.encode(context_string), resp.status_code, headers)

    return response


# Download Information Endpoint
@app.route('/api/v2/tasks/download', methods=["GET"])
def runner_api():
    # Print out User Agent
    logging.info("User Agent Information: " + request.user_agent.string)

    logging.info("Printing Headers we got from servers: ")
    logging.info(request.headers)


    # Grab JSON Body from the request
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        request_json = request.json
        logging.info("Printing JSON Body we got from servers: ")
        logging.info(request_json)

    # If Architecture is s390x or ppc64le, then hijack the request and redirect the download to our webserver
    if request_json["arch"] == "s390x" or request_json["arch"] == "ppc64le":
        # Template for response
        url = "http://{proxy_server}/circleci-agent/{version}/{os}/{arch}/circleci-agent".format(proxy_server=os.getenv('PROXY_SERVER'), version=request_json["version"], os=request_json["os"], arch=request_json["arch"])
        path_to_download = "binaries/{arch}/circleci-agent".format(arch=request_json["arch"])
        
        # Since we are not building every version of task agent for s390x/ppc64le, just say the version is the version requested and dynamically gerenate checksum
        template = {
            "url": url,
            "checksum": sha256sum(path_to_download),
            "version": request_json["version"]
        }

        # Return and render JSON object
        return jsonify(template), 200

    # Else proxy the request back to the official Runner API
    else:
        resp = requests.request(
            method=request.method,
            url=request.url.replace(request.host_url, 'https://runner.circleci.com/'),
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

        excluded_headers = []
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response


# Route to Build/Task Agent Download
@app.route('/circleci-agent/<version>/<os>/<arch>/circleci-agent', methods=["GET"])
def build_agent_download(version, os, arch):
    # We do not need to redirect request for other architectures since we only accept/give out URLs for s390x/ppc64le
    path_to_download = "binaries/{arch}/circleci-agent".format(arch=arch)
    return send_file(path_to_download, attachment_filename='circleci-agent')


# Route to the Launch Agent or Proxy the Connect to Official Launch Agent Download
@app.route('/circleci-launch-agent/<version>/<os>/<arch>/circleci-launch-agent', methods=["GET"])
def launch_agent_download(version, os, arch):
    # If someone requests the launch agent for s390x/ppc64le
    if arch == "s390x" or arch == "ppc64le":
        path_to_download = "binaries/{arch}/circleci-launch-agent".format(arch=arch)
        return send_file(path_to_download, attachment_filename='circleci-launch-agent')
    # If not s390x/ppc64le, then redirect request back to official S3 Bucket
    else:
        resp = requests.request(
            method=request.method,
            url=request.url.replace(request.host_url, 'https://circleci-binary-releases.s3.amazonaws.com/'),
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

        excluded_headers = []
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response


# Catch All Route that will proxy/redirect all requests back to official runner API
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'DELETE', 'PUT', 'PATCH'])
@app.route("/<string:path>", methods=['GET', 'POST', 'DELETE', 'PUT', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'DELETE', 'PUT', 'PATCH'])
def catch_all(path):
    # Print out User Agent
    logging.info("User Agent Information: " + request.user_agent.string)

    # Print Out Headers
    logging.info("Printing Headers we got from servers: ")
    logging.info(request.headers)

    # Grab JSON Body from the request
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        request_json = request.json
        logging.info("Printing JSON Body we got from servers: ")
        logging.info(request_json)

    # Replace host with official runner API URL
    resp = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, 'https://runner.circleci.com/'),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = []
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response


# Run Flask Programmatically
if __name__ == "__main__":
    # Set Debug to true, set host IP to localhost, and set port to 8080
    app.run(debug=True, host="0.0.0.0", port=os.getenv('PORT') or '8080')
