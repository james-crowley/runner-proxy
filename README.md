# CircleCI Runner Proxy

Proxies the the request from CircleCI Runner agent by setting `API URL` configuration parameter. The proxy will hijack the requests for downloading launch agent and task agent.
Once hijacked, they will point to the binaries located in the `binaries/`. 

## Running Runner Proxy
To run the Runner Proxy issue the following command:

```bash
docker run --env PROXY_SERVER=http://runner.circleci-demo-app.com -d -p 80:8080 jimcrowley/runner-proxy:latest 
```

Make sure to set the `PROXY_SERVER` environment variable to point to your own IP/DNS.


## Runner Install
To install runner on `s390x` or `ppc64le`, you will need to follow the official cli install instructions linked [here](https://circleci.com/docs/2.0/runner-installation-cli/). When following
the official cli install instructions a couple modifications will need to be made.

First, when running the script referenced here, https://circleci.com/docs/2.0/runner-installation-cli/#continued-for-linux-macos-and-server, please change the that refers to the `base_url`:

Here is what the normal line looks like:
```
base_url="https://circleci-binary-releases.s3.amazonaws.com/circleci-launch-agent"
```

Instead of `https://circleci-binary-releases.s3.amazonaws.com/circleci-launch-agent` please use `http://runner.circleci-demo-app.com/circleci-launch-agent` or your proxy's URL/DNS.

After modifiying the install script, please export the correct platform and OS. The example command looks like, `export platform=linux/amd64 && sh ./download-launch-agent.sh`. 
Make sure to replace the platform with either `linux/s390x` or `linux/ppc64le`.

After installing the launch agent follow the directions for your the `linux` platform: https://circleci.com/docs/2.0/runner-installation-linux/. When following the instructions use the 
recommended runner config down below. 


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


## Known Limitations
Currently, `s390x` and `ppc64le` are not officially supported platforms. Using the proxy and instructions are at your own risk and CircleCI will not provide support.

Additionally, the proxy will respond for any version of launch agent or task agent requested. Please note the compiled binaries found in this repo are only compiled
for certain version of the launch agent and task agent. While the proxy will "trick" the launch agent to download the binaries found here in the repo, the underlying version
of the launch agent and task agent will not change. This might lead to the launch agent or task agent breaking in the future due to lack of newer features.

Currently the launch agent is compiled for version: `1.0.35012-2fb4f32` and the task agent is compiled for version: `1.0.122087-0df92f5c`.