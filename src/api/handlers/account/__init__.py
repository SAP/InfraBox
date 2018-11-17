import os

if os.environ['INFRABOX_ACCOUNT_LDAP_ENABLED'] == 'true':
    import api.handlers.account.account_ldap
else:
    import api.handlers.account.account

if os.environ['INFRABOX_ACCOUNT_SAML_ENABLED'] == 'true':
    import api.handlers.account.saml

if os.environ['INFRABOX_GITHUB_ENABLED'] == 'true':
    import api.handlers.account.github
