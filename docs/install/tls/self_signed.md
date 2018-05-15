# Self signed TLS Certificate
This is ok for testing, but not recommended for production (replace `infrabox.example.com` with your domain):

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /tmp/tls.key -out /tmp/tls.crt -subj "/CN=infrabox.example.com"

Now create a Kubernetes secret for the certificate:

    kubectl create -n infrabox-system secret tls infrabox-tls-certs --key /tmp/tls.key --cert /tmp/tls.crt

**It's important to pass the following option to `install.py` when configuring InfraBox:**

    --general-dont-check-certificates
