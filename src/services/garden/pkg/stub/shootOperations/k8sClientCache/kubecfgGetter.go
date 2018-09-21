package k8sClientCache

import (
	"fmt"

	"github.com/sirupsen/logrus"

	"github.com/sap/infrabox/src/services/garden/pkg/apis/garden/v1alpha1"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/common"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/utils"
)

type StaticKubecfgGetter struct {
	config string // full config, not just a path to some file
}

func NewStaticKubecfgGetter(cfg string) *StaticKubecfgGetter {
	return &StaticKubecfgGetter{config: cfg}
}

func (g *StaticKubecfgGetter) Get(cluster *v1alpha1.ShootCluster) (string, error) {
	return g.config, nil
}

// SecretKubecfgGetter fetches the kubeconfig from a secret. In detail, the secret must be in the same namespace as the
// dhInfra object itself.
type SecretKubecfgGetter struct {
	opsdk common.SdkOperations
}

func NewSecretKubecfgGetter(sdk common.SdkOperations) *SecretKubecfgGetter {
	return &SecretKubecfgGetter{opsdk: sdk}
}

func (g *SecretKubecfgGetter) Get(cluster *v1alpha1.ShootCluster) (string, error) {
	if cluster == nil {
		return "", fmt.Errorf("invalid input: got nil")
	}

	s := utils.NewSecret(cluster)
	err := g.opsdk.Get(s)
	if err != nil {
		logrus.Error("sdk get failed: ", err)
		return "", err
	}

	if cfg, ok := s.Data[common.KeyGardenKubectlInSecret]; !ok {
		logrus.Error("secret doesn't contain garden kubecfg", err)
		return "", fmt.Errorf("secret doesn't contain garden kubecfg")
	} else {
		return string(cfg), nil
	}
}
