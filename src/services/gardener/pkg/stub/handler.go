package stub

import (
	"bytes"
	cryptoRand "crypto/rand"
	"crypto/tls"
	"crypto/x509"
	b64 "encoding/base64"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"mime/multipart"
	"net/http"
	"os"

	"github.com/operator-framework/operator-sdk/pkg/sdk/action"
	"github.com/operator-framework/operator-sdk/pkg/sdk/handler"
	"github.com/operator-framework/operator-sdk/pkg/sdk/query"
	"github.com/operator-framework/operator-sdk/pkg/sdk/types"
	"github.com/sirupsen/logrus"
	appsv1 "k8s.io/api/apps/v1"
	"k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/common"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/k8sClientCache"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/utils"
)

type MasterAuth struct {
	ClientCertificate    string
	ClientKey            string
	ClusterCaCertificate string
	Username             string
	Password             string
}

type RemoteCluster struct {
	Name       string
	Status     string
	Endpoint   string
	MasterAuth MasterAuth
}

func NewHandler(sdk common.SdkOperations) handler.Handler {
	initRand()

	k8sCCache := k8sClientCache.NewClientCache(k8sClientCache.NewSecretKubecfgGetter(sdk))
	shootOpFac := shootOperations.NewShootOperatorFactory(sdk, k8sCCache, utils.NewDefaultDynamicK8sK8sClientSetFactory())
	return &Handler{shootOpFac}
}

func initRand() {
	var seed int64
	binary.Read(cryptoRand.Reader, binary.LittleEndian, &seed)
	rand.Seed(seed)
}

type Handler struct {
	fac shootOperations.ShootOperatorFactory
}

func (h *Handler) Handle(ctx types.Context, event types.Event) error {
	switch o := event.Object.(type) {
	case *v1alpha1.ShootCluster:
		ns := o
		if event.Deleted {
			return nil
		}

		log := logrus.WithFields(logrus.Fields{
			"namespace": ns.Namespace,
			"name":      ns.Name,
		})

		delTimestamp := ns.GetDeletionTimestamp()
		if delTimestamp != nil {
			return h.delete(ns, log)
		} else {
			return h.sync(ns, log)
		}
	}
	return nil
}

func (h *Handler) sync(shootCluster *v1alpha1.ShootCluster, log *logrus.Entry) error {
	if len(shootCluster.Status.ClusterName) == 0 || len(shootCluster.Status.GardenerNamespace) == 0 {
		if err := h.ensureThatGardenerFieldsAreSet(shootCluster, log); err != nil {
			return err
		}
	}

	if err := h.ensureThatFinalizersAreSet(shootCluster, log); err != nil {
		return err
	}

	oldStatus := shootCluster.Status.Status
	oldMsg := shootCluster.Status.Message
	if err := h.fac.Get(log).Sync(shootCluster); err != nil {
		shootCluster.Status.Status = "error"
		shootCluster.Status.Message = err.Error()
		err = action.Update(shootCluster)
		return err
	}

	if shootCluster.Status.Status != oldStatus || shootCluster.Status.Message != oldMsg {
		if err := action.Update(shootCluster); err != nil {
			log.Error("failed to update cr after sync. err: ", err)
			return err
		}
	}

	if shootCluster.Status.Status == v1alpha1.ShootClusterStateShootReady {
		if err := h.injectCollectorsAndUpdateState(shootCluster, log); err != nil && !errors.IsResourceExpired(err) {
			return err
		}
	}

	return nil
}

const ENVGardenNamespace = "GARDENER_NAMESPACE"

func (h *Handler) ensureThatGardenerFieldsAreSet(shootCluster *v1alpha1.ShootCluster, log *logrus.Entry) error {
	if len(shootCluster.Status.ClusterName) == 0 {
		if err := h.createAndSetClustername(shootCluster, log); err != nil {
			log.Errorf("couldn't generate shootCluster name. err: %s", err.Error())
			return err
		}
	}

	if len(shootCluster.Status.GardenerNamespace) == 0 {
		if err := h.setGardenNamespace(shootCluster, log); err != nil {
			return err
		}
	}

	if err := action.Update(shootCluster); err != nil {
		log.Errorf("couldn't update shootCluster object. err: %s", err.Error())
		return err
	}

	return nil
}

