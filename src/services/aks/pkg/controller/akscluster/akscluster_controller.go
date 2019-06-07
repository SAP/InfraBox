package akscluster

import (
	"context"
	"github.com/sirupsen/logrus"

	"github.com/sap/infrabox/src/services/aks/pkg/apis/azure/v1alpha1"
	"github.com/satori/go.uuid"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"

	appsv1 "k8s.io/api/apps/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"os/exec"
	"encoding/json"
	"strconv"
	"time"
	"strings"
	"os"
	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"crypto/tls"
	"net/http"
	"io/ioutil"
	"bytes"
	"mime/multipart"
	"fmt"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/apimachinery/pkg/api/resource"
	"k8s.io/client-go/tools/clientcmd"
	"io"
	"crypto/x509"
)

/**
* USER ACTION REQUIRED: This is a scaffold file intended for the user to modify with their own Controller
* business logic.  Delete these comments after modifying this file.*
 */

type RemoteCluster struct {
	Name     string	`json:"name"`
	Status   string `json:"provisioningState"`
	Endpoint string `json:"fqdn"`
	KubeConfigPath string
}

// Add creates a new AKSCluster Controller and adds it to the Manager. The Manager will set fields on the Controller
// and Start it when the Manager is Started.
func Add(mgr manager.Manager) error {
	return add(mgr, newReconciler(mgr))
}

// newReconciler returns a new reconcile.Reconciler
func newReconciler(mgr manager.Manager) reconcile.Reconciler {
	return &ReconcileAKSCluster{client: mgr.GetClient(), scheme: mgr.GetScheme()}
}

// add adds a new Controller to mgr with r as the reconcile.Reconciler
func add(mgr manager.Manager, r reconcile.Reconciler) error {
	// Create a new controller
	c, err := controller.New("akscluster-controller", mgr, controller.Options{Reconciler: r})
	if err != nil {
		return err
	}

	// Watch for changes to primary resource AKSCluster
	err = c.Watch(&source.Kind{Type: &v1alpha1.AKSCluster{}}, &handler.EnqueueRequestForObject{})
	if err != nil {
		return err
	}

	return nil
}

var _ reconcile.Reconciler = &ReconcileAKSCluster{}

// ReconcileAKSCluster reconciles a AKSCluster object
type ReconcileAKSCluster struct {
	// This client, initialized using mgr.Client() above, is a split client
	// that reads objects from the cache and writes to the apiserver
	client client.Client
	scheme *runtime.Scheme
}

// Reconcile reads that state of the cluster for a AKSCluster object and makes changes based on the state read
// and what is in the AKSCluster.Spec
// a Pod as an example
// Note:
// The Controller will requeue the Request to be processed again if the returned error is non-nil or
// Result.Requeue is true, otherwise upon completion it will remove the work from the queue.
func (r *ReconcileAKSCluster) Reconcile(request reconcile.Request) (reconcile.Result, error) {

	// Fetch the AKSCluster instance
	cr := &v1alpha1.AKSCluster{}
	err := r.client.Get(context.TODO(), request.NamespacedName, cr)
	if err != nil {
		if errors.IsNotFound(err) {
			return reconcile.Result{}, nil
		}
		return reconcile.Result{}, err
	}

	customFormatter := new(logrus.TextFormatter)
	customFormatter.TimestampFormat = "2006-01-02 15:04:05"
	customFormatter.FullTimestamp = true
	logrus.SetFormatter(customFormatter)
	log := logrus.WithFields(logrus.Fields{
		"namespace": cr.Namespace,
		"name":      cr.Name,
	})


	delTimestamp := cr.GetDeletionTimestamp()
	if delTimestamp != nil {
		deleteAKSCluster(r, cr, log)
	} else {
		status, err := syncAKSCluster(r, cr, log)

		if err != nil {
			cr.Status.Status = "error"
			cr.Status.Message = err.Error()
			err = r.client.Update(context.TODO(), cr)
			return reconcile.Result{}, err
		} else {
			log.Info("status: ", status.Status, ", msg: ", status.Message, ", cluster name: ", status.ClusterName)
			if cr.Status.Status != status.Status || cr.Status.Message != status.Message {
				cr.Status = *status
				err = r.client.Update(context.TODO(), cr)
				return reconcile.Result{Requeue:true, RequeueAfter:time.Duration(10 * time.Second)}, err
			} else if cr.Status.Status != "ready" {
				return reconcile.Result{Requeue:true, RequeueAfter:time.Duration(30 * time.Second)}, err
			}
		}
	}

	return reconcile.Result{}, nil
}

