package mocks

import (
	gardenClientSet "github.com/gardener/gardener/pkg/client/garden/clientset/versioned"
	"k8s.io/client-go/kubernetes"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/k8sClientCache"
)

type K8sClientsCacheMock struct {
	k8sClient       kubernetes.Interface
	gardenK8sClient gardenClientSet.Interface
}

func NewK8sClientCacheMock(k8sClient kubernetes.Interface, gardenK8sClient gardenClientSet.Interface) *K8sClientsCacheMock {
	return &K8sClientsCacheMock{k8sClient: k8sClient, gardenK8sClient: gardenK8sClient}
}

func (cache *K8sClientsCacheMock) GetK8sClientSet() kubernetes.Interface {
	return cache.k8sClient
}
func (cache *K8sClientsCacheMock) GetGardenClientSet() gardenClientSet.Interface {
	return cache.gardenK8sClient
}
func (cache *K8sClientsCacheMock) Get(shootCluster *v1alpha1.ShootCluster) k8sClientCache.ClientGetter {
	return cache
}