func (h *Handler) setGardenNamespace(shootCluster *v1alpha1.ShootCluster, log *logrus.Entry) error {
	if val, exists := os.LookupEnv(ENVGardenNamespace); !exists {
		err := fmt.Errorf("env variable %s not set", ENVGardenNamespace)
		log.Error("couldn't set gardener namespace. err: ", err)
		return err

	} else if len(val) == 0 {
		err := fmt.Errorf("env variable %s must not be empty", ENVGardenNamespace)
		log.Error("couldn't set gardener namespace. err: ", err)
		return err

	} else {
		shootCluster.Status.GardenerNamespace = val
	}

	return nil
}

func (h *Handler) createAndSetClustername(cr *v1alpha1.ShootCluster, log *logrus.Entry) error {
	log.Debug("generating name for cluster...")
	var dhlist v1alpha1.ShootClusterList
	gvk := cr.GroupVersionKind()
	dhlist.SetGroupVersionKind(gvk)
	if err := query.List(cr.GetNamespace(), &dhlist); err != nil {
		log.Errorf("Failed to get list of existent clusters: %v", err)
		return err
	}
	cr.Status.ClusterName = utils.CreateUniqueClusterName(&dhlist)
	log.Debugf("cluster name will be %s", cr.Status.ClusterName)
	return nil
}

func (h *Handler) injectCollectorsAndUpdateState(shootCluster *v1alpha1.ShootCluster, log *logrus.Entry) error {
	// the shootCluster cr might have been updated -> get current version
	if err := query.Get(shootCluster); err != nil {
		log.Error("couldn't query shoot cr. err: ", err)
		return err
	}

	if err := h.tryToInjectCollectors(shootCluster, log); err != nil {
		log.Error("injecting collectors failed")
		return err
	}

	shootCluster.Status.Status = v1alpha1.ShootClusterStateReady
	if err := action.Update(shootCluster); err != nil {
		if !errors.IsResourceExpired(err) { // deletion might be triggered
			log.Error("failed to update cr during collector injection. err: ", err)
		}
		return err
	}

	return nil
}

func (h *Handler) ensureThatFinalizersAreSet(ns *v1alpha1.ShootCluster, log *logrus.Entry) error {
	finalizers := ns.GetFinalizers()
	if len(finalizers) == 0 {
		ns.SetFinalizers([]string{"gardener.service.infrabox.net"})
		//ns.Status.ClusterName = ns.Status.ClusterName
		err := action.Update(ns)
		if err != nil {
			log.Errorf("Failed to set finalizers: %v", err)
			return err
		}
	}

	return nil
}

func (h *Handler) tryToInjectCollectors(ns *v1alpha1.ShootCluster, log *logrus.Entry) error {
	cluster, err := h.getRemoteClusterFromSecret(ns, log)
	if err != nil {
		return err
	}

	if err = injectCollector(cluster, log); err != nil {
		log.Errorf("Failed to inject collector: %v", err)
		return err
	}

	return nil
}

func (h *Handler) getRemoteClusterFromSecret(ns *v1alpha1.ShootCluster, log *logrus.Entry) (*RemoteCluster, error) {
	s := utils.NewSecret(ns)
	if err := query.Get(s); err != nil {
		log.Errorf("couldn't get secret containing credentials. err: %s", err.Error())
		return nil, err
	}
	restCfg, err := utils.BuildK8sConfig("", s.Data[common.KeyNameOfShootKubecfgInSecret])
	if err != nil {
		log.Errorf("couldn't parse config from kubeconfig. err: %s", err.Error())
		return nil, err
	}
	cluster := &RemoteCluster{
		Status:   ns.Status.Status,
		Name:     ns.Status.ClusterName,
		Endpoint: restCfg.Host,
		MasterAuth: MasterAuth{
			Username:             restCfg.Username,
			Password:             restCfg.Password,
			ClusterCaCertificate: string(restCfg.CAData),
			ClientCertificate:    string(restCfg.CertData),
			ClientKey:            string(restCfg.KeyData),
		},
	}

	return cluster, nil
}

