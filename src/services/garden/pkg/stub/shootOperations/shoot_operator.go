package shootOperations

import (
	"bytes"
	"fmt"
	"time"

	"github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	gardenClientSet "github.com/gardener/gardener/pkg/client/garden/clientset/versioned"
	"github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	apiErrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1"

	"github.com/sap/infrabox/src/services/garden/pkg/apis/garden/v1alpha1"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/common"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/k8sClientCache"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/utils"
)

type Operator interface {
	Sync(dhinfrastructure *v1alpha1.ShootCluster) error
	Delete(dhinfrastructure *v1alpha1.ShootCluster) error
}

func NewShootOperator(sdkops common.SdkOperations, cache k8sClientCache.ClientCacher, csFactory utils.K8sClientSetCreator, log *logrus.Entry) *ShootOperator {
	return &ShootOperator{
		operatorSdk: sdkops,
		log:         log,
		clientCache: cache,
		csFactory:   csFactory,
	}
}

type ShootOperator struct {
	operatorSdk common.SdkOperations
	log         *logrus.Entry
	clientCache k8sClientCache.ClientCacher
	csFactory   utils.K8sClientSetCreator
}

func (so *ShootOperator) Sync(dhInfra *v1alpha1.ShootCluster) error {
	defer func(tStart time.Time) { so.log.Infof("synced with shoot within %s", time.Now().Sub(tStart)) }(time.Now())

	clients := so.clientCache.Get(dhInfra)
	if clients == nil {
		so.log.Error("couldn't get k8s clientsets")
		return fmt.Errorf("couldn't get k8s clientsets")
	}

	// try to install
	_, err := CreateShootCluster(so.operatorSdk, clients.GetGardenClientSet(), dhInfra, so.log)
	if err != nil && !apiErrors.IsAlreadyExists(err) {
		err = fmt.Errorf("failed to create deployment: %v", err)
		so.log.Error(err)
		return err
	}

	// shoot creation was triggered or is completed
	if err := so.setFinalizerIfNotPresent(dhInfra); err != nil {
		return err
	}

	if len(dhInfra.Status.Status) == 0 {
		dhInfra.Status.Status = v1alpha1.ShootClusterStateCreating
		dhInfra.Status.Message = ""
	}

	if err = CheckReadinessAndUpdateDHInfraObj(clients.GetGardenClientSet(), dhInfra); err != nil {
		so.log.Errorf("couldn't check if cluster is ready. err : %s", err)
		return err
	}

	if dhInfra.Status.Status == v1alpha1.ShootClusterStateReady {
		// fetch kubecfg for shoot cluster
		shootCredsSecret, err := so.fetchKubeconfigFor(dhInfra, clients)
		if err != nil {
			dhInfra.Status.Status = v1alpha1.ShootClusterStateError
			return err
		}

		so.syncSecret(dhInfra, shootCredsSecret, clients)
	}

	err = so.updateShootIfNecessary(dhInfra, clients)
	return err
}

func (so *ShootOperator) setFinalizerIfNotPresent(dhInfra *v1alpha1.ShootCluster) error {
	if len(dhInfra.GetFinalizers()) == 0 {
		dhInfra.SetFinalizers([]string{"datahub.sap.com"})
		if err := so.operatorSdk.Update(dhInfra); err != nil {
			so.log.Error("Failed to set finalizers")
			return err
		}
	}
	return nil
}

//func (so *ShootOperator) syncSecret(dhInfra *v1alpha1.ShootCluster, shootKubeCfg []byte, clientGetter k8sClientCache.ClientGetter) {
func (so *ShootOperator) syncSecret(dhInfra *v1alpha1.ShootCluster, shootCredsSecret *corev1.Secret, clientGetter k8sClientCache.ClientGetter) {
	secretWeWant := newSecretFromShootCredSecr(dhInfra, shootCredsSecret)

	secretWeHave, exists := so.secretExists(dhInfra)
	if exists {
		if err := so.updateSecretIfNecessary(secretWeWant, secretWeHave); err == nil {
			dhInfra.Status.SecretName = secretWeWant.GetName()

		} else if apiErrors.IsResourceExpired(err) { // probably the secret was updated in the meantime. no real error. just return
			so.log.Debugf("shoot-op: resource expired for secret (name: %s, ns: %s)", secretWeWant.GetName(), secretWeWant.GetNamespace())
			return
		} else {
			dhInfra.Status.Status = v1alpha1.ShootClusterStateError
			dhInfra.Status.Message = fmt.Sprintf("couldn't update secret. err: %v", err)
			return
		}
	} else {
		if err := so.operatorSdk.Create(secretWeWant); err == nil {
			dhInfra.Status.SecretName = secretWeWant.GetName()
		} else if apiErrors.IsResourceExpired(err) { // probably the secret was updated in the meantime.  no real error. just return
			so.log.Debugf("shoot-op: resource expired for new secret (name: %s, ns: %s)", secretWeWant.GetName(), secretWeWant.GetNamespace())
			return
		} else {
			so.log.Errorf("creating secret filled with gardener kubeconfig failed. err: %s", err)
			dhInfra.Status.Status = v1alpha1.ShootClusterStateError
			dhInfra.Status.Message = fmt.Sprintf("couldn't create secret. err: %v", err)
			return
		}
	}

	return
}

