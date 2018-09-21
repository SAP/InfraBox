package shootOperations

import (
	"github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	gardenClientSet "github.com/gardener/gardener/pkg/client/garden/clientset/versioned"
	"github.com/sirupsen/logrus"
	apiErrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1"

	"github.com/sap/infrabox/src/services/garden/pkg/apis/garden/v1alpha1"
)

func CheckReadinessAndUpdateDHInfraObj(gardenCs gardenClientSet.Interface, dhInfra *v1alpha1.ShootCluster) (err error) {
	var shoot *v1beta1.Shoot
	shoot, err = gardenCs.GardenV1beta1().Shoots(dhInfra.Spec.GardenerNamespace).Get(dhInfra.Spec.ShootName, v1.GetOptions{})
	if err != nil {
		if !apiErrors.IsNotFound(err) {
			logrus.Errorf("couldn't get shoot information: %s", err)

		} else if dhInfra.Status.Status == v1alpha1.ShootClusterStateReady {
			dhInfra.Status.Status = v1alpha1.ShootClusterStateError
			dhInfra.Status.Message = "created cluster should exist, but gardener claimed that it is gone"
		}
		return
	}

	if isShootReady(shoot) && (dhInfra.Status.Status != v1alpha1.ShootClusterStateReady) {
		setStateToReady(dhInfra)
	}

	if isShootReady(shoot) && !isShootReconciling(shoot) {
		dhInfra.Status.NumNodes = numNodesInShoot(shoot)
	}

	return
}

// Counts the number of nodes in the shoot. Assumes that no node addition/removal is going on at the moment.
func numNodesInShoot(shoot *v1beta1.Shoot) int {
	cnt := 0
	for i := range shoot.Spec.Cloud.AWS.Workers {
		// the shoot state doesn't tell us about the exact number of nodes, only about the [min, max] range in the spec. We assume here that min == max
		cnt += shoot.Spec.Cloud.AWS.Workers[i].Worker.AutoScalerMin
	}

	return cnt
}

func setStateToReady(dhInfra *v1alpha1.ShootCluster) {
	dhInfra.Status.Status = v1alpha1.ShootClusterStateReady
	dhInfra.Status.Message = ""
}

func isShootReconciling(shoot *v1beta1.Shoot) bool {
	if shoot == nil {
		return false
	} else if shoot.Status.LastOperation == nil {
		logrus.Debugf("shoot %s isn't ready because no last operation is set", shoot.GetUID())
		return false
	}

	return (shoot.Status.LastOperation.Type == v1beta1.ShootLastOperationTypeReconcile) &&
		(shoot.Status.LastOperation.State != v1beta1.ShootLastOperationStateSucceeded) &&
		(shoot.Status.LastOperation.State != v1beta1.ShootLastOperationStateFailed) &&
		(shoot.Status.LastOperation.State != v1beta1.ShootLastOperationStateError) &&
		(shoot.Status.LastOperation.State != v1beta1.ShootLastOperationStatePending)
}

func isShootReady(shoot *v1beta1.Shoot) bool {
	if shoot == nil {
		return false
	} else if shoot.Status.LastOperation == nil {
		logrus.Debugf("shoot %s isn't ready because no last operation is set", shoot.GetUID())
		return false
	}

	/*
		readiness was defined by an email from Rafael Franzke
		"wenn in der lastOperation type=Create,state=Succeeded oder type=Reconcile steht, dann wurde das Cluster erfolgreich angelegt."
		translated:
			- IF the operation type is Create AND the state is succeeded THEN shoot is ready
			- IF the operation type is reconcile THEN shoot is ready
			- else: shoot isn't ready
	*/
	if shoot.Status.LastOperation.Type == v1beta1.ShootLastOperationTypeReconcile {
		return true
	}

	if (shoot.Status.LastOperation.Type == v1beta1.ShootLastOperationTypeCreate) && (shoot.Status.LastOperation.State == v1beta1.ShootLastOperationStateSucceeded) {
		return true
	}

	return false
}