func (h *Handler) delete(sc *v1alpha1.ShootCluster, log *logrus.Entry) error {
	if len(sc.GetFinalizers()) == 0 { // work was finished in a previous run. We just got this cr again before it was deleted
		log.Debug("got a to-delete cr, but work was already done -> ignore")
		return nil
	}

	if sc.Status.Status == v1alpha1.ShootClusterStateShootReady {
		cluster, err := h.getRemoteClusterFromSecret(sc, log)
		if err != nil && !errors.IsNotFound(err) {
			log.Errorf("Failed to get Cluster: %v", err)
			return err
		}

		retrieveLogs(sc, cluster, log)
	}

	sc.Status.Status = v1alpha1.ShootClusterStateDeleting
	if err := action.Update(sc); err != nil {
		log.Errorf("couldn't update cluster state to %s. err: %s", sc.Status.Status, err)
		return err
	}

	return h.fac.Get(log).Delete(sc)
}

func doCollectorRequest(cluster *RemoteCluster, log *logrus.Entry, endpoint string) (*[]byte, error) {
	caCrt, _ := b64.StdEncoding.DecodeString(cluster.MasterAuth.ClusterCaCertificate)

	caCertPool := x509.NewCertPool()
	caCertPool.AppendCertsFromPEM(caCrt)

	tlsConfig := &tls.Config{
		RootCAs: caCertPool,
	}
	tlsConfig.BuildNameToCertificate()
	transport := &http.Transport{TLSClientConfig: tlsConfig}
	client := &http.Client{Transport: transport}

	req, err := http.NewRequest("GET", "https://"+cluster.Endpoint+"/api/v1/namespaces/infrabox-collector/services/infrabox-collector-api:80/proxy"+endpoint, nil)
	if err != nil {
		log.Errorf("Failed to create new request: %v", err)
		return nil, err
	}

	req.SetBasicAuth(cluster.MasterAuth.Username, cluster.MasterAuth.Password)

	resp, err := client.Do(req)
	if err != nil {
		log.Errorf("Failed to GET remote pod list: %v", err)
		return nil, err
	}

	bodyText, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Errorf("Failed to read response body: %v", err)
		return nil, err
	}

	return &bodyText, nil
}

func uploadToArchive(cr *v1alpha1.ShootCluster, log *logrus.Entry, data *[]byte, filename string) error {
	annotations := cr.GetAnnotations()
	root_url, _ := annotations["infrabox.net/root-url"]
	job_token, _ := annotations["infrabox.net/job-token"]

	body := new(bytes.Buffer)
	writer := multipart.NewWriter(body)
	part, err := writer.CreateFormFile(filename, filename)
	if err != nil {
		log.Warningf("Failed to create form file: %v", err)
		return err
	}

	part.Write(*data)
	err = writer.Close()
	if err != nil {
		log.Warningf("Failed to clise writer: %v", err)
		return err
	}

	req, err := http.NewRequest("POST", root_url+"/api/job/archive", body)

	if err != nil {
		log.Warningf("Failed to create request: %v", err)
		return err
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())
	req.Header.Set("Authorization", "token "+job_token)
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}
	client := &http.Client{Transport: tr}
	response, err := client.Do(req)

	if err != nil {
		log.Warningf("Failed to execute request: %v", err)
		return err
	}

	bodyText, err := ioutil.ReadAll(response.Body)
	log.Info(string(bodyText))

	return nil
}

type CollectedPod struct {
	NamespaceID string   `json:"namespace_id"`
	PodID       string   `json:"pod_id"`
	Pod         string   `json:"pod_name"`
	Containers  []string `json:"containers"`
	Namespace   string   `json:"namespace_name"`
}

