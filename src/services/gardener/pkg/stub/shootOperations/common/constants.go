package common

const (
	EnvCredentialSecretName  = "CREDENTIALS_SECRET" // env variable for name of input secret
	KeyGardenKubectlInSecret = "gardener.conf"

	// output secret
	LabelForTargetSecret = "service.infrabox.net/secret-name"

	// keys of "output" entries
	KeyNameOfShootKubecfgInSecret    = "config"
	KeyNameOfShootCaCrtInSecret      = "ca.crt"
	KeyNameOfShootKubecfgKeyInSecret = "client.key"
	KeyNameOfShootKubecfgCrtInSecret = "client.crt"
	KeyNameOfShootUserInSecret       = "username"
	KeyNameOfShootPasswordInSecret   = "password"
	KeyNameOfShootEndpointInSecret   = "endpoint"
)
