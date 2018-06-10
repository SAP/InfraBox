# Configure GitHub

To be able to use the GitHub integration you first have to create an OAuth application. See [here](https://developer.github.com/apps/building-integrations/setting-up-and-registering-oauth-apps/registering-oauth-apps/) for some instructions on how to create it.

As "Authorization callback URL" use:

    https://<YOUR_DOMAIN>/github/auth/callback

When configuring your InfraBox with `helm` set these options:

```yaml
github:
    # Enable Github
    enabled: true

    # Client ID of you Github App
    client_id: # <REQUIRED>

    # Client Secret of your Github App
    client_secret: # <REQUIRED>

    # A secret for the webhooks
    webhook_secret: # <REQUIRED>

    login:
        # If true then user can login with the Github account
        enabled: false

        # Github Login URL, change it if you use Github Enterprise
        url: https://github.com/login

        # If Github login is enabled you can limit access to users which belong to a certain set of
        # Github Organizations. Comma separated list for Github Organizations (i.e. "Org1,Org2,Org3")
        # If no organization is set everybody can login with its github ccount
        allowed_organizations:

    # Github API URL
    api_url: https://api.github.com
```

In case you use a GitHub Enterprise installation please also change

```yaml
github:
    login:
        url: <YOUR_GITHUB_ENTERPRISE_LOGIN_ENDPOINT>
    api_url: <YOUR_GITHUB_ENTERPRISE_API_ENDPOINT>
```

By default the login with a GitHub account to InfraBox is disabled. If you would like to enable it use

```yaml
github:
    login:
        enabled: true
```

Now your users can login with their GitHub account. If you want to limit login to users belonging to a certain set of GitHub Organizations you can additionaly specify a comma separated list of GitHub Organization names:

```yaml
github:
    login:
        allowed_organizations: Org1,Org2
```

With this only users who belong to at least one of the organization may be able to login.
