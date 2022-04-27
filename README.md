# CircleCI Runner Proxy

Proxies the the request from CircleCI Runner agent by setting `API URL` configuration parameter.

To use the proxy, run the docker container and set the `api.url` parameter in your runner's config to IP/DNS of where your proxy is hosted.

Make sure to set the `PROXY_SERVER` environment variable inside the docker container to your IP/DNS. 