from flask import Flask, redirect, request, make_response, Response, jsonify, send_file
import requests
import logging
import os
import hashlib


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

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response


# Download Information Endpoint
@app.route('/api/v2/tasks/download', methods=["GET"])
def runner_api():
    # Print out User Agent
    logging.info("User Agent Information: " + request.user_agent.string)

    logging.info("Printing Headers we got from servers: ")
    logging.info(request.headers)

    if request.method == "GET":
        logging.info("GET Request Issued!")

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
            path_to_download = "binaries/{arch}/circleci-launch-agent".format(arch=request_json["arch"])
            
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

            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            headers = [(name, value) for (name, value) in resp.raw.headers.items()
                    if name.lower() not in excluded_headers]

            response = Response(resp.content, resp.status_code, headers)
            return response

# Route to Download Binary
@app.route('/circleci-agent/<version>/<os>/<arch>/circleci-agent', methods=["GET"])
def runner_download(version, os, arch):
    path_to_download = "binaries/{arch}/circleci-launch-agent".format(arch=arch)
    return send_file(path_to_download, attachment_filename='circleci-agent')


# Catch All Route that will Proxy any Requests
@app.route('/', defaults={'path': ''})
@app.route("/<string:path>")
@app.route('/<path:path>')
def catch_all(path):
    # Print out User Agent
    logging.info("User Agent Information: " + request.user_agent.string)

    logging.info("Printing Headers we got from servers: ")
    logging.info(request.headers)

    resp = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, 'https://runner.circleci.com/'),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response


# Run Flask Programmatically
if __name__ == "__main__":
    # Set Debug to true, set host IP to localhost, and set port to 8080
    app.run(debug=True, host="0.0.0.0", port=os.getenv('PORT') or '8080')
