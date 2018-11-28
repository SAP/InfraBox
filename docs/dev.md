# Developer Guide
You need these requirementes to be installed on your machine:

- [infraboxcli](https://github.com/SAP/infrabox-cli)
- [docker](https://www.docker.com/)
- python 2.7

## Setup development environment

Install all the python packages you need for development.

```bash
pip install pipenv
pipenv install
```

To activate the environment every time you open a new shell:

```bash
pipenv shell
```

## Build Images
To build all images run:

``` bash
infrabox run ib
./ib.py images build
```

If you want to build them for another registry (default is `localhost:5000`) use the `--registry` and the `--tag` option:

``` bash
./ib.py images build --registry myregistry --tag mytag
```

You may also filter which images to build with the `--filter` option. It takes a regular expression and every image name matchin the regex will be build.

``` bash
./ib.py images build --filter api # builds only api
./ib.py images build --filter '.*' # builds all, default
```

## Push Image
After building the images you may want to push them to a registry.

``` bash
./ib.py images push
```

It also takes the `--registry`, `--tag` and `--filter` options like `images build` does.

## Starting Service
During development you may want to start several services separately to test your changes. You can start services like this:

```bash
./ib.py services start <service_name>
```

Services to start are `storage`, `opa`, `api` and `dashboard-client`.

## Generate Changelog
If you want to create a new changelog file, run:
```bash
./ib.py changelog create
```

Please, not that you should have your **CHANGELOG_GITHUB_TOKEN** path variable specified.
Otherwise, you may want to explicitly specify your token within a command:
```bash
./ib.py changelog create --token=YOUR_TOKEN_HERE
```

See the service's READMEs for details:
- [Storage](/infrabox/utils/storage/)
- [Open Policy Agent](/src/openpolicyagent)
- [API](/src/api/)
- [Dashboard UI](/src/dashboard-client)