// before deleting the cluster: retrieve the logs
func retrieveLogs(cr *v1alpha1.ShootCluster, cluster *RemoteCluster, log *logrus.Entry) {
	log.Info("Collecting data from remote cluster")

	annotations := cr.GetAnnotations()
	_, ok := annotations["infrabox.net/root-url"]
	if !ok {
		log.Warning("infrabox.net/root-url not set, not retrieving logs")
		return
	}

	_, ok = annotations["infrabox.net/job-id"]
	if !ok {
		log.Warning("infrabox.net/job-id not set, not retrieving logs")
		return
	}

	_, ok = annotations["infrabox.net/job-token"]
	if !ok {
		log.Warning("infrabox.net/job-token not set, not retrieving logs")
		return
	}

	var pods []CollectedPod
	data, err := doCollectorRequest(cluster, log, "/api/pods")

	if err != nil {
		log.Errorf("Failed to get collected pod list: %v", err)
		return
	}

	err = json.Unmarshal(*data, &pods)
	if err != nil {
		log.Errorf("Failed to collected pod list: %v", err)
		return
	}

	for _, pod := range pods {
		for _, container := range pod.Containers {
			log.Info("Collecting logs for pod: ", pod.PodID)
			data, err := doCollectorRequest(cluster, log, "/api/pods/"+pod.PodID+"/log/"+container)

			if err != nil {
				log.Warningf("Failed to get collected pod logs: %v", err)
				continue
			}

			filename := "pod_" + pod.Namespace + "_" + pod.Pod + "_" + container + ".log"
			err = uploadToArchive(cr, log, data, filename)
			if err != nil {
				log.Warningf("Failed to upload log to archive: %v", err)
				continue
			}
		}
	}
}

// after the cluster exists: deploy collectors
func injectCollector(cluster *RemoteCluster, log *logrus.Entry) error {
	client, err := newRemoteClusterSDK(cluster, log)

	if err != nil {
		log.Errorf("Failed to create remote cluster client: %v", err)
		return err
	}

	err = client.Create(newCollectorNamespace(), log)
	if err != nil && !errors.IsAlreadyExists(err) {
		log.Errorf("Failed to create collector deployment: %v", err)
		return err
	}

	err = client.Create(newCollectorCRB(), log)
	if err != nil && !errors.IsAlreadyExists(err) {
		log.Errorf("Failed to create collector crb: %v", err)
		return err
	}

	err = client.Create(newCollectorDeployment(), log)
	if err != nil && !errors.IsAlreadyExists(err) {
		log.Errorf("Failed to create collector deployment: %v", err)
		return err
	}

	err = client.Create(newCollectorService(), log)
	if err != nil && !errors.IsAlreadyExists(err) {
		log.Errorf("Failed to create collector service: %v", err)
		return err
	}

	err = client.Create(newFluentbitConfigMap(), log)
	if err != nil && !errors.IsAlreadyExists(err) {
		log.Errorf("Failed to create collector fluentbit config map: %v", err)
		return err
	}

	err = client.Create(newCollectorDaemonSet(), log)
	if err != nil && !errors.IsAlreadyExists(err) {
		log.Errorf("Failed to create collector daemon set: %v", err)
		return err
	}

	return nil
}

func newFluentbitConfigMap() *v1.ConfigMap{
	return &v1.ConfigMap{
		TypeMeta: metav1.TypeMeta{
			Kind:       "ConfigMap",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      "infrabox-fluent-bit",
			Namespace: "infrabox-collector",
		},
		Data: map[string]string {
			"parsers.conf": `
[PARSER]
    Name         docker_utf8
    Format       json
    Time_Key     time
    Time_Format  %Y-%m-%dT%H:%M:%S.%L
    Time_Keep    On
    Decode_Field_as escaped_utf8 log do_next
    Decode_Field_as escaped      log
`,
			"fluent-bit.conf": `
[SERVICE]
    Flush        2
    Daemon       Off
    Log_Level    info
    Parsers_File parsers.conf
[INPUT]
    Name             tail
    Path             /var/log/containers/*.log
    Parser           docker_utf8
    Tag              kube.*
    Refresh_Interval 2
    Mem_Buf_Limit    50MB
    Skip_Long_Lines  On
[FILTER]
    Name                kubernetes
    Match               kube.*
    Kube_URL            https://kubernetes.default.svc.cluster.local:443
    Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
[OUTPUT]
    Name  http
    Match *
    Host infrabox-collector-api.infrabox-collector
    Port 80
    URI /api/log
    Format json
`,
		},
	}
}

