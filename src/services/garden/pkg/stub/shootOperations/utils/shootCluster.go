package utils

import (
	"github.com/sap/infrabox/src/services/garden/pkg/apis/garden/v1alpha1"
	"k8s.io/apimachinery/pkg/runtime/schema"
)

func CreateShootCluster() *v1alpha1.ShootCluster {
	shootCluster := &v1alpha1.ShootCluster{}
	shootCluster.Spec.GardenerNamespace = "gnamespace"
	shootCluster.Spec.ShootName = "shootname"
	shootCluster.Spec.SecretBindingRef = "bindingRef"
	shootCluster.Spec.VpcCIDR = "172.0.0.0/16"
	shootCluster.Spec.MinNodes = 42
	shootCluster.Spec.MaxNodes = 42
	shootCluster.SetName("shootClusterName")
	shootCluster.SetNamespace("shootClusterNamespace")
	shootCluster.SetGroupVersionKind(schema.GroupVersionKind{Group: "garden.service.infrabox.net", Version: "v1alpha1", Kind: "ShootCluster"})
	return shootCluster
}
