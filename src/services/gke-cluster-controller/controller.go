package main

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"strconv"
	"time"

	b64 "encoding/base64"
	"github.com/golang/glog"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/apimachinery/pkg/util/wait"
	kubeinformers "k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/scheme"
	typedcorev1 "k8s.io/client-go/kubernetes/typed/core/v1"
	corelisters "k8s.io/client-go/listers/core/v1"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/tools/record"
	"k8s.io/client-go/util/workqueue"

	clusterv1alpha1 "github.com/infrabox/infrabox/src/services/gke-cluster-controller/pkg/apis/gkecontroller/v1alpha1"
	clientset "github.com/infrabox/infrabox/src/services/gke-cluster-controller/pkg/client/clientset/versioned"
	gkescheme "github.com/infrabox/infrabox/src/services/gke-cluster-controller/pkg/client/clientset/versioned/scheme"
	informers "github.com/infrabox/infrabox/src/services/gke-cluster-controller/pkg/client/informers/externalversions"
	listers "github.com/infrabox/infrabox/src/services/gke-cluster-controller/pkg/client/listers/gkecontroller/v1alpha1"
)

const controllerAgentName = "infrabox-infrabox/src/services/gke-cluster-controller"

type Controller struct {
	kubeclientset  kubernetes.Interface
	gkeclientset   clientset.Interface
	clusterLister  listers.ClusterLister
	clustersSynced cache.InformerSynced
	secretsLister  corelisters.SecretLister
	secretsSynced  cache.InformerSynced
	workqueue      workqueue.RateLimitingInterface
	recorder       record.EventRecorder
}

// NewController returns a new sample controller
func NewController(
	kubeclientset kubernetes.Interface,
	gkeclientset clientset.Interface,
	kubeInformerFactory kubeinformers.SharedInformerFactory,
	gkeInformerFactory informers.SharedInformerFactory) *Controller {

	clusterInformer := gkeInformerFactory.Gke().V1alpha1().Clusters()
	secretsInformer := kubeInformerFactory.Core().V1().Secrets()

	// Create event broadcaster
	// Add sample-controller types to the default Kubernetes Scheme so Events can be
	// logged for sample-controller types.
	gkescheme.AddToScheme(scheme.Scheme)
	glog.V(4).Info("Creating event broadcaster")
	eventBroadcaster := record.NewBroadcaster()
	eventBroadcaster.StartLogging(glog.Infof)
	eventBroadcaster.StartRecordingToSink(&typedcorev1.EventSinkImpl{Interface: kubeclientset.CoreV1().Events("")})
	recorder := eventBroadcaster.NewRecorder(scheme.Scheme, corev1.EventSource{Component: controllerAgentName})

	controller := &Controller{
		kubeclientset:  kubeclientset,
		gkeclientset:   gkeclientset,
		clusterLister:  clusterInformer.Lister(),
		clustersSynced: clusterInformer.Informer().HasSynced,
		secretsLister:  secretsInformer.Lister(),
		secretsSynced:  secretsInformer.Informer().HasSynced,
		workqueue:      workqueue.NewNamedRateLimitingQueue(workqueue.DefaultControllerRateLimiter(), "Clusters"),
		recorder:       recorder,
	}

	glog.Info("Setting up event handlers")

	clusterInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: controller.enqueueCluster,
		UpdateFunc: func(old, new interface{}) {
			controller.enqueueCluster(new)
		},
		DeleteFunc: func(old interface{}) {
			glog.Info("Waiting for informer caches to sync")
		},
	})

	return controller
}

func (c *Controller) Run(threadiness int, stopCh <-chan struct{}) error {
	defer runtime.HandleCrash()
	defer c.workqueue.ShutDown()

	glog.Info("Starting Cluster controller")

	glog.Info("Waiting for informer caches to sync")
	if ok := cache.WaitForCacheSync(stopCh, c.clustersSynced); !ok {
		return fmt.Errorf("failed to wait for caches to sync")
	}

	glog.Info("Starting workers")
	for i := 0; i < threadiness; i++ {
		go wait.Until(c.runWorker, time.Second, stopCh)
	}

	glog.Info("Started workers")
	<-stopCh
	glog.Info("Shutting down workers")

	return nil
}

func (c *Controller) runWorker() {
	for c.processNextWorkItem() {
	}
}

