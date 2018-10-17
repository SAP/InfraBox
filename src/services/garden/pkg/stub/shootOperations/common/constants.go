package common

const EnvCredentialSecretName = "CRENDENTIALS_SECRET"	// env variable for name of input secret
const KeyGardenKubectlInSecret = "garden_kubecfg"

// output secret
const LabelForTargetSecret = "service.infrabox.net/secret-name"

// keys of "output" entries
const KeyNameOfShootKubecfgInSecret = "config"
const KeyNameOfShootKubecfgKeyInSecret = "kubecfg.key"
const KeyNameOfShootCaCrtInSecret = "ca.crt"
const KeyNameOfShootKubecfgCrtInSecret = "kubecfg.crt"
const KeyNameOfShootUserInSecret = "username"
const KeyNameOfShootPasswordInSecret = "password"