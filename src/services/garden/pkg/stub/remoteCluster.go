package stub

import (
	"fmt"

	"github.com/operator-framework/operator-sdk/pkg/sdk/types"
	"github.com/operator-framework/operator-sdk/pkg/util/k8sutil"
	"github.com/sirupsen/logrus"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/discovery"
	"k8s.io/client-go/discovery/cached"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

type RemoteClusterSDK struct {
	kubeConfig *rest.Config
	cluster    *RemoteCluster
	clientPool dynamic.ClientPool
	restMapper *discovery.DeferredDiscoveryRESTMapper
}

func (r *RemoteClusterSDK) Create(object types.Object, log *logrus.Entry) (err error) {
	_, namespace, err := k8sutil.GetNameAndNamespace(object)

	if err != nil {
		log.Errorf("Failed to get namespace: %v", err)
		return err
	}

	gvk := object.GetObjectKind().GroupVersionKind()
	apiVersion, kind := gvk.ToAPIVersionAndKind()

	resourceClient, _, err := r.getRemoteResourceClient(apiVersion, kind, namespace)
	if err != nil {
		return fmt.Errorf("failed to get resource client: %v", err)
	}

	unstructObj := k8sutil.UnstructuredFromRuntimeObject(object)
	unstructObj, err = resourceClient.Create(unstructObj)
	if err != nil {
		//log.Errorf("Failed to create object: %v", err)
		return err
	}

	// Update the arg object with the result
	err = k8sutil.UnstructuredIntoRuntimeObject(unstructObj, object)
	if err != nil {
		return fmt.Errorf("failed to unmarshal the retrieved data: %v", err)
	}

	return nil
}

func newRemoteClusterSDK(cluster *RemoteCluster, log *logrus.Entry) (*RemoteClusterSDK, error) {
	tlsClientConfig := rest.TLSClientConfig{}
	tlsClientConfig.CAData = []byte(cluster.MasterAuth.ClusterCaCertificate)
	tlsClientConfig.CertData = []byte(cluster.MasterAuth.ClientCertificate)
	tlsClientConfig.KeyData = []byte(cluster.MasterAuth.ClientKey)

	kubeConfig := &rest.Config{
		Host:            cluster.Endpoint,
		TLSClientConfig: tlsClientConfig,
		Username:        cluster.MasterAuth.Username,
		Password:        cluster.MasterAuth.Password,
	}

	kubeClient := kubernetes.NewForConfigOrDie(kubeConfig)

	cachedDiscoveryClient := cached.NewMemCacheClient(kubeClient.Discovery())
	restMapper := discovery.NewDeferredDiscoveryRESTMapper(cachedDiscoveryClient, meta.InterfacesForUnstructured)
	restMapper.Reset()
	kubeConfig.ContentConfig = dynamic.ContentConfig()
	clientPool := dynamic.NewClientPool(kubeConfig, restMapper, dynamic.LegacyAPIPathResolverFunc)

	return &RemoteClusterSDK{
		kubeConfig: kubeConfig,
		clientPool: clientPool,
		cluster:    cluster,
		restMapper: restMapper,
	}, nil
}

func apiResource(gvk schema.GroupVersionKind, restMapper *discovery.DeferredDiscoveryRESTMapper) (*v1.APIResource, error) {
	mapping, err := restMapper.RESTMapping(gvk.GroupKind(), gvk.Version)
	if err != nil {
		return nil, fmt.Errorf("failed to get the resource REST mapping for GroupVersionKind(%s): %v", gvk.String(), err)
	}
	resource := &v1.APIResource{
		Name:       mapping.Resource,
		Namespaced: mapping.Scope == meta.RESTScopeNamespace,
		Kind:       gvk.Kind,
	}
	return resource, nil
}

func (r *RemoteClusterSDK) getRemoteResourceClient(apiVersion, kind, namespace string) (dynamic.ResourceInterface, string, error) {
	gv, err := schema.ParseGroupVersion(apiVersion)
	if err != nil {
		return nil, "", fmt.Errorf("failed to parse apiVersion: %v", err)
	}

	gvk := schema.GroupVersionKind{
		Group:   gv.Group,
		Version: gv.Version,
		Kind:    kind,
	}

	client, err := r.clientPool.ClientForGroupVersionKind(gvk)
	if err != nil {
		return nil, "", fmt.Errorf("failed to get client for GroupVersionKind(%s): %v", gvk.String(), err)
	}
	resource, err := apiResource(gvk, r.restMapper)
	if err != nil {
		return nil, "", fmt.Errorf("failed to get resource type: %v", err)
	}
	pluralName := resource.Name
	resourceClient := client.Resource(resource, namespace)
	return resourceClient, pluralName, nil
}