func (c *Controller) processNextWorkItem() bool {
	obj, shutdown := c.workqueue.Get()

	if shutdown {
		return false
	}

	err := func(obj interface{}) error {
		defer c.workqueue.Done(obj)
		var key string
		var ok bool

		if key, ok = obj.(string); !ok {
			c.workqueue.Forget(obj)
			runtime.HandleError(fmt.Errorf("expected string in workqueue but got %#v", obj))
			return nil
		}

		if err := c.syncHandler(key); err != nil {
			return fmt.Errorf("%s: error syncing: %s", key, err.Error())
		}

		c.workqueue.Forget(obj)
		return nil
	}(obj)

	if err != nil {
		runtime.HandleError(err)
		return true
	}

	return true
}

type MasterAuth struct {
	ClientCertificate    string
	ClientKey            string
	ClusterCaCertificate string
	Username             string
	Password             string
}

type GKECluster struct {
	Name       string
	Status     string
	Endpoint   string
	MasterAuth MasterAuth
}

func (c *Controller) updateClusterStatus(cluster *clusterv1alpha1.Cluster, gke *GKECluster) error {
	clusterCopy := cluster.DeepCopy()

	switch gke.Status {
	case "RUNNING":
		clusterCopy.Status.Infrabox.Status = "ready"
	case "PROVISIONING":
		clusterCopy.Status.Infrabox.Status = "pending"
	default:
		clusterCopy.Status.Infrabox.Status = "error"
	}

	clusterCopy.Status.Status = gke.Status

	_, err := c.gkeclientset.GkeV1alpha1().Clusters(cluster.Namespace).Update(clusterCopy)
	return err
}

func (c *Controller) getGKEClusters() ([]GKECluster, error) {
	cmd := exec.Command("gcloud", "container", "clusters", "list", "--format", "json")
	out, err := cmd.CombinedOutput()

	if err != nil {
		runtime.HandleError(fmt.Errorf("Could not list clusters"))
		return nil, err
	}

	var gkeclusters []GKECluster
	err = json.Unmarshal(out, &gkeclusters)

	if err != nil {
		runtime.HandleError(fmt.Errorf("Could not parse cluster list"))
		return nil, err
	}

	return gkeclusters, nil
}

func (c *Controller) getGKECluster(name string) (*GKECluster, error) {
	cmd := exec.Command("gcloud", "container", "clusters", "list",
		"--filter", "name=ib-"+name, "--format", "json")

	out, err := cmd.Output()

	if err != nil {
		runtime.HandleError(fmt.Errorf("Could not list clusters"))
		out, _ := cmd.CombinedOutput()
		glog.Warning(out)
		return nil, err
	}

	var gkeclusters []GKECluster
	err = json.Unmarshal(out, &gkeclusters)

	if err != nil {
		runtime.HandleError(fmt.Errorf("Could not parse cluster list"))
		out, _ := cmd.CombinedOutput()
		glog.Warning(out)
		return nil, err
	}

	if len(gkeclusters) == 0 {
		return nil, nil
	}

	return &gkeclusters[0], nil
}

func newSecret(cluster *clusterv1alpha1.Cluster, gke *GKECluster) *corev1.Secret {
	caCrt, _ := b64.StdEncoding.DecodeString(gke.MasterAuth.ClusterCaCertificate)
	clientKey, _ := b64.StdEncoding.DecodeString(gke.MasterAuth.ClientKey)
	clientCrt, _ := b64.StdEncoding.DecodeString(gke.MasterAuth.ClientCertificate)

	return &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      cluster.Spec.Infrabox.SecretName,
			Namespace: cluster.Namespace,
			OwnerReferences: []metav1.OwnerReference{
				*metav1.NewControllerRef(cluster, schema.GroupVersionKind{
					Group:   clusterv1alpha1.SchemeGroupVersion.Group,
					Version: clusterv1alpha1.SchemeGroupVersion.Version,
					Kind:    "Cluster",
				}),
			},
		},
		Type: "Opaque",
		Data: map[string][]byte{
			"ca.crt":     []byte(caCrt),
			"client.key": []byte(clientKey),
			"client.crt": []byte(clientCrt),
			"username":   []byte(gke.MasterAuth.Username),
			"password":   []byte(gke.MasterAuth.Password),
			"endpoint":   []byte("https://" + gke.Endpoint),
		},
	}
}

func (c *Controller) deleteSecret(cluster *clusterv1alpha1.Cluster) (bool, error) {
	secret, err := c.secretsLister.Secrets(cluster.Namespace).Get(cluster.Spec.Infrabox.SecretName)

	if err != nil {
		return errors.IsNotFound(err), err
	}

	if secret != nil {
		return true, nil
	}

	glog.Infof("%s/%s: Deleting secret for cluster credentials", cluster.Namespace, cluster.Name)
	err = c.kubeclientset.CoreV1().Secrets(cluster.Namespace).Delete(cluster.Spec.Infrabox.SecretName, metav1.NewDeleteOptions(0))

	if err != nil {
		runtime.HandleError(fmt.Errorf("%s/%s: Failed to delete secret", cluster.Namespace, cluster.Name))
		return false, err
	}

	return true, nil
}

