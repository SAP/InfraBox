# Open Policy Agent (OPA)

InfraBox uses [Open Policy Agent](https://www.openpolicyagent.org/docs/) for authorization management. The InfraBox API will connect to an Open Policy Agent server defined by the environment variables `INFRABOX_OPA_HOST` for the hostname and `INFRABOX_OPA_PORT` for the port the OPA server is listening on.

## Starting the OPA service for development

The Open Policy Agent server can be started isolated by running:

``` bash
./ib.py services start opa
```

By default the service will be listening on port `8181`.


The built docker image will come with these policy files preloaded.

## Pushing updated data to OPA

To determine authorized and unauthorized requests the OPA service is required to have access to up-to-date information such as which projects are public and which users are collaborators to which projects. Therefore, this data is repeatedly pushed by the API to the OPA service.
The interval of the push in seconds is set in the environment variable `INFRABOX_OPA_PUSH_INTERVAL`.