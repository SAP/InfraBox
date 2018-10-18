package k8sClientCache

import (
	gardenClientSet "github.com/gardener/gardener/pkg/client/garden/clientset/versioned"
	"k8s.io/client-go/kubernetes"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
)

// interface for getting the k8s clientsets for both, the native kubernetes clientset and the gardener clienset for the same Garden kubernetes cluster. Is returned by the cache
type ClientGetter interface {
	GetK8sClientSet() kubernetes.Interface
	GetGardenClientSet() gardenClientSet.Interface
}

// interface for caches which cache both, the native kubernetes clientset and the gardener clienset for the same Garden kubernetes cluster
type ClientCacher interface {
	Get(shootCluster *v1alpha1.ShootCluster) ClientGetter
}

type KubecfgGetter interface {
	// takes a shootCluster object and returns the full kubeconfig as string (not just a path to the kubecfg)
	Get(shootCluster *v1alpha1.ShootCluster) (string, error)
}
