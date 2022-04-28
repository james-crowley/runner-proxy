# CircleCI Runner Proxy

Proxies the the request from CircleCI Runner agent by setting `API URL` configuration parameter. The proxy will hijack the requests for downloading launch agent and task agent.
Once hijacked, they will point to the binaries located in the `binaries/`. 

## Running Runner Proxy
To run the Runner Proxy issue the following command:


```bash
docker run --env PROXY_SERVER=http://runner.circleci-demo-app.com -d -p 80:8080 jimcrowley/runner-proxy:latest 
```

Make sure to set the `PROXY_SERVER` environment variable to point to your own IP/DNS.



## Runner Config
When using the Runner Proxy its recommended to run with the following config:

```yaml
api:
  auth_token: AUTH_TOKEN
  url: http://runner.circleci-demo-app.com

logging:
  file: /opt/circleci/runner.log

runner:
  name: RUNNER_NAME
  command_prefix: ["sudo", "-niHu", "circleci", "--"]
  working_directory: /opt/circleci/workdir/%s
  cleanup_working_directory: true
  disable_auto_update: true
```

Make sure to set the `url` value to your IP/DNS of where your proxy is running.