func (so *ShootOperator) fetchKubeconfigFor(dhInfra *v1alpha1.ShootCluster, clientGetter k8sClientCache.ClientGetter) (*corev1.Secret, error) {
	cfgPath := dhInfra.Spec.ShootName + ".kubeconfig"
	secret, err := clientGetter.GetK8sClientSet().CoreV1().Secrets(dhInfra.Spec.GardenerNamespace).Get(cfgPath, v1.GetOptions{})
	if err != nil {
		so.log.Errorf("couldn't fetch the secret for cluster. err: %s", err.Error())
		return nil, err
	}

	if _, ok := secret.Data["kubeconfig"]; !ok {
		return nil, fmt.Errorf("Secret for '%s' does not have a kubeconfig", dhInfra.Spec.ShootName)
	} else {
		return secret, nil
	}
}

func (so *ShootOperator) updateSecretIfNecessary(want *corev1.Secret, have *corev1.Secret) error {
	var updateNecessary bool

	for k, v := range want.Data {
		if oldVal, exists := have.Data[k]; !exists  || !bytes.Equal(oldVal, v) {
			have.Data[k] = v
			updateNecessary = true
		}
	}

	//shootKubecfg, exists := have.Data["config"]
	//if !exists {
	//	updateNecessary = true
	//} else if !bytes.Equal(want.Data["config"], shootKubecfg) {
	//	updateNecessary = true
	//}


	if !updateNecessary {
		return nil
	}

	//have.Data["config"] = want.Data["config"]
	//have.Data[common.KeyNameOfK8sStorageClassInSecret] = want.Data[common.KeyNameOfK8sStorageClassInSecret]
	if err := so.operatorSdk.Update(have); err != nil { // we are only interested in setting the 'config', rest can stay
		return err
	}
	return nil
}

func newSecretFromShootCredSecr(dhInfra *v1alpha1.ShootCluster, credSecr *corev1.Secret) *corev1.Secret {
	if dhInfra == nil {
		return nil
	}

	secret := utils.NewSecret(dhInfra)
	secret.Data[common.KeyNameOfShootKubecfgInSecret] = credSecr.Data["kubeconfig"]
	secret.Data[common.KeyNameOfShootKubecfgKeyInSecret] = credSecr.Data["kubecfg.key"]
	secret.Data[common.KeyNameOfShootCaCrtInSecret] = credSecr.Data["ca.crt"]
	secret.Data[common.KeyNameOfShootKubecfgCrtInSecret] = credSecr.Data["kubecfg.crt"]
	secret.Data[common.KeyNameOfShootUserInSecret] = credSecr.Data["username"]
	secret.Data[common.KeyNameOfShootPasswordInSecret] = credSecr.Data["password"]

	return secret
}

func newSecret(dhInfra *v1alpha1.ShootCluster, cfg []byte) *corev1.Secret {
	if dhInfra == nil {
		return nil
	}

	secret := utils.NewSecret(dhInfra)
	secret.Data[common.KeyNameOfShootKubecfgInSecret] = cfg
	secret.Data[common.KeyNameOfK8sStorageClassInSecret] = []byte(common.NameOfDefaultStorageClass)
	return secret
}

func (so *ShootOperator) secretExists(dhInfra *v1alpha1.ShootCluster) (*corev1.Secret, bool) {
	secret := newSecret(dhInfra, nil)
	if err := so.operatorSdk.Get(secret); apiErrors.IsNotFound(err) {
		return nil, false
	} else if err != nil {
		logrus.Errorf("couldn't check secret: %s", err)
		return nil, false
	}

	return secret, true
}