func newCollectorNamespace() *v1.Namespace {
	return &v1.Namespace{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Namespace",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name: "infrabox-collector",
		},
	}
}

func newCollectorCRB() *rbacv1.ClusterRoleBinding {
	return &rbacv1.ClusterRoleBinding{
		TypeMeta: metav1.TypeMeta{
			Kind:       "ClusterRoleBinding",
			APIVersion: "rbac.authorization.k8s.io/v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      "infrabox-collector-crb",
			Namespace: "infrabox-collector",
		},
		Subjects: []rbacv1.Subject{{
			Kind:      "ServiceAccount",
			Name:      "default",
			Namespace: "infrabox-collector",
		}},
		RoleRef: rbacv1.RoleRef{
			Kind:     "ClusterRole",
			Name:     "cluster-admin",
			APIGroup: "rbac.authorization.k8s.io",
		},
	}
}

func newCollectorService() *v1.Service {
	return &v1.Service{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Service",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      "infrabox-collector-api",
			Namespace: "infrabox-collector",
		},
		Spec: v1.ServiceSpec{
			Ports: []v1.ServicePort{{
				Name:       "http",
				Port:       80,
				TargetPort: intstr.FromInt(8080),
			}},
			Selector: map[string]string{
				"app": "api.collector.infrabox.net",
			},
		},
	}
}

func newCollectorDeployment() *appsv1.Deployment {
	var replicas int32 = 1
	return &appsv1.Deployment{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Deployment",
			APIVersion: "extensions/v1beta1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      "infrabox-collector-api",
			Namespace: "infrabox-collector",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{
					"app": "api.collector.infrabox.net",
				},
			},
			Template: v1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						"app": "api.collector.infrabox.net",
					},
				},
				Spec: v1.PodSpec{
					Containers: []v1.Container{{
						Name:  "api",
						Image: "quay.io/infrabox/collector-api",
					}},
				},
			},
		},
	}
}

func newCollectorDaemonSet() *appsv1.DaemonSet {
	return &appsv1.DaemonSet{
		TypeMeta: metav1.TypeMeta{
			Kind:       "DaemonSet",
			APIVersion: "extensions/v1beta1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      "infrabox-collector-fluent-bit",
			Namespace: "infrabox-collector",
		},
		Spec: appsv1.DaemonSetSpec{
			Template: v1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						"app": "fluentbit.collector.infrabox.net",
					},
				},
				Spec: v1.PodSpec{
					Containers: []v1.Container{{
						Name:  "fluent-bit",
						Image: "fluent/fluent-bit:0.13",
						Resources: v1.ResourceRequirements{
							Limits: v1.ResourceList{
								"memory": resource.MustParse("100Mi"),
							},
							Requests: v1.ResourceList{
								"cpu":    resource.MustParse("100m"),
								"memory": resource.MustParse("100Mi"),
							},
						},
						VolumeMounts: []v1.VolumeMount{{
							Name:      "varlog",
							MountPath: "/var/log",
						}, {
							Name:      "varlibdockercontainers",
							MountPath: "/var/lib/docker/containers",
							ReadOnly:  true,
						}, {
							Name:      "config",
							MountPath: "/fluent-bit/etc/parsers.conf",
							SubPath:   "parsers.conf",
						}, {
							Name:      "config",
							MountPath: "/fluent-bit/etc/fluent-bit.conf",
							SubPath:   "fluent-bit.conf",
						}},
					}},
					Volumes: []v1.Volume{{
						Name: "varlibdockercontainers",
						VolumeSource: v1.VolumeSource{
							HostPath: &v1.HostPathVolumeSource{
								Path: "/var/lib/docker/containers",
							},
						},
					}, {
						Name: "varlog",
						VolumeSource: v1.VolumeSource{
							HostPath: &v1.HostPathVolumeSource{
								Path: "/var/log",
							},
						},
					}, {
						Name: "config",
						VolumeSource: v1.VolumeSource{
							ConfigMap: &v1.ConfigMapVolumeSource{
								LocalObjectReference: v1.LocalObjectReference{
									Name: "infrabox-fluent-bit",
								},
							},
						},
					}},
				},
			},
		},
	}
}
