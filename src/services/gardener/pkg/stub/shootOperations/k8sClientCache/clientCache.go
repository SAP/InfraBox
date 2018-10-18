package k8sClientCache

import (
	"os"
	"sync"

	gardenClientSet "github.com/gardener/gardener/pkg/client/garden/clientset/versioned"
	"github.com/sirupsen/logrus"
	"k8s.io/client-go/kubernetes"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/utils"
)

type clientGetter struct {
	k8sClient       kubernetes.Interface
	gardenK8sClient gardenClientSet.Interface
}

func (cg *clientGetter) GetK8sClientSet() kubernetes.Interface         { return cg.k8sClient }
func (cg *clientGetter) GetGardenClientSet() gardenClientSet.Interface { return cg.gardenK8sClient }

func NewClientCache(cfgGetter KubecfgGetter) *ClientCache {
	return &ClientCache{kubecfgGetter: cfgGetter, cache: make(map[string]ClientGetter)}
}

type ClientCache struct {
	sync.Mutex
	kubecfgGetter KubecfgGetter
	cache         map[string]ClientGetter
}

func (cc *ClientCache) Get(shootCluster *v1alpha1.ShootCluster) ClientGetter {
	cc.Lock()
	defer cc.Unlock()

	hash := cc.hash(shootCluster)
	if cg, ok := cc.cache[hash]; ok {
		return cg
	}

	clientGetter := cc.createNewClientGetter(shootCluster)
	if clientGetter != nil {
        cc.cache[hash] = clientGetter
    }
	return clientGetter
}

func (cc *ClientCache) hash(shootCluster *v1alpha1.ShootCluster) string {
	return shootCluster.Status.ClusterName + shootCluster.Status.GardenerNamespace
}

func (cc *ClientCache) createNewClientGetter(shootCluster *v1alpha1.ShootCluster) ClientGetter {
	kubecfg, err := cc.kubecfgGetter.Get(shootCluster)
	if err != nil {
		logrus.Errorf("Couldn't get the kubeconfigs. err: %s", err)
		return nil
	}

	tmpfileRootdir := "/dev/shm" // try to store it on a ramdisk. /dev/shm is a ramdisk per default on linux >=  2.6.X
	if _, err := os.Stat(tmpfileRootdir); err == os.ErrNotExist {
		tmpfileRootdir = ""
	}

	cfg, err := utils.BuildK8sConfig(tmpfileRootdir, []byte(kubecfg))
	if err != nil {
		return nil
	}

	k8sClient, err := kubernetes.NewForConfig(cfg)
	if err != nil {
		logrus.Errorf("couldn't get k8sClient from config. err: %s", err)
		return nil
	}
	gardenCs, err := gardenClientSet.NewForConfig(cfg)
	if err != nil {
		logrus.Errorf("couldn't gardenClient from config. err: %s", err)
		return nil
	}

	return &clientGetter{gardenK8sClient: gardenCs, k8sClient: k8sClient}
}
