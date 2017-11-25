# Quickstart: Upload a build
In this guide we show you how you can run builds on InfraBox without having a github repository. Actually you don't even need git.

For this guide you need:

- A github account (only to login to InfraBox)
- [infraboxcli](https://github.com/InfraBox/cli) (pip install infraboxcli)

## Create a project on InfraBox
First login to the InfraBox dashboard [https://infrabox.ninja/](https://infrabox.ninja/dashboard/#/login) with your github account.

After logging in you can click on the "+" sign at the bottom right corner of the dashboard. Select "upload" and click on *continue*. Give your project a name and click *continue*. Select if the dashboard of your project should be accsible by everybody (public) or only by you and the projects collaborators (private) and click *finish*.

Click on the newly created project name and open the Settings tab. In the *Tokens* section create a new token. Tokens are used by [infraboxcli](https://github.com/InfraBox/cli) to authenticate you. They are like passwords so keep them safe. You can delete a token at any point if you lost it or create a new one. Remember the token as we will need it in following steps.

Open the *Project Information* section and copy the project ID. We need this in the following stepts as well.

## Create a local workflow
We can use [infraboxcli](https://github.com/InfraBox/cli) to intialize a project.

    $ mkdir /tmp/infrabox-project
    $ cd /tmpinfrabox-project
    $ infrabox init

## Push your project
Before we can push the projec to InfraBox we have to configure the environment.

    $ export INFRABOX_CLI_TOKEN=<THE_TOKEN_YOU_CREATED_EARLIER>
    $ export INFRABOX_CLI_PROJECT_ID=<THE_PROJECT_ID>
    $ export INFRABOX_API_URL=https://infrabox.ninja/api/cli

To actually push your project run

    $ infrabox push

Open the [dashboard](https://infrabox.ninja/dashboard/#/) and watch your worklfow running.
See the [documentation](https://infrabox.ninja/docs) for more examples on how to configure your builds.
