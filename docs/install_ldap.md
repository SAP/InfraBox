# Configure LDAP with InfraBox

Create credentials:

   kubectl -n  infrabox-system create secret generic \
        infrabox-ldap \
        --from-literal=password=<PASSWORD> \
        --from-literal=dn=<DN>
