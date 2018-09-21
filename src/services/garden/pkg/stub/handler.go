package stub

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	b64 "encoding/base64"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"mime/multipart"
	"net/http"
	"os/exec"
	"strconv"
	"strings"

	"github.com/operator-framework/operator-sdk/pkg/sdk/query"
	"github.com/sap/infrabox/src/services/garden/pkg/apis/garden/v1alpha1"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/common"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/k8sClientCache"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/utils"
	"github.com/satori/go.uuid"

	"github.com/operator-framework/operator-sdk/pkg/sdk/action"
	"github.com/operator-framework/operator-sdk/pkg/sdk/handler"
	"github.com/operator-framework/operator-sdk/pkg/sdk/types"
	"github.com/sirupsen/logrus"
	appsv1 "k8s.io/api/apps/v1"
	"k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/util/intstr"
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
	k8sCCache := k8sClientCache.NewClientCache(k8sClientCache.NewSecretKubecfgGetter(sdk))
	shootOpFac := shootOperations.NewShootOperatorFactory(sdk, k8sCCache, utils.NewDefaultDynamicK8sK8sClientSetFactory())
	return &Handler{shootOpFac}
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

func (h *Handler) sync(ns *v1alpha1.ShootCluster, log *logrus.Entry) error {
    if err := h.ensureThatFinalizersAreSet(ns, log); err != nil {
        return err
    }

    oldStatus := ns.Status.Status
    oldMsg := ns.Status.Message
    err := h.fac.Get(log).Sync(ns)
    //status, err := syncGardenCluster(ns, log)
    if err != nil {
        ns.Status.Status = "error"
        ns.Status.Message = err.Error()
        err = action.Update(ns)
        return err
    } else {
        if ns.Status.Status != oldStatus || ns.Status.Message != oldMsg {
            err = action.Update(ns)
            return err
        }
    }

    // if cluster is ready -> injectCollector
    if ns.Status.Status == v1alpha1.ShootClusterStateReady {
        if err := h.tryToInjectCollectors(ns, log, ); err != nil {
            log.Error("injecting collectors failed")
            return err
        }
        // TODO: only become ready if injectors are ready
    }

    return nil
}

func (h *Handler) ensureThatFinalizersAreSet(ns *v1alpha1.ShootCluster, log *logrus.Entry) error {
    finalizers := ns.GetFinalizers()
    if len(finalizers) == 0 {
        ns.SetFinalizers([]string{"garden.service.infrabox.net"})
        ns.Status.Status = "pending" // TODO: use status from set of valid ones

        ns.Status.ClusterName = ns.Spec.ShootName
        err := action.Update(ns)
        if err != nil {
            log.Errorf("Failed to set finalizers: %v", err)
            return err
        }
    }

    return nil
}

func (h *Handler) tryToInjectCollectors(ns *v1alpha1.ShootCluster, log *logrus.Entry) error {
    s := utils.NewSecret(ns)
    if err := query.Get(s); err != nil {
        log.Errorf("couldn't get secret containing credentials. err: %s", err.Error())
        return err
    }

    restCfg, err := utils.BuildK8sConfig("", s.Data[common.KeyNameOfShootKubecfgInSecret])
    if err != nil {
        log.Errorf("couldn't parse config from kubeconfig. err: %s", err.Error())
        return err
    }

    cluster := &RemoteCluster{
        Status:   ns.Status.Status,
        Name:     ns.Spec.ShootName,
        Endpoint: restCfg.Host,
        MasterAuth: MasterAuth{
            Username:             restCfg.Username,
            Password:             restCfg.Password,
            ClusterCaCertificate: string(restCfg.CAData),
            ClientCertificate:    string(restCfg.CertData),
            ClientKey:            string(restCfg.KeyData),
        },
    }

    if err = injectCollector(cluster, log); err != nil {
        log.Errorf("Failed to inject collector: %v", err)
        return err
    }

    return nil
}

func (h *Handler) delete(sc *v1alpha1.ShootCluster, log *logrus.Entry) error {

	// 1) retrieve logs (only if not in state DELETING)

	if sc.Status.Status == v1alpha1.ShootClusterStateReady {
        gkecluster, err := getRemoteCluster(sc.Status.ClusterName, log)
        if err != nil && !errors.IsNotFound(err) {
            log.Errorf("Failed to get GKE Cluster: %v", err)
            return err
        }
        retrieveLogs(sc, gkecluster, log)
    }

	sc.Status.Status = v1alpha1.ShootClusterStateDeleting
	if err := action.Update(sc); err != nil {
	    return err
    }

	// 2) switch to state "deleting"
	// 3) trigger deletion
	return h.fac.Get(log).Delete(sc)
}

