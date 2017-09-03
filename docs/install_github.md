# Create a Github OAuth Application
As Authorization URL use:

    http://<URL>:<DashboardNodePort>/github/auth/callback

# Create github credentials
Creating github secret is only necessary if 'github.enabled = true'.

    kubectl -n infrabox-system create secret generic \
        infrabox-github \
        --from-literal=client_id=<CLIENT_ID> \
        --from-literal=client_secret=<CLIENT_SECRET> \
        --from-literal=webhook_secret=<WEBHOOK_SECRET>
