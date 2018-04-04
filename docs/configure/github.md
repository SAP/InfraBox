# Configure GitHub

To be able to use the GitHub integration you first have to create an OAuth application. See [here](https://developer.github.com/apps/building-integrations/setting-up-and-registering-oauth-apps/registering-oauth-apps/) for some instructions on how to create it.

As "Authorization callback URL" use:

    https://<YOUR_DOMAIN>/github/auth/callback

When configuring your InfraBox with `install.py` set these options:

    --github-enabled
    --github-client-id <GITHUB_CLIENT_ID>
    --github-client-secret <GITHUB_CLIENT_SECRET>
    --github-webhook-secret <CHOSE_A_RANDOM_SECRET>

In case you use a GitHub Enterprise installation please also set

    --github-login-url <YOUR_GITHUB_ENTERPRISE_LOGIN_ENDPOINT>
    --github-api-url <YOUR_GITHUB_ENTERPRISE_API_ENDPOINT>

By default the login with a GitHub account to InfraBox is disabled. If you would like to enable it use

    --github-login-enabled

Now your users can login with their GitHub account. If you want to limit login to users belonging to a certain set of GitHub Organizations you can additionaly specify a comma separated list of GitHub Organization names:

    --github-login-allowed-organizations Org1,Org2

With this only users who belong to at least one of the organization may be able to login.