func syncGardenCluster(cr *v1alpha1.ShootCluster, log *logrus.Entry) (*v1alpha1.ShootClusterStatus, error) {
	if cr.Status.Status == "ready" || cr.Status.Status == "error" {
		return &cr.Status, nil
	}

	finalizers := cr.GetFinalizers()
	if len(finalizers) == 0 {
		cr.SetFinalizers([]string{"gcp.service.infrabox.net"})
		cr.Status.Status = "pending"
		u := uuid.NewV4()

		cr.Status.ClusterName = "ib-" + u.String()
		err := action.Update(cr)
		if err != nil {
			log.Errorf("Failed to set finalizers: %v", err)
			return nil, err
		}
	}

	// Get the GKE Cluster
	gkecluster, err := getRemoteCluster(cr.Status.ClusterName, log)
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Could not get GKE Cluster: %v", err)
		return nil, err
	}

	if gkecluster == nil {
		args := []string{"container", "clusters",
			"create", cr.Status.ClusterName,
			"--async",
			"--enable-autorepair",
			"--scopes=gke-default,storage-rw",
			"--zone", cr.Spec.Zone,
		}

		if cr.Spec.DiskSize != 0 {
			args = append(args, "--disk-size")
			args = append(args, strconv.Itoa(int(cr.Spec.DiskSize)))
		}

		if cr.Spec.MachineType != "" {
			args = append(args, "--machine-type")
			args = append(args, cr.Spec.MachineType)
		}

		if cr.Spec.EnableNetworkPolicy {
			args = append(args, "--enable-network-policy")
		}

		if cr.Spec.NumNodes != 0 {
			args = append(args, "--num-nodes")
			args = append(args, strconv.Itoa(int(cr.Spec.NumNodes)))
		}

		if cr.Spec.Preemptible {
			args = append(args, "--preemptible")
		}

		if cr.Spec.EnableAutoscaling {
			args = append(args, "--enable-autoscaling")

			if cr.Spec.MaxNodes != 0 {
				args = append(args, "--max-nodes")
				args = append(args, strconv.Itoa(int(cr.Spec.MaxNodes)))
			}

			if cr.Spec.MinNodes != 0 {
				args = append(args, "--min-nodes")
				args = append(args, strconv.Itoa(int(cr.Spec.MinNodes)))
			}
		}

		if cr.Spec.ClusterVersion != "" {
			// find out the exact cluster version
			version, err := getExactClusterVersion(cr, log)

			if err != nil {
				return nil, err
			}

			args = append(args, "--cluster-version", version)
		}

		cmd := exec.Command("gcloud", args...)
		out, err := cmd.CombinedOutput()

		if err != nil {
			log.Errorf("Failed to create GKE Cluster: %v", err)
			log.Error(string(out))
			return nil, err
		}

		status := cr.Status
		status.Status = "pending"
		status.Message = "Cluster is being created"
		return &status, nil
	} else {
		if err != nil {
			log.Errorf("Failed to create secret: %v", err)
			return nil, err
		}

		if gkecluster.Status == "RUNNING" {
			err = injectCollector(gkecluster, log)
			if err != nil {
				log.Errorf("Failed to inject collector: %v", err)
				return nil, err
			}

			err = action.Create(newSecret(cr, gkecluster))
			if err != nil && !errors.IsAlreadyExists(err) {
				log.Errorf("Failed to create secret: %v", err)
				return nil, err
			}

			status := cr.Status
			status.Status = "ready"
			status.Message = "Cluster ready"
			return &status, nil
		}
	}

	return &cr.Status, nil
}

func deleteGKECluster(cr *v1alpha1.ShootCluster, log *logrus.Entry) error {
	cr.Status.Status = "pending"
	cr.Status.Message = "deleting"

	err := action.Update(cr)
	if err != nil {
		log.Errorf("Failed to update status: %v", err)
		return err
	}

	// Get the GKE Cluster
	gkecluster, err := getRemoteCluster(cr.Status.ClusterName, log)
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Failed to get GKE Cluster: %v", err)
		return err
	}

	if gkecluster != nil {
		if gkecluster.Status == "RUNNING" {
			// only try it once when the cluster is still running
			retrieveLogs(cr, gkecluster, log)
		}

		// Cluster still exists, delete it
		cmd := exec.Command("gcloud", "-q", "container", "clusters", "delete", cr.Status.ClusterName, "--async", "--zone", cr.Spec.Zone)
		out, err := cmd.CombinedOutput()

		if err != nil {
			log.Errorf("Failed to delete cluster: %v", err)
			log.Error(string(out))
			return err
		}

		return nil
	}

	secretName := cr.ObjectMeta.Labels["service.infrabox.net/secret-name"]
	secret := v1.Secret{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Secret",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      secretName,
			Namespace: cr.Namespace,
		},
	}

	err = action.Delete(&secret)
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Failed to delete secret: %v", err)
		return err
	}

	cr.SetFinalizers([]string{})
	err = action.Update(cr)
	if err != nil {
		log.Errorf("Failed to remove finalizers: %v", err)
		return err
	}

	err = action.Delete(cr)
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Failed to delete cr: %v", err)
		return err
	}

	return nil
}

