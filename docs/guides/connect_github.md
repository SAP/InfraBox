# Quickstart: Connect github repository
In this guide we show you how you can connect your github repository to InfraBox and run your first build within 3 minutes. We use the InfraBox playground, but the same works on your own InfraBox installation.

For this guide you need:

- A github account
- A repository on github which you want to connect
- [infraboxcli](https://github.com/SAP/InfraBox-cli) (pip install infraboxcli)

## Connect github repository
After logging in you can click on the "+" sign at the bottom right corner of the dashboard. Select "github" and click on *continue*. Give your project a name and select the repository you want to connect and click *continue*. Select if the dashboard of your project should be accsible by everybody (public) or only by you and the projects collaborators (private) and click *finish*.

That's it, your project has been connected to InfraBox. Every time you push to your repository a build on InfraBox will be triggered.

## Trigger a first build
If you have not yet configured any workflow which should be run on InfraBox follow these instructions.

First clone your repository and cd into it. We can now use [infraboxcli](https://github.com/SAP/InfraBox-cli) to create a "hello world" workflow for your project.

    $ infrabox init

This create all the neccessary files for a simple workflow. Let's commit the files and trigger the first build on InfraBox.

    $ git add .
    $ git commit -m "first InfraBox workflow"
    $ git push origin master

See the [documentation](/docs/doc.md) for more examples on how to configure your builds.
