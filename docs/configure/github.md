# Configure GitHub

To be able to use the GitHub integration you first have to create a OAuth application. See [here](https://developer.github.com/apps/building-integrations/setting-up-and-registering-oauth-apps/registering-oauth-apps/) for some instructions on how to create it.

As "Authorization callback URL" use:

    http://<URL>:<DashboardNodePort>/github/auth/callback

If you use github.com and not a local GitHub Enterprise installation you may have to tunnel the webhooks. See [these instructions](https://developer.github.com/webhooks/configuring/#using-ngrok) on how you can do it with ngrok.

    --github-enabled
    --github-client-id <GITHUB_CLIENT_ID>
    --github-client-secret <GITHUB_CLIENT_SECRET>
    --github-webhook-secret <CHOSE_A_RANDOM_SECRET>

In case you use a GitHub Enterprise installation please also set

    --github-login-url <YOUR_GITHUB_ENTERPRISE_LOGIN_ENDPOINT>
    --github-api-url <YOUR_GITHUB_ENTERPRISE_API_ENDPOINT>

By default the login with a GitHub account to InfraBox is disabled. If you would like to enable it use

    --github-login-enabled

Now your users can login with their GitHub account.
