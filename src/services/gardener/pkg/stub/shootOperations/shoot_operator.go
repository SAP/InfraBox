package shootOperations

import (
	"bytes"
	"fmt"
	"os"
	"time"

	"github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	gardenClientSet "github.com/gardener/gardener/pkg/client/garden/clientset/versioned"
	"github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	apiErrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/common"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/k8sClientCache"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/utils"
)

type Operator interface {
	Sync(shootCluster *v1alpha1.ShootCluster) error
	Delete(shootCluster *v1alpha1.ShootCluster) error
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

func (so *ShootOperator) Sync(shootCluster *v1alpha1.ShootCluster) error {
	defer func(tStart time.Time) { so.log.Debugf("synced with shoot within %s", time.Now().Sub(tStart)) }(time.Now())

	clients := so.clientCache.Get(shootCluster)
	if clients == nil {
		so.log.Error("couldn't get k8s clientsets")
		return fmt.Errorf("couldn't get k8s clientsets")
	}

	// try to install
	_, err := CreateShootCluster(so.operatorSdk, clients.GetGardenClientSet(), shootCluster, so.log)
	if err != nil && !apiErrors.IsAlreadyExists(err) {
		err = fmt.Errorf("failed to create deployment: %v", err)
		so.log.Error(err)
		return err
	}

	if len(shootCluster.Status.Status) == 0 {
		shootCluster.Status.Status = v1alpha1.ShootClusterStateCreating
		shootCluster.Status.Message = ""
	}

	if err = CheckReadinessAndUpdateShootClusterObj(clients.GetGardenClientSet(), shootCluster); err != nil {
		so.log.Errorf("couldn't check if cluster is ready. err : %s", err)
		return err
	}

	if shootCluster.Status.Status == v1alpha1.ShootClusterStateShootReady {
		// fetch kubecfg for shoot cluster
		shootCredsSecret, err := so.fetchKubeconfigFor(shootCluster, clients)
		if err != nil {
			shootCluster.Status.Status = v1alpha1.ShootClusterStateError
			return err
		}

		so.syncSecret(shootCluster, shootCredsSecret, clients)
	}

	err = so.updateShootIfNecessary(shootCluster, clients)
	return err
}

func (so *ShootOperator) syncSecret(shootCluster *v1alpha1.ShootCluster, shootCredsSecret *corev1.Secret, clientGetter k8sClientCache.ClientGetter) {
	secretWeWant := newSecretFromShootCredSecr(shootCluster, shootCredsSecret)

	secretWeHave, exists := so.secretExists(shootCluster)
	if exists {
		if err := so.updateSecretIfNecessary(secretWeWant, secretWeHave); err == nil {
			shootCluster.Status.SecretName = secretWeWant.GetName()

		} else if apiErrors.IsResourceExpired(err) { // probably the secret was updated in the meantime. no real error. just return
			so.log.Debugf("shoot-op: resource expired for secret (name: %s, ns: %s)", secretWeWant.GetName(), secretWeWant.GetNamespace())
			return
		} else {
			shootCluster.Status.Status = v1alpha1.ShootClusterStateError
			shootCluster.Status.Message = fmt.Sprintf("couldn't update secret. err: %v", err)
			return
		}
	} else {
		if err := so.operatorSdk.Create(secretWeWant); err == nil {
			shootCluster.Status.SecretName = secretWeWant.GetName()
		} else if apiErrors.IsResourceExpired(err) { // probably the secret was updated in the meantime.  no real error. just return
			so.log.Debugf("shoot-op: resource expired for new secret (name: %s, ns: %s)", secretWeWant.GetName(), secretWeWant.GetNamespace())
			return
		} else {
			so.log.Errorf("creating secret filled with gardener kubeconfig failed. err: %s", err)
			shootCluster.Status.Status = v1alpha1.ShootClusterStateError
			shootCluster.Status.Message = fmt.Sprintf("couldn't create secret. err: %v", err)
			return
		}
	}

	return
}

func (so *ShootOperator) fetchKubeconfigFor(shootCluster *v1alpha1.ShootCluster, clientGetter k8sClientCache.ClientGetter) (*corev1.Secret, error) {
	cfgPath := shootCluster.Status.ClusterName + ".kubeconfig"
	secret, err := clientGetter.GetK8sClientSet().CoreV1().Secrets(shootCluster.Status.GardenerNamespace).Get(cfgPath, v1.GetOptions{})
	if err != nil {
		so.log.Errorf("couldn't fetch the secret for cluster. err: %s", err.Error())
		return nil, err
	}

	if _, ok := secret.Data["kubeconfig"]; !ok {
		return nil, fmt.Errorf("Secret for '%s' does not have a kubeconfig", shootCluster.Status.ClusterName)
	} else {
		return secret, nil
	}
}

func (so *ShootOperator) updateSecretIfNecessary(want *corev1.Secret, have *corev1.Secret) error {
	var updateNecessary bool

	for k, v := range want.Data {
		if oldVal, exists := have.Data[k]; !exists || !bytes.Equal(oldVal, v) {
			have.Data[k] = v
			updateNecessary = true
		}
	}

	if !updateNecessary {
		return nil
	}

	if err := so.operatorSdk.Update(have); err != nil { // we are only interested in setting the 'config', rest can stay
		return err
	}
	return nil
}

func newSecretFromShootCredSecr(shootCluster *v1alpha1.ShootCluster, credSecr *corev1.Secret) *corev1.Secret {
	if shootCluster == nil {
		return nil
	}

	secret := utils.NewSecret(shootCluster)

	secret.Data[common.KeyNameOfShootKubecfgInSecret] = credSecr.Data["kubeconfig"]
	secret.Data[common.KeyNameOfShootKubecfgKeyInSecret] = credSecr.Data["kubecfg.key"]
	secret.Data[common.KeyNameOfShootCaCrtInSecret] = credSecr.Data["ca.crt"]
	secret.Data[common.KeyNameOfShootKubecfgCrtInSecret] = credSecr.Data["kubecfg.crt"]
	secret.Data[common.KeyNameOfShootUserInSecret] = credSecr.Data["username"]
	secret.Data[common.KeyNameOfShootPasswordInSecret] = credSecr.Data["password"]

	endpoint := extractEndpoint(credSecr)
	if endpoint == nil {
		return nil
	}

	secret.Data[common.KeyNameOfShootEndpointInSecret] = endpoint
	setShootClusterCrAsOwner(shootCluster, secret)
	return secret
}

func extractEndpoint(s *corev1.Secret) []byte {
	tmpfileRootdir := "/dev/shm" // try to store it on a ramdisk. /dev/shm is a ramdisk per default on linux >=  2.6.X
	if _, err := os.Stat(tmpfileRootdir); err == os.ErrNotExist {
		tmpfileRootdir = ""
	}

	cfg, err := utils.BuildK8sConfig(tmpfileRootdir, []byte(s.Data["kubeconfig"]))
	if err != nil {
		return nil
	}

	return []byte(cfg.Host)
}

func setShootClusterCrAsOwner(shootCluster *v1alpha1.ShootCluster, secret *corev1.Secret) {
	secret.OwnerReferences = []v1.OwnerReference{
		*v1.NewControllerRef(shootCluster, schema.GroupVersionKind{
			Group:   v1alpha1.SchemeGroupVersion.Group,
			Version: v1alpha1.SchemeGroupVersion.Version,
			Kind:    shootCluster.Kind,
		}),
	}
}

func newSecret(shootCluster *v1alpha1.ShootCluster, cfg []byte) *corev1.Secret {
	if shootCluster == nil {
		return nil
	}

	secret := utils.NewSecret(shootCluster)
	secret.Data[common.KeyNameOfShootKubecfgInSecret] = cfg
	return secret
}

func (so *ShootOperator) secretExists(shootCluster *v1alpha1.ShootCluster) (*corev1.Secret, bool) {
	secret := newSecret(shootCluster, nil)
	if err := so.operatorSdk.Get(secret); apiErrors.IsNotFound(err) {
		return nil, false
	} else if err != nil {
		logrus.Errorf("couldn't check secret: %s", err)
		return nil, false
	}

	return secret, true
}

func (so *ShootOperator) updateShootIfNecessary(shootCluster *v1alpha1.ShootCluster, clientGetter k8sClientCache.ClientGetter) error {
	shoot, err := clientGetter.GetGardenClientSet().GardenV1beta1().Shoots(shootCluster.Status.GardenerNamespace).Get(shootCluster.Status.ClusterName, v1.GetOptions{})
	if err != nil {
		so.log.Errorf("couldn't get current status of shoot cluster. err: %s", err)
		return err
	}

	if so.updateShootSpecIfNecessary(shoot, shootCluster) {
		so.log.Info("specifications have changed, will update shoot...")
		if _, err := clientGetter.GetGardenClientSet().GardenV1beta1().Shoots(shootCluster.Status.GardenerNamespace).Update(shoot); err != nil {
			so.log.Errorf("couldn't update shoot with new specs. err: ", err)
			return err
		}
	}

	return nil
}

func (so *ShootOperator) updateShootSpecIfNecessary(shoot *v1beta1.Shoot, shootCluster *v1alpha1.ShootCluster) bool {
	needsUpdate := false
	if len(shoot.Spec.Cloud.AWS.Workers) != 0 {
		worker := &shoot.Spec.Cloud.AWS.Workers[0]
		if worker.AutoScalerMin != int(shootCluster.Spec.MinNodes) {
			needsUpdate = true
			worker.AutoScalerMin = int(shootCluster.Spec.MinNodes)
		}

		if worker.AutoScalerMax != int(shootCluster.Spec.MaxNodes) {
			needsUpdate = true
			worker.AutoScalerMax = int(shootCluster.Spec.MaxNodes)
		}

		if expVolSize := fmt.Sprintf("%dGi", shootCluster.Spec.DiskSize); worker.VolumeSize != expVolSize {
			needsUpdate = true
			worker.VolumeSize = expVolSize
		}
	}

	return needsUpdate
}

func (so *ShootOperator) Delete(shootCluster *v1alpha1.ShootCluster) error {
	clientGetter := so.clientCache.Get(shootCluster)
	if clientGetter == nil {
		so.log.Error("couldn't get k8s clientsets. Aborting deletion...")
		return fmt.Errorf("couldn't get k8s clientsets")
	}

	deleteShootCluster(clientGetter.GetGardenClientSet().GardenV1beta1().Shoots(shootCluster.Status.GardenerNamespace), shootCluster, so.log)

	shootCluster.SetFinalizers([]string{})
	if err := so.operatorSdk.Update(shootCluster); err != nil {
		so.log.Errorf("Could not update shootCluster object (removing finalizers). err: %s", err)
		return err
	} else {
		so.log.Debugf("successfully deleted shootCluster %s", shootCluster.GetName())
	}

	return nil
}

func CreateShootCluster(sdkops common.SdkOperations, gardenCs gardenClientSet.Interface, shootCluster *v1alpha1.ShootCluster, log *logrus.Entry) (*v1beta1.Shoot, error) {
	tstart := time.Now()

	shootcfg, err := createAwsConfig(sdkops, shootCluster, gardenCs.GardenV1beta1().CloudProfiles())
	if err != nil {
		log.Errorf("couldn't create a valid config. err: %s", err)
		return nil, err
	}

	shoot, err := gardenCs.GardenV1beta1().Shoots(shootCluster.Status.GardenerNamespace).Create(shootcfg)
	if err != nil {
		if !apiErrors.IsAlreadyExists(err) {
			log.Errorf("gardener didn't create the shoot. err: %s", err)
		}
		return shoot, err
	}

	log.Infof("successfully created new shoot %s in namespace %s within %s", shoot.GetName(), shoot.GetNamespace(), time.Now().Sub(tstart).String())
	return shoot, nil
}
