package utils

func ValidDummyKubeconfig() string {
	return `
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data:
      "lalala=="
    server: https://api.blue.gardener.canary.k8s.ondemand.com:443
  name: canary
contexts:
- context:
    cluster: canary
    user: api-user
  name: canary-context
current-context: canary-context
kind: Config
preferences: {}
users:
- name: api-user
  user:
    token:
      foofafo
`
}
