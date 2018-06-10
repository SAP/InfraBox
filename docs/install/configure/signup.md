# Configure Signup
If you want that every use can signup and login to your InfraBox add the following options when configuring with `helm`:

```yaml
account:
    signup:
        # Enable users to signup with Email/Username/Password
        enabled: false
```

Be aware that everybody with access to InfraBox can signup and login!