func (c *Controller) createSecret(cluster *clusterv1alpha1.Cluster, gkecluster *GKECluster) error {
	secret, err := c.secretsLister.Secrets(cluster.Namespace).Get(cluster.Spec.Infrabox.SecretName)

	if err != nil {
		if !errors.IsNotFound(err) {
			return err
		}
	}

	if secret != nil {
		return nil
	}

	// Secret does not yet exist
	glog.Infof("%s/%s: Creating secret for cluster credentials", cluster.Namespace, cluster.Name)
	secret, err = c.kubeclientset.CoreV1().Secrets(cluster.Namespace).Create(newSecret(cluster, gkecluster))

	if err != nil {
		runtime.HandleError(fmt.Errorf("%s/%s: Failed to create secret: %s", cluster.Namespace, cluster.Name, err.Error()))
		return err
	}

	return nil
}

func (c *Controller) deleteGKECluster(cluster *clusterv1alpha1.Cluster) (bool, error) {
	glog.Infof("%s/%s: deleting gke cluster", cluster.Namespace, cluster.Name)
	gkecluster, err := c.getGKECluster(cluster.Name)
	if err != nil {
		runtime.HandleError(fmt.Errorf("%s/%s: Could not get GKE Cluster for", cluster.Namespace, cluster.Name))
		glog.Warning(err)
		return false, err
	}

	if gkecluster == nil {
		return true, nil
	}

	// Cluster still exists, delete it
	cmd := exec.Command("gcloud", "-q", "container", "clusters", "delete", "ib-"+cluster.Name, "--async")
	out, err := cmd.CombinedOutput()

	if err != nil {
		runtime.HandleError(fmt.Errorf("%s/%s: Failed to delete cluster", cluster.Namespace, cluster.Name))
		glog.Warning(string(out))
		return false, err
	}

	return false, nil
}

func (c *Controller) deleteCluster(cluster *clusterv1alpha1.Cluster) error {
	// Update status to pending
	if cluster.Status.Infrabox.Status != "pending" {
		cluster.Status.Infrabox.Status = "pending"
		cluster, err := c.gkeclientset.GkeV1alpha1().Clusters(cluster.Namespace).Update(cluster)

		if err != nil {
			runtime.HandleError(fmt.Errorf("%s/%s: Failed to update status", cluster.Namespace, cluster.Name))
			return err
		}
	}

	// Delete GKE Cluster
	deleted, err := c.deleteGKECluster(cluster)
	if err != nil {
		runtime.HandleError(fmt.Errorf("%s/%s: Failed to delete GKE cluster", cluster.Namespace, cluster.Name))
		return err
	}

	if !deleted {
		return nil
	}

	// Delete Secret
	deleted, err = c.deleteSecret(cluster)
	if err != nil {
		runtime.HandleError(fmt.Errorf("%s/%s: Failed to delete secret", cluster.Namespace, cluster.Name))
		return err
	}

	if !deleted {
		return nil
	}

	// Everything deleted, remove finalizers and delete cluster
	glog.Infof("%s/%s: removing finalizers", cluster.Namespace, cluster.Name)
	cluster.SetFinalizers([]string{})
	_, err = c.gkeclientset.GkeV1alpha1().Clusters(cluster.Namespace).Update(cluster)

	if err != nil {
		runtime.HandleError(fmt.Errorf("%s/%s: Failed to set finalizers", cluster.Namespace, cluster.Name))
		return err
	}

	glog.Infof("%s/%s: Finally deleting cluster", cluster.Namespace, cluster.Name)
	err = c.gkeclientset.GkeV1alpha1().Clusters(cluster.Namespace).Delete(cluster.Name, metav1.NewDeleteOptions(0))
	if err != nil {
		runtime.HandleError(fmt.Errorf("%s/%s: Failed to delete cluster", cluster.Namespace, cluster.Name))
		return err
	}

	return nil
}