func syncAKSCluster(r *ReconcileAKSCluster, cr *v1alpha1.AKSCluster, log *logrus.Entry) (*v1alpha1.AKSClusterStatus, error) {
	if cr.Status.Status == "ready" || cr.Status.Status == "error" {
		return &cr.Status, nil
	}

	finalizers := cr.GetFinalizers()
	if len(finalizers) == 0 {
		cr.SetFinalizers([]string{"azure.service.infrabox.net"})
		cr.Status.Status = "pending"
		u := uuid.NewV4()
		cr.Status.ClusterName = "ib-" + string([]byte(u.String())[:18])
		err := r.client.Update(context.TODO(), cr)
		if err != nil {
			log.Errorf("Failed to set finalizers: %v", err)
			return nil, nil
		}
	}

	aksCluster, err := getRemoteCluster(cr.Status.ClusterName, log)
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Could not get AKS Cluster: %v", err)
		return nil, err
	}

	if aksCluster == nil {
		cmd := exec.Command("az", "group", "create", "--name", cr.Status.ClusterName, "--location", cr.Spec.Zone)
		out, err := cmd.CombinedOutput()
		if err != nil {
			log.Errorf("Could not create AKS cluster: %v. msg: %s", err, string(out))
			return nil, err
		}

		args := []string{"aks", "create",
			"--name", cr.Status.ClusterName,
			"--resource-group", cr.Status.ClusterName,
			"--no-wait",
			"--no-ssh-key",
			"--location", cr.Spec.Zone,
			"--service-principal", os.Getenv("SERVICE_PRINCIPAL"),
			"--client-secret", os.Getenv("CLIENT_SECRET"),
		}

		if cr.Spec.DiskSize != 0 {
			args = append(args, "--node-osdisk-size")
			args = append(args, strconv.Itoa(int(cr.Spec.DiskSize)))
		}

		if cr.Spec.MachineType != "" {
			args = append(args, "--node-vm-size")
			args = append(args, cr.Spec.MachineType)
		}

		if cr.Spec.NumNodes != 0 {
			args = append(args, "--node-count")
			args = append(args, strconv.Itoa(int(cr.Spec.NumNodes)))
		}

		if cr.Spec.ClusterVersion != "" {
			args = append(args, "--kubernetes-version")
			args = append(args, cr.Spec.MachineType)
		}

		cmd = exec.Command("az", args...)

		out, err = cmd.CombinedOutput()

		if err != nil {
			log.Errorf("Failed to create AKS Cluster: %v", err)
			log.Error(string(out))
			return nil, err
		}

		status := cr.Status
		status.Status = "pending"
		status.Message = "Cluster is being created"
		return &status, nil
	} else {
		if aksCluster.Status == "Succeeded" {
			err = injectCollector(aksCluster, log)
			if err != nil {
				log.Errorf("Failed to inject collector: %v", err)
				return nil, err
			}
			err = r.client.Create(context.TODO(), newSecret(cr, aksCluster))
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

func getRemoteCluster(name string, log *logrus.Entry) (*RemoteCluster, error) {
	cmd := exec.Command("az", "group", "exists", "--name", name)
	out, err := cmd.CombinedOutput()
	if err != nil {
		log.Errorf("Could not get resource group: %s, msg: %s", name, string(out))
		return nil, err
	}

	if strings.Contains(string(out), "false") {
		//cluster is not created
		log.Infof("Cluster %s was not found. Starting creating", name)
		return nil, nil
	}

	cmd = exec.Command("az", "aks", "show", "--name", name, "--resource-group", name)
	out, err = cmd.CombinedOutput()
	if err != nil {
		log.Errorf("Could not show clusters: %s, msg: %s", name, string(out))
		return nil, err
	}

	var aksCluster RemoteCluster
	err = json.Unmarshal(out, &aksCluster)

	if err != nil {
		log.Errorf("Could not parse cluster: %s", name)
		return nil, err
	}

	if aksCluster.Status != "Succeeded" {
		return &aksCluster, nil
	}

	aksCluster.KubeConfigPath = "/tmp/kube_config_" + name
	cmd = exec.Command("az", "aks", "get-credentials", "--admin", "--name", name, "--resource-group", name, "--file", aksCluster.KubeConfigPath)
	out, err = cmd.CombinedOutput()
	if err != nil {
		log.Errorf("Could not get credentials for clusters: %s, msg: %s", name, string(out))
		return nil, err
	}

	return &aksCluster, nil
}

func deleteAKSCluster(r *ReconcileAKSCluster, cr *v1alpha1.AKSCluster, log *logrus.Entry) error {
	cr.Status.Status = "pending"
	cr.Status.Message = "deleting"

	err := r.client.Update(context.TODO(), cr)
	if err != nil {
		log.Errorf("Failed to update status: %v", err)
		return err
	}

	aksCluster, err := getRemoteCluster(cr.Status.ClusterName, log)
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Could not get AKS Cluster: %v", err)
		return err
	}

	if aksCluster.Status == "Succeeded" {
		// only try it once when the cluster is still running
		retrieveLogs(cr, aksCluster, log)
	}

	secretName := cr.ObjectMeta.Labels["service.infrabox.net/secret-name"]
	secret := &v1.Secret{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Secret",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      secretName,
			Namespace: cr.Namespace,
		},
	}

	err = r.client.Delete(context.TODO(), secret)
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Failed to delete secret: %v", err)
		return err
	}

	name := cr.Status.ClusterName
	cmd := exec.Command("az", "aks", "delete", "--no-wait", "--yes", "--name", name, "--resource-group", name)
	out, err := cmd.CombinedOutput()
	if err != nil {
		log.Errorf("Could not delete cluster: %s, msg: %s", name, string(out))
		return err
	}

	if aksCluster.KubeConfigPath != "" {
		os.Remove(aksCluster.KubeConfigPath)
	}

	cr.SetFinalizers([]string{})
	err = r.client.Update(context.TODO(), cr)
	if err != nil {
		log.Errorf("Failed to remove finalizers: %v", err)
		return err
	}

	err = r.client.Delete(context.TODO(), cr)
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Failed to delete cr: %v", err)
		return err
	}

	log.Infof("AKSCluster %s deleted", name)

	return nil
}

