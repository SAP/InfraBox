package common

const (
	EnvCredentialSecretName  = "CRENDENTIALS_SECRET" // env variable for name of input secret
	KeyGardenKubectlInSecret = "gardener.conf"

	// output secret
	LabelForTargetSecret = "service.infrabox.net/secret-name"

	// keys of "output" entries
	KeyNameOfShootKubecfgInSecret    = "config"
	KeyNameOfShootKubecfgKeyInSecret = "kubecfg.key"
	KeyNameOfShootCaCrtInSecret      = "ca.crt"
	KeyNameOfShootKubecfgCrtInSecret = "kubecfg.crt"
	KeyNameOfShootUserInSecret       = "username"
	KeyNameOfShootPasswordInSecret   = "password"
	KeyNameOfShootEndpointInSecret   = "endpoint"
)