func (so *ShootOperator) updateShootIfNecessary(dhInfra *v1alpha1.ShootCluster, clientGetter k8sClientCache.ClientGetter) error {
	shoot, err := clientGetter.GetGardenClientSet().GardenV1beta1().Shoots(dhInfra.Spec.GardenerNamespace).Get(dhInfra.Spec.ShootName, v1.GetOptions{})
	if err != nil {
		so.log.Errorf("couldn't get current status of shoot cluster. err: %s", err)
		return err
	}

	if so.updateShootSpecIfNecessary(shoot, dhInfra) {
		so.log.Info("specifications have changed, will update shoot...")
		if _, err := clientGetter.GetGardenClientSet().GardenV1beta1().Shoots(dhInfra.Spec.GardenerNamespace).Update(shoot); err != nil {
			so.log.Errorf("couldn't update shoot with new specs. err: ", err)
			return err
		}
	}

	return nil
}

func (so *ShootOperator) updateShootSpecIfNecessary(shoot *v1beta1.Shoot, dhInfra *v1alpha1.ShootCluster) bool {
	needsUpdate := false
	if len(shoot.Spec.Cloud.AWS.Workers) != 0 {
		worker := &shoot.Spec.Cloud.AWS.Workers[0]
		if worker.AutoScalerMin != int(dhInfra.Spec.MinNodes) {
			needsUpdate = true
			worker.AutoScalerMin = int(dhInfra.Spec.MinNodes)
		}

		if worker.AutoScalerMax != int(dhInfra.Spec.MaxNodes) {
			needsUpdate = true
			worker.AutoScalerMax = int(dhInfra.Spec.MaxNodes)
		}

		if expVolSize := fmt.Sprintf("%dGi", dhInfra.Spec.DiskSize); worker.VolumeSize != expVolSize {
			needsUpdate = true
			worker.VolumeSize = expVolSize
		}
	}

	return needsUpdate
}

func (so *ShootOperator) Delete(dhInfra *v1alpha1.ShootCluster) error {
	clientGetter := so.clientCache.Get(dhInfra)
	if clientGetter == nil {
		so.log.Error("couldn't get k8s clientsets. Aborting deletion...")
		return fmt.Errorf("couldn't get k8s clientsets")
	}

	deleteShootCluster(clientGetter.GetGardenClientSet().GardenV1beta1().Shoots(dhInfra.Spec.GardenerNamespace), dhInfra, so.log)
	if err := so.deleteSecret(dhInfra); err != nil {
		return err
	}

	dhInfra.SetFinalizers([]string{})
	if err := so.operatorSdk.Update(dhInfra); err != nil {
		so.log.Errorf("Could not update dhinfrastructure object (removing finalizers). err: %s", err)
		return err
	} else {
		so.log.Infof("successfully deleted dhinfrastructure %s", dhInfra.GetName())
	}

	return nil
}

func (so *ShootOperator) deleteSecret(dhInfra *v1alpha1.ShootCluster) error {
	secret := newSecret(dhInfra, nil)

	err := so.operatorSdk.Delete(secret)
	if err != nil {
		if !apiErrors.IsNotFound(err) {
			so.log.Error("couldn't delete secret: ", err.Error())
			return err
		}
	}

	so.log.Info("successfully deleted secret")
	return nil
}

func CreateShootCluster(sdkops common.SdkOperations, gardenCs gardenClientSet.Interface, dhInfra *v1alpha1.ShootCluster, log *logrus.Entry) (*v1beta1.Shoot, error) {
	tstart := time.Now()

	shootcfg, err := createAwsConfig(sdkops, dhInfra, gardenCs.GardenV1beta1().CloudProfiles())
	if err != nil {
		log.Errorf("couldn't create a valid config. err: %s", err)
		return nil, err
	}

	shoot, err := gardenCs.GardenV1beta1().Shoots(dhInfra.Spec.GardenerNamespace).Create(shootcfg)
	if err != nil {
		if !apiErrors.IsAlreadyExists(err) {
			log.Errorf("gardener didn't create the shoot. err: %s", err)
		}
		return shoot, err
	}

	log.Infof("successfully created new shoot %s in namespace %s within %s", shoot.GetName(), shoot.GetNamespace(), time.Now().Sub(tstart).String())
	return shoot, nil
}
