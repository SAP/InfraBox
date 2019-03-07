# SSH Keys for accessing private repositories on Github

Adding a private github repository works like adding a public github repository. No additional work is necessary.

If you have a repository which uses submodules and one or multiple of your submodules are private repositories then you may run into authentication errors. InfraBox generates one deploy key for each connected repository, but not for the submodule repositories. So cloning the submodules will fail, because InfraBox knows only about the deploy key for the root repository.

To make this work you can configure a global ssh key in your InfraBox project:

1. Create a [machine user on Github](https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users)
2. Give the machine user account access to all the repositories which you need to clone for your InfraBox builds
3. Add an SSH Key to the machine user account
4. Go to your InfraBox project settings tab
    1. Create a secret in your InfraBox project with the private SSH key you created in step 3)
    2. Add the SSH key to your InfraBox project by giving it a name and selecting the secret name you created in step 4.1)

Now your jobs should be able to clone all the required repositories.