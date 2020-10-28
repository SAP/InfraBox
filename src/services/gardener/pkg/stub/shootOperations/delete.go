package shootOperations

import (
	"encoding/json"
	"errors"
	"time"

	jsonPatch "github.com/evanphx/json-patch"
	"github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	gardenV1beta1 "github.com/gardener/gardener/pkg/client/garden/clientset/versioned/typed/garden/v1beta1"
	"github.com/sirupsen/logrus"
	apiErrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
)

func deleteShootCluster(shoots gardenV1beta1.ShootInterface, shootCluster *v1alpha1.ShootCluster, log *logrus.Entry) {
	logSuccess := func() { log.Debugf("successfully triggered deletion of shoot %s", shootCluster.Status.ClusterName) }

	log.Debugf("Try to delete shoot %s in the namespace %s", shootCluster.Status.ClusterName, shootCluster.Status.GardenerNamespace)
	err := setDeletionConfirmation(shoots, shootCluster.Status.ClusterName, log)
	if err != nil {
		if apiErrors.IsNotFound(err) {
			log.Info("shoot cluster does not exist")
		} else {
			log.Errorf("Couldn't set deletion confirmation: %s", err.Error())
		}
		return
	}

	err = shoots.Delete(shootCluster.Status.ClusterName, &metav1.DeleteOptions{})
	if err != nil {
		if apiErrors.IsNotFound(err) {
			log.Info("shoot cluster does not exist")
		} else {
			log.Errorf("Couldn't tell gardener to delete shoot: %s", err.Error())
		}
		return
	}

	err = setDeletionTimestampConfirmation(shoots, shootCluster.Status.ClusterName)
	if err != nil {
		if apiErrors.IsNotFound(err) {
			log.Info("shoot cluster does not exist")
		} else {
			log.Errorf("Couldn't set deletion timestamp confirmation: %s", err.Error())
		}
		return
	}

	logSuccess()
}

func setDeletionConfirmation(shootInterface gardenV1beta1.ShootInterface, shootName string, log *logrus.Entry) error {
	shoot, err := shootInterface.Get(shootName, v1.GetOptions{})
	if err != nil {
		if !apiErrors.IsNotFound(err) {
			log.Errorf("couldn't delete shoot %s. err: %s", shootName, err)
		}
		return err
	}

	patch, err := createDeletionConfirmationJPatch(shoot)
	if err != nil {
		return errors.New("Couldn't create json patch: " + err.Error())
	}

	_, err = shootInterface.Patch(shoot.GetName(), types.MergePatchType, patch)
	if err != nil {
		return errors.New("Couldn't patch shoot: " + shootName + ", err: " + err.Error())
	}

	return nil
}

const confirmationAnnotationName = "confirmation.gardener.cloud/deletion"

func createDeletionConfirmationJPatch(shoot *v1beta1.Shoot) ([]byte, error) {
	if shoot == nil {
		return nil, errors.New("invalid shoot config given (nil)")
	}

	shootjson, err := json.Marshal(shoot)
	if err != nil {
		return nil, errors.New("Couldn't marshal old shoot: " + err.Error())
	}
	if shoot.GetAnnotations() == nil {
		shoot.Annotations = map[string]string{confirmationAnnotationName: "true"}
	} else {
		shoot.GetAnnotations()[confirmationAnnotationName] = "true"
	}
	tjson, err := json.Marshal(shoot)
	if err != nil {
		return nil, errors.New("Couldn't marshal new shoot: " + err.Error())
	}
	patch, err := jsonPatch.CreateMergePatch([]byte(shootjson), []byte(tjson))
	if err != nil {
		return nil, errors.New("Couldn't create shoot patch: " + err.Error())
	}

	return patch, nil
}

func setDeletionTimestampConfirmation(shootInterface gardenV1beta1.ShootInterface, shootName string) error {
	shoot, err := shootInterface.Get(shootName, v1.GetOptions{})
	if err != nil {
		return err
	}

	patch, err := createDeletionConfirmationTimestampPatch(shoot)
	if err != nil {
		return errors.New("Couldn't create patch: " + err.Error())
	}

	_, err = shootInterface.Patch(shoot.GetName(), types.MergePatchType, patch)
	if err != nil {
		return errors.New("Couldn't patch shoot: " + err.Error())
	}

	return nil
}

func createDeletionConfirmationTimestampPatch(shoot *v1beta1.Shoot) ([]byte, error) {
	if shoot == nil {
		return nil, errors.New("invalid shoot config given (nil)")
	}

	shootjson, err := json.Marshal(shoot)
	if err != nil {
		return nil, errors.New("Couldn't marshal old shoot: " + err.Error())
	}

	var deletionTimestamp string
	if tDeletion := shoot.GetObjectMeta().GetDeletionTimestamp(); tDeletion != nil {
		deletionTimestamp = tDeletion.Format(time.RFC3339) // kubernetes uses RFC3339 (https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.10/#objectmeta-v1-meta)
	}

	if shoot.GetAnnotations() == nil {
		shoot.Annotations = map[string]string{"confirmation.gardener.sapcloud.io/deletionTimestamp": deletionTimestamp}
	} else {
		shoot.GetAnnotations()["confirmation.gardener.sapcloud.io/deletionTimestamp"] = deletionTimestamp
	}

	tjson, err := json.Marshal(shoot)
	if err != nil {
		return nil, errors.New("Couldn't marshal new shoot: " + err.Error())
	}

	patch, err := jsonPatch.CreateMergePatch([]byte(shootjson), []byte(tjson))
	if err != nil {
		return nil, errors.New("Couldn't create shoot patch: " + err.Error())
	}
	return patch, nil
}