type ServerConfig struct {
	ValidMasterVersions []string `json:"validMasterVersions"`
	ValidNodeVersions   []string `json:"validNodeVersions"`
}

func getExactClusterVersion(cr *v1alpha1.ShootCluster, log *logrus.Entry) (string, error) {
	cmd := exec.Command("gcloud", "container", "get-server-config",
		"--format", "json",
		"--zone", cr.Spec.Zone)

	out, err := cmd.Output()

	if err != nil {
		log.Errorf("Could not get server config: %v", err)
		return "", err
	}

	var config ServerConfig
	err = json.Unmarshal(out, &config)

	if err != nil {
		log.Errorf("Could not parse cluster config: %v", err)
		return "", err
	}

	for _, v := range config.ValidMasterVersions {
		if strings.HasPrefix(v, cr.Spec.ClusterVersion) {
			return v, nil
		}
	}

	return "", fmt.Errorf("Could not find a valid cluster version match for %v", cr.Spec.ClusterVersion)
}

func getRemoteCluster(name string, log *logrus.Entry) (*RemoteCluster, error) {
	cmd := exec.Command("gcloud", "container", "clusters", "list",
		"--filter", "name="+name, "--format", "json")

	out, err := cmd.Output()

	if err != nil {
		log.Errorf("Could not list clusters: %v", err)
		return nil, err
	}

	var gkeclusters []RemoteCluster
	err = json.Unmarshal(out, &gkeclusters)

	if err != nil {
		log.Errorf("Could not parse cluster list: %v", err)
		return nil, err
	}

	if len(gkeclusters) == 0 {
		return nil, nil
	}

	return &gkeclusters[0], nil
}

func newSecret(cluster *v1alpha1.ShootCluster, gke *RemoteCluster) *v1.Secret {
	caCrt, _ := b64.StdEncoding.DecodeString(gke.MasterAuth.ClusterCaCertificate)
	clientKey, _ := b64.StdEncoding.DecodeString(gke.MasterAuth.ClientKey)
	clientCrt, _ := b64.StdEncoding.DecodeString(gke.MasterAuth.ClientCertificate)

	secretName := cluster.ObjectMeta.Labels["service.infrabox.net/secret-name"]

	return &v1.Secret{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Secret",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      secretName,
			Namespace: cluster.Namespace,
			OwnerReferences: []metav1.OwnerReference{
				*metav1.NewControllerRef(cluster, schema.GroupVersionKind{
					Group:   v1alpha1.SchemeGroupVersion.Group,
					Version: v1alpha1.SchemeGroupVersion.Version,
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

	log.Info(string(*data))

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

			filename := "pod_" + pod.Namespace + "_" + pod.Pod + "_" + pod.PodID + ".txt"
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

	err = client.Create(newCollectorDaemonSet(), log)
	if err != nil && !errors.IsAlreadyExists(err) {
		log.Errorf("Failed to create collector daemon set: %v", err)
		return err
	}

	return nil
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
			Name:      "infrabox-collector-fluentd",
			Namespace: "infrabox-collector",
		},
		Spec: appsv1.DaemonSetSpec{
			Template: v1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						"app": "fluentd.collector.infrabox.net",
					},
				},
				Spec: v1.PodSpec{
					Containers: []v1.Container{{
						Name:  "fluentd",
						Image: "quay.io/infrabox/collector-fluentd",
						Resources: v1.ResourceRequirements{
							Limits: v1.ResourceList{
								"memory": resource.MustParse("200Mi"),
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
						}},
						Env: []v1.EnvVar{{
							Name:  "INFRABOX_COLLECTOR_ENDPOINT",
							Value: "http://infrabox-collector-api.infrabox-collector/api/log",
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
					}},
				},
			},
		},
	}
}
