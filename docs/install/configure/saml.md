# Configure SAML

```yaml
saml:
    # Enables SAML
    enabled: false

    # Define mapping of saml attributes to user details
    format:
        name: '{name}'
        username: '{NameID}'
        email: '{email}'

    settings_path: 'src/api/handlers/account'

    # Strict: In production, the strict parameter MUST be set as "true".
    strict: true
    # Enable debug mode (outputs errors).
    debug: false
    # Service Provider
    sp:
        # ID of SP (must be a URI)
        entityId: # <REQUIRED> https://host/saml/metadata
        assertionConsumerService:
            # callback url where the <Response> from the IdP will be returned
            url: # <REQUIRED> https://host/saml/callback
            # Type of SAML protocol binding for the idp-response
            binding: urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST
        singleLogoutService:
            # callback url where the <Response> from the IdP will be returned
            url: # <REQUIRED> https://host/saml/logout
            # Type of SAML protocol binding for the idp-response
            binding: urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect
        # SAML Format
        NameIDFormat: # <REQUIRED>
        # SP certificate
        x509cert: # <REQUIRED>
        # SP Private Key
        privateKey: # <REQUIRED>

    # Identity Provider
    idp:
        # IdP entityID
        entityId: # <REQUIRED>
        singleSignOnService:
            # url to sso service
            url: # <REQUIRED>
            # Type of SAML-Binding
            binding: urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect
        singleLogoutService:
            # url to slo service
            url: # <REQUIRED>
            # Type of SAML protocol binding
            binding: urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect
        # Public IdP certificate
        x509cert: # <REQUIRED>

    # Advanced settings for saml-security
    advanced:
        nameIdEncrypted: false
        authnRequestsSigned: true
        logoutRequestSigned: false
        logoutResponseSigned: false
        signMetadata: false
        wantMessagesSigned: false
        wantAssertionsSigned: true
        wantAssertionsEncrypted: false
        wantNameId: true
        wantNameIdEncrypted: false
        wantAttributeStatement: true
        rejectUnsolicitedResponsesWithInResponseTo: false
        requestedAuthnContext: true
        requestedAuthnContextComparison: exact
        metadataValidUntil: null
        metadataCacheDuration: null
        signatureAlgorithm: http://www.w3.org/2000/09/xmldsig#rsa-sha1
        digestAlgorithm: http://www.w3.org/2000/09/xmldsig#sha1
```

The format strings can be written using the [Python format string syntax](https://docs.python.org/2/library/string.html#format-string-syntax). Used can be the NameID and all attributes provided by the IdP.