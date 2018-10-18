package utils

import (
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/common"
)

func NewSecret(shootCluster *v1alpha1.ShootCluster) *corev1.Secret {
	if shootCluster == nil {
		return nil
	}

	name, exists := shootCluster.GetLabels()[common.LabelForTargetSecret]
	if !exists {
		return nil
	}

	secret := &corev1.Secret{
		TypeMeta: v1.TypeMeta{
			Kind:       "Secret",
			APIVersion: "v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      name,
			Namespace: shootCluster.GetNamespace(),
		},
		Type: "Opaque",
		Data: make(map[string][]byte),
	}
	return secret
}
