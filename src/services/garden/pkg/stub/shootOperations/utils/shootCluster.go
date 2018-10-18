package utils

import (
	"k8s.io/apimachinery/pkg/runtime/schema"

	"github.com/sap/infrabox/src/services/garden/pkg/apis/garden/v1alpha1"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/common"
)

func CreateShootCluster() *v1alpha1.ShootCluster {
	shootCluster := &v1alpha1.ShootCluster{}
	shootCluster.Spec.MinNodes = 42
	shootCluster.Spec.MaxNodes = 42
	shootCluster.SetName("shootClusterName")
	shootCluster.SetNamespace("shootClusterNamespace")
	shootCluster.SetGroupVersionKind(schema.GroupVersionKind{Group: "garden.service.infrabox.net", Version: "v1alpha1", Kind: "ShootCluster"})

	shootCluster.Status.ClusterName = "shootname"
	shootCluster.Status.GardenerNamespace = "gnamespace"

	shootCluster.Labels = map[string]string{common.LabelForTargetSecret : "targetsecret"}
	return shootCluster
}