func newSecret(cluster *v1alpha1.AKSCluster, aks *RemoteCluster) *v1.Secret {
	file,err:=os.Open(aks.KubeConfigPath)
	if err !=nil {
		fmt.Println(err)
	}
	defer file.Close()
	adminConf,err:=ioutil.ReadAll(file)
	if err !=nil {
		fmt.Println(err)
	}

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
			"admin.conf":     []byte(adminConf),
		},
	}
}

func doCollectorRequest(cluster *RemoteCluster, log *logrus.Entry, endpoint string) (*[]byte, error) {
	kubeConfig, _ := clientcmd.BuildConfigFromFlags("", cluster.KubeConfigPath)

	cert, err := tls.X509KeyPair(kubeConfig.CertData, kubeConfig.KeyData)
	caCertPool := x509.NewCertPool()
	caCertPool.AppendCertsFromPEM(kubeConfig.CAData)
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs: caCertPool,
	}
	tlsConfig.BuildNameToCertificate()

	transport := &http.Transport{TLSClientConfig: tlsConfig}
	client := &http.Client{Transport: transport}
	var bearer = "Bearer " + kubeConfig.BearerToken

	req, err := http.NewRequest("GET", "https://"+cluster.Endpoint+"/api/v1/namespaces/infrabox-collector/services/infrabox-collector-api:80/proxy"+endpoint, nil)
	if err != nil {
		log.Errorf("Failed to create new request: %v", err)
		return nil, err
	}
	req.Header.Add("Authorization", bearer)

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

func uploadToArchive(cr *v1alpha1.AKSCluster, log *logrus.Entry, data *[]byte, filename string) error {
	annotations := cr.GetAnnotations()
	rootURL, _ := annotations["infrabox.net/root-url"]
	jobToken, _ := annotations["infrabox.net/job-token"]

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

	req, err := http.NewRequest("POST", rootURL+"/api/job/archive", body)

	if err != nil {
		log.Warningf("Failed to create request: %v", err)
		return err
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())
	req.Header.Set("Authorization", "token "+jobToken)
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

func retrieveLogs(cr *v1alpha1.AKSCluster, cluster *RemoteCluster, log *logrus.Entry) {
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

func injectCollector(cluster *RemoteCluster, log *logrus.Entry) error {

	err := kubectlApply(cluster, newCollectorNamespace(), log)
	if err != nil {
		log.Errorf("Failed to create collector deployment: %v", err)
		return err
	}

	err = kubectlApply(cluster, newCollectorCRB(), log)
	if err != nil {
		log.Errorf("Failed to create collector crb: %v", err)
		return err
	}

	err = kubectlApply(cluster, newCollectorDeployment(), log)
	if err != nil {
		log.Errorf("Failed to create collector deployment: %v", err)
		return err
	}

	err = kubectlApply(cluster, newCollectorService(), log)
	if err != nil {
		log.Errorf("Failed to create collector service: %v", err)
		return err
	}

	err = kubectlApply(cluster, newFluentbitConfigMap(), log)
	if err != nil {
		log.Errorf("Failed to create fluent bit config map: %v", err)
		return err
	}

	err = kubectlApply(cluster, newCollectorDaemonSet(), log)
	if err != nil {
		log.Errorf("Failed to create collector daemon set: %v", err)
		return err
	}

	return nil
}

func kubectlApply(cluster *RemoteCluster, object runtime.Object, log *logrus.Entry) (err error) {
	b, err := json.Marshal(object)
	if err != nil {
		log.Errorf("error running MarshalJSON on runtime object: %v", err)
		return err
	}
	cmd := exec.Command("kubectl", "apply", "-f", "-")
	cmd.Env = append(os.Environ(),
		"KUBECONFIG="+cluster.KubeConfigPath,    // this value is used
	)
	stdin, err := cmd.StdinPipe()
	io.WriteString(stdin, string(b))
	stdin.Close()
	out, err := cmd.CombinedOutput()
	if err != nil {
		log.Errorf("error applying object, %s", out)
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
