package common

type HealthState string

const (
	Healthy   HealthState = "healthy"
	Unhealthy HealthState = "unhealthy"
)

const NameDhaasSecretWithDefaultCredentials = "default-credentials"
const NameOfDefaultStorageClass = "dh-default-storage-class"

// keys of "input" entries
const KeyGardenKubectlInSecret = "garden_kubecfg"
const KeySecretBindingRefInSecret = "garden_secret_binding_ref"

// keys of "output" entries
const KeyNameOfShootKubecfgInSecret = "config"
const KeyNameOfShootKubecfgKeyInSecret = "kubecfg.key"
const KeyNameOfShootCaCrtInSecret = "ca.crt"
const KeyNameOfShootKubecfgCrtInSecret = "kubecfg.crt"
const KeyNameOfShootUserInSecret = "username"
const KeyNameOfShootPasswordInSecret = "password"
const KeyNameOfK8sStorageClassInSecret = "k8s_storage_class"