func (c *Controller) syncHandler(key string) error {
	namespace, name, err := cache.SplitMetaNamespaceKey(key)
	if err != nil {
		runtime.HandleError(fmt.Errorf("invalid resource key: %s", key))
		return nil
	}

	cluster, err := c.clusterLister.Clusters(namespace).Get(name)

	if err != nil {
		if errors.IsNotFound(err) {
			runtime.HandleError(fmt.Errorf("%s: Cluster in work queue no longer exists", key))
			return nil
		}
		return err
	}

	if cluster.Status.Infrabox.Status == "error" {
		return nil
	}

	err = c.syncHandlerImpl(key, cluster.DeepCopy())

	if err != nil {
		cluster = cluster.DeepCopy()
		cluster.Status.Infrabox.Status = "error"
		cluster.Status.Infrabox.Message = err.Error()
		_, err := c.gkeclientset.GkeV1alpha1().Clusters(cluster.Namespace).Update(cluster)

		if err != nil {
			runtime.HandleError(fmt.Errorf("%s: Failed to update status", key))
			return err
		}
	}

	return nil
}

func (c *Controller) syncHandlerImpl(key string, cluster *clusterv1alpha1.Cluster) error {
	// Check wether we should delete the cluster
	delTimestamp := cluster.GetDeletionTimestamp()
	if delTimestamp != nil {
		return c.deleteCluster(cluster)
	}

	// Get the GKE Cluster
	gkecluster, err := c.getGKECluster(cluster.Name)
	if err != nil {
		runtime.HandleError(fmt.Errorf("%s: Could not get GKE Cluster", key))
		glog.Warning(err)
		return err
	}

	if gkecluster == nil {
		glog.Infof("%s: Cluster does not exist yet, creating one", key)

		// First set finalizers so we don't forget to delete it later on
		cluster.SetFinalizers([]string{"gkecontroller.infrabox.net"})
		cluster, err := c.gkeclientset.GkeV1alpha1().Clusters(cluster.Namespace).Update(cluster)

		if err != nil {
			runtime.HandleError(fmt.Errorf("%s: Failed to set finalizers", key))
			return err
		}

		name := "ib-" + cluster.Name
		args := []string{"container", "clusters",
			"create", name, "--async"}

		if cluster.Spec.DiskSize != 0 {
			args = append(args, "--disk-size")
			args = append(args, strconv.Itoa(cluster.Spec.DiskSize))
		}

		if cluster.Spec.MachineType != "" {
			args = append(args, "--machine-type")
			args = append(args, cluster.Spec.MachineType)
		}

		if cluster.Spec.EnableNetworkPolicy {
			args = append(args, "--enable-network-policy")
		}

		if cluster.Spec.NumNodes != 0 {
			args = append(args, "--num-nodes")
			args = append(args, strconv.Itoa(cluster.Spec.NumNodes))
		}

		if cluster.Spec.Preemptible {
			args = append(args, "--preemptible")
		}

		if cluster.Spec.EnableAutoscaling {
			args = append(args, "--enable-autoscaling")

			if cluster.Spec.MaxNodes != 0 {
				args = append(args, "--max-nodes")
				args = append(args, strconv.Itoa(cluster.Spec.MaxNodes))
			}

			if cluster.Spec.MinNodes != 0 {
				args = append(args, "--min-nodes")
				args = append(args, strconv.Itoa(cluster.Spec.MinNodes))
			}
		}

		cmd := exec.Command("gcloud", args...)
		out, err := cmd.CombinedOutput()

		if err != nil {
			runtime.HandleError(fmt.Errorf("%s: Failed to create gke cluster", key))
			glog.Error(string(out))
			return err
		}

		glog.Infof("%s: Cluster creation started", key)
		gkecluster, err := c.getGKECluster(cluster.Name)

		if err != nil {
			runtime.HandleError(fmt.Errorf("%s: Could not get GKE Cluster", key))
			return err
		}

		err = c.updateClusterStatus(cluster, gkecluster)

		if err != nil {
			runtime.HandleError(fmt.Errorf("%s: Failed to update status", key))
			return err
		}
	} else {
		err = c.createSecret(cluster, gkecluster)
		if err != nil {
			return err
		}

		if cluster.Status.Infrabox.Status == "pending" {
			if gkecluster.Status == "RUNNING" {
				glog.Infof("%s: Cluster is ready", key)
			}

			err = c.updateClusterStatus(cluster, gkecluster)

			if err != nil {
				runtime.HandleError(fmt.Errorf("%s: Failed to update status", key))
				return err
			}
		}
	}

	return nil
}

func (c *Controller) enqueueCluster(obj interface{}) {
	var key string
	var err error
	if key, err = cache.MetaNamespaceKeyFunc(obj); err != nil {
		runtime.HandleError(err)
		return
	}
	c.workqueue.AddRateLimited(key)
}
