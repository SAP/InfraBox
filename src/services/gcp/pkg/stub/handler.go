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
    "os"
    "os/exec"
    "path"
    "strconv"
    "strings"
    "time"

    uuid "github.com/satori/go.uuid"

    "github.com/sap/infrabox/src/services/gcp/pkg/apis/gcp/v1alpha1"
    "github.com/sap/infrabox/src/services/gcp/pkg/stub/cleaner"

    goerrors "errors"

    "k8s.io/client-go/discovery"
    "k8s.io/client-go/discovery/cached"
    "k8s.io/client-go/dynamic"
    "k8s.io/client-go/kubernetes"
    _ "k8s.io/client-go/plugin/pkg/client/auth/gcp"
    "k8s.io/client-go/rest"
    "k8s.io/client-go/tools/clientcmd"
    clientcmdapi "k8s.io/client-go/tools/clientcmd/api"

    "github.com/operator-framework/operator-sdk/pkg/sdk/action"
    "github.com/operator-framework/operator-sdk/pkg/sdk/handler"
    "github.com/operator-framework/operator-sdk/pkg/sdk/types"
    "github.com/operator-framework/operator-sdk/pkg/util/k8sutil"

    "github.com/sirupsen/logrus"

    appsv1 "k8s.io/api/apps/v1"
    v1 "k8s.io/api/core/v1"
    rbacv1 "k8s.io/api/rbac/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

    "k8s.io/apimachinery/pkg/api/errors"
    "k8s.io/apimachinery/pkg/api/meta"
    "k8s.io/apimachinery/pkg/api/resource"
    "k8s.io/apimachinery/pkg/runtime/schema"
    "k8s.io/apimachinery/pkg/util/intstr"

    "github.com/mholt/archiver"
)

const adminSAName = "admin"

type MasterAuth struct {
    ClientCertificate    string
    ClientKey            string
    ClusterCaCertificate string
    Username             string
    Password             string
    Token                string
}

type RemoteCluster struct {
    Name       string
    Status     string
    Zone       string
    Endpoint   string
    MasterAuth MasterAuth
}

func NewHandler() handler.Handler {
    return &Handler{}
}

type Handler struct{}

func setClusterName(cr *v1alpha1.GKECluster, log *logrus.Entry) error {
    finalizers := cr.GetFinalizers()
    if len(finalizers) == 0 {
        cr.SetFinalizers([]string{"gcp.service.infrabox.net"})
        cr.Status.Status = "pending"
        u := uuid.NewV4()

        cr.Status.ClusterName = "ib-" + u.String()
        return action.Update(cr)
    }
    return nil
}

func createCluster(cr *v1alpha1.GKECluster, log *logrus.Entry) (*v1alpha1.GKEClusterStatus, error) {
    limit := os.Getenv("MAX_NUM_CLUSTERS")
    status := cr.Status

    if limit != "" {
        gkeclusters, err := getRemoteClusters(log)
        if err != nil && !errors.IsNotFound(err) {
            err = fmt.Errorf("could not get GKE Clusters: %v", err)
            log.Error(err)
            return nil, err
        }

        l, err := strconv.Atoi(limit)

        if err != nil {
            log.Errorf("Failed to parse cluster limit: %v", err)
            return nil, err
        }

        if len(gkeclusters) >= l {
            status.Status = "pending"
            status.Message = "Cluster limit reached, waiting..."
            log.Debug(status.Message)
            return &status, nil
        }
    }

    log.Infof("Create GKE cluster %s", cr.Status.ClusterName)
    args := []string{"container", "clusters",
        "create", cr.Status.ClusterName,
        "--async",
        "--enable-autorepair",
        "--scopes=gke-default,storage-rw",
        "--zone", cr.Spec.Zone,
    }

    args = append(args, "--metadata")
    args = append(args, "block-project-ssh-keys=true")

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

    if !cr.Spec.DisableLegacyAuthorization {
        args = append(args, "--enable-legacy-authorization")
    }

    if cr.Spec.EnablePodSecurityPolicy {
        args = append(args, "--enable-pod-security-policy")
        args = append([]string{"beta"}, args...)
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
        version, channel, err := getExactClusterVersion(cr, log)

        if err != nil {
            return nil, err
        }
        if channel == "" {
            channel = "stable"
        }
        args = append(args, "--cluster-version", version)
        args = append(args, "--release-channel", channel)
    }

    args = append(args, "--enable-ip-alias")
    args = append(args, "--create-subnetwork", "")

    if cr.Spec.ClusterCidr == "" {
        cr.Spec.ClusterCidr = "/18"
        args = append(args, "--cluster-ipv4-cidr", cr.Spec.ClusterCidr)
    }
    if cr.Spec.ServiceCidr == "" {
        cr.Spec.ServiceCidr = "/18"
        args = append(args, "--services-ipv4-cidr", cr.Spec.ServiceCidr)
    }


    cmd := exec.Command("gcloud" , args...)
    out, err := cmd.CombinedOutput()

    if err != nil {
        err = fmt.Errorf("failed to create GKE Cluster: %v, %s", err, out)
        log.Error(err)
        return nil, err
    }

    status.Status = "pending"
    status.Message = "Cluster is being created"
    return &status, nil
}

func syncGKECluster(cr *v1alpha1.GKECluster, log *logrus.Entry) (*v1alpha1.GKEClusterStatus, error) {
    if cr.Status.Status == "ready" || cr.Status.Status == "error" {
        return &cr.Status, nil
    }

    if err := setClusterName(cr, log); err != nil {
        log.Errorf("Failed to set finalizers: %v", err)
        return nil, err
    }
    // Get the GKE Cluster
    gkecluster, err := getRemoteCluster(cr.Status.ClusterName, log)
    if err != nil && !errors.IsNotFound(err) {
        log.Errorf("Could not get GKE Cluster: %v", err)
        return nil, err
    }

    if gkecluster == nil {
        return createCluster(cr, log)
    } else {
        if gkecluster.Status == "RUNNING" {
            err = injectAdminServiceAccount(gkecluster, log)
            if err != nil {
                log.Errorf("Failed to inject admin service account: %v", err)
                return nil, err
            }

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

            log.Infof("GKE cluster %s is ready", cr.Status.ClusterName)

            status := cr.Status
            status.Status = "ready"
            status.Message = "Cluster ready"
            return &status, nil
        }
        if gkecluster.Status == "ERROR" {
            log.Errorf("Error creating cluster %s", cr.Status.ClusterName)
            return nil, goerrors.New("error creating GKE cluster")
        }
    }

    return &cr.Status, nil
}

func getAdminToken(gkecluster *RemoteCluster) (string, error) {
    client, err := newRemoteClusterSDK(gkecluster)
    c, err := kubernetes.NewForConfig(client.kubeConfig)
    if err != nil {
        return "", fmt.Errorf("error getting k8s client: %s, %v", gkecluster.Name, err)
    }

    _, err = c.CoreV1().ServiceAccounts("kube-system").Get(adminSAName, metav1.GetOptions{})
    if err != nil {
        return "", fmt.Errorf("error getting admin service account: %s, %v", gkecluster.Name, err)
    }

    secret, err := c.CoreV1().Secrets("kube-system").Get(adminSAName + "-token", metav1.GetOptions{})
    if err != nil {
        return "", fmt.Errorf("error getting admin sa secret: %s, %v", gkecluster.Name, err)
    }
    token := secret.Data["token"]

    return string(token), nil
}

func injectAdminServiceAccount(gkecluster *RemoteCluster, log *logrus.Entry) error {

    client, err := newRemoteClusterSDK(gkecluster)


    if err != nil {
        err = fmt.Errorf("failed to create remote cluster client: %v", err)
        log.Error(err)
        return err
    }

    err = client.Create(newAdminServiceAccount(), log)
    if err != nil && !errors.IsAlreadyExists(err) {
        err = fmt.Errorf("failed to create admin service account : %v", err)
        log.Error(err)
        return err
    }

    err = client.Create(newAdminCRB(), log)
    if err != nil && !errors.IsAlreadyExists(err) {
        err = fmt.Errorf("failed to create admin service account : %v", err)
        log.Error(err)
        return err
    }

	err = client.Create(newTokenSecret(), log)
	if err != nil && !errors.IsAlreadyExists(err) {
		err = fmt.Errorf("failed to create token secret : %v", err)
		log.Error(err)
		return err
	}

    token, err := getAdminToken(gkecluster)
    if err != nil {
        err = fmt.Errorf("error getting admin token: %s", gkecluster.Name)
        log.Error(err)
        return err
    }

    gkecluster.MasterAuth.Token = token
    return nil
}

func newAdminServiceAccount() *v1.ServiceAccount {
    return &v1.ServiceAccount{
        TypeMeta:                     metav1.TypeMeta{
            Kind: "ServiceAccount",
            APIVersion: "v1",
        },
        ObjectMeta:                   metav1.ObjectMeta{
            Name: adminSAName,
            Namespace: "kube-system",
        },
    }
}

func newAdminCRB() *rbacv1.ClusterRoleBinding {
    return &rbacv1.ClusterRoleBinding{
        TypeMeta: metav1.TypeMeta{
            Kind:       "ClusterRoleBinding",
            APIVersion: "rbac.authorization.k8s.io/v1",
        },
        ObjectMeta: metav1.ObjectMeta{
            Name:      "admin-crb",
            Namespace: "kube-system",
        },
        Subjects: []rbacv1.Subject{{
            Kind:      "ServiceAccount",
            Name:      "admin",
            Namespace: "kube-system",
        }},
        RoleRef: rbacv1.RoleRef{
            Kind:     "ClusterRole",
            Name:     "cluster-admin",
            APIGroup: "rbac.authorization.k8s.io",
        },
    }
}



func getGkeKubeConfig(gkecluster *RemoteCluster, log *logrus.Entry) error {
    kubeConfigPath := "/tmp/kubeconfig-" + gkecluster.Name

    if _, err := os.Stat(kubeConfigPath); !os.IsNotExist(err) {
        return nil
    }

    cmd := exec.Command("gcloud", "container", "clusters", "get-credentials", gkecluster.Name,
                        "--zone", gkecluster.Zone)
    cmd.Env = os.Environ()
    cmd.Env = append(cmd.Env, "KUBECONFIG=" + kubeConfigPath)

    out, err := cmd.CombinedOutput()
    if err != nil {
        log.Errorf("Failed to get kubeconfig for cluster: %s, %s, %v", gkecluster.Name, out, err)
        os.Remove(kubeConfigPath)
        return err
    }

    return nil
}

func deleteRemoteCluster(cr *v1alpha1.GKECluster, log *logrus.Entry) error {
    log.Infof("Deleting cluster %s", cr.Status.ClusterName)
    cmd := exec.Command("gcloud", "-q", "container", "clusters", "delete", cr.Status.ClusterName, "--async", "--zone", cr.Spec.Zone)
    out, err := cmd.CombinedOutput()

    os.Remove("/tmp/kubeconfig-" + cr.ClusterName)

    if err != nil {
        log.Errorf("Failed to delete cluster: %v", err)
        log.Error(string(out))
    }
    return err
}

func collectLogs(c *RemoteCluster, cr *v1alpha1.GKECluster, log *logrus.Entry, started chan int) {
    logPath := path.Join("/tmp", cr.Status.ClusterName)
    err := os.Mkdir(logPath, os.ModePerm)
    if err != nil {
        log.Warningf("Failed to create pod logs dir, won't collect pod logs %v", err)
        close(started)
        return
    }
    close(started)

    done := make(chan error)
    go retrieveLogs(cr, c, log, logPath, done)

    defer func() {
        if _, err := os.Stat(logPath); !os.IsNotExist(err) {
            _ = os.RemoveAll(logPath)
        }
    }()

    for {
        select {
        case <-time.After(time.Minute * 5):
            log.Infof("timeout collecting logs for %s", cr.Status.ClusterName)
            return
        case <-done:
            log.Infof("finished collecting logs for %s", cr.Status.ClusterName)
            return
        }
    }
}

func cleanUpCrd(cr *v1alpha1.GKECluster, log *logrus.Entry) error {
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

    err := action.Delete(&secret)
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

func checkTimeout(cr *v1alpha1.GKECluster, log *logrus.Entry) error {
    t, err := time.Parse(time.RFC1123, cr.Status.FirstCleanedAt)
    if err != nil {
        log.Debugf("couldn't parse stored timestamp ('%s', err: %s) => reset it", cr.Status.FirstCleanedAt, err.Error())
        if err = setAndUpdateFirstCleaned(cr, log); err != nil {
            log.Errorf("couldn't set first cleaned timestamp: %v", err)
            return err
        }
    } else {
        waitDur := time.Minute * 5
        sinceFirstCleaned := time.Since(t).Truncate(time.Second)
        if sinceFirstCleaned < waitDur {
            log.Debugf("timestamp FirstCleaned: %s => %s since then. Wait until %s have elapsed since first cleaning", cr.Status.FirstCleanedAt, sinceFirstCleaned, waitDur)
        } else {
            log.Debugf("timestamp FirstCleaned: %s => %s since then. Proceed with deleting cluster", cr.Status.FirstCleanedAt, sinceFirstCleaned)
            cr.Status.Message = "deleting cluster"
            if err = action.Update(cr); err != nil {
                log.Errorf("Failed to update status: %v", err)
                return err
            }
        }
    }
    return nil
}

func deleteGKECluster(cr *v1alpha1.GKECluster, log *logrus.Entry) error {
    // Get the GKE Cluster
    gkecluster, err := getRemoteCluster(cr.Status.ClusterName, log)
    if err != nil && !errors.IsNotFound(err) {
        log.Errorf("Failed to get GKE Cluster: %v", err)
        return err
    }

    if gkecluster == nil {
        if err = cleanUpCrd(cr, log); err != nil {
            log.Errorf("Failed to delete GKECluster CRD")
        }
        log.Infof("GKE cluster %s removed", cr.Status.ClusterName)
        return err
    }

    if cr.Status.Status != "deleting" {
        cr.Status.Status = "deleting"

        // Don't collect logs for abnormal clusters
        if gkecluster.Status != "RUNNING" {
            cr.Status.Message = "cleaning cluster"
            if err = action.Update(cr); err != nil {
                log.Errorf("Failed to update status: %v", err)
                return err
            }
            return nil
        }

        cr.Status.Message = "collecting logs"

        if err := setAndUpdateFirstCleaned(cr, log); err != nil {
            return err
        }

        log.Infof("Start clean up GKE cluster %s", cr.Status.ClusterName)

        started := make(chan int)
        go collectLogs(gkecluster, cr, log, started)
        <- started
    }

    switch cr.Status.Message {
    case "collecting logs":
        if _, err := os.Stat(path.Join("/tmp", cr.Status.ClusterName)); os.IsNotExist(err) {
            cr.Status.Message = "cleaning cluster"
            err := action.Update(cr)
            if err != nil {
                log.Errorf("Failed to update status: %v", err)
                return err
            }
        }

    case "cleaning cluster":
        isClean, err := cleanupK8s(gkecluster, log)
        if err != nil {
            _ = checkTimeout(cr, log)
            return err
        } else if !isClean { // don't proceed if cluster isn't clean
            _ = checkTimeout(cr, log)
            return nil
        }

        cr.Status.Message = "deleting cluster"
        if err = action.Update(cr); err != nil {
            log.Errorf("Failed to update status: %v", err)
            return err
        }

    case "deleting cluster":
        // cluster is being deleted
        if gkecluster.Status == "STOPPING" {
            return nil
        }
        if err = deleteRemoteCluster(cr, log); err != nil {
            log.Errorf("Error delete gke cluster %s", cr.Status.ClusterName)
            return err
        }
    }

    return nil
}

func setAndUpdateFirstCleaned(cr *v1alpha1.GKECluster, log *logrus.Entry) error {
    cr.Status.FirstCleanedAt = time.Now().Format(time.RFC1123)
    log.Debug("set first-cleaned timestamp to ", cr.Status.FirstCleanedAt)
    err := action.Update(cr)
    if err != nil {
        log.Errorf("Failed to update status: %v", err)
    }
    return err
}

func cleanupK8s(cluster *RemoteCluster, log *logrus.Entry) (bool, error) {
    remoteClusterSdk, err := newRemoteClusterSDK(cluster)
    if err != nil {
        return false, err
    }

    cs, err := kubernetes.NewForConfig(remoteClusterSdk.kubeConfig)
    if err != nil {
        log.Errorf("Failed to create clientset from given kubeconfig: %v", err)
        return false, err
    }

    isClean, err := cleaner.NewK8sCleaner(cs, log).Cleanup()
    return isClean, err
}

func (h *Handler) Handle(ctx types.Context, event types.Event) error {
    switch o := event.Object.(type) {
    case *v1alpha1.GKECluster:
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
            return deleteGKECluster(ns, log)
        } else {
            status, err := syncGKECluster(ns, log)

            if err != nil {
                ns.Status.Status = "error"
                ns.Status.Message = err.Error()
                err = action.Update(ns)
                return err
            } else {
                if ns.Status.Status != status.Status || ns.Status.Message != status.Message {
                    ns.Status = *status
                    err = action.Update(ns)
                    return err
                }
            }
        }
    }
    return nil
}

func getLabels(cr *v1alpha1.GKECluster) map[string]string {
    return map[string]string{}
}

type Channel struct {
    Channel        string   `json:"channel"`
    DefaultVersion string   `json:"defaultVersion"`
    ValidVersions  []string `json:"validVersions"`
}

type ServerConfig struct {
    ValidMasterVersions []string `json:"validMasterVersions"`
    ValidNodeVersions   []string `json:"validNodeVersions"`
    Channels            []Channel `json:"channels"`
}

func getExactClusterVersion(cr *v1alpha1.GKECluster, log *logrus.Entry) (string, string, error) {
    cmd := exec.Command("gcloud", "container", "get-server-config",
        "--format", "json",
        "--zone", cr.Spec.Zone)

    out, err := cmd.Output()

    if err != nil {
        log.Errorf("Could not get server config: %v", err)
        return "", "", err
    }

    var config ServerConfig
    err = json.Unmarshal(out, &config)

    if err != nil {
        log.Errorf("Could not parse cluster config: %v", err)
        return "", "", err
    }

    if cr.Spec.ClusterVersion == "latest" {
        version := "" //Store the latest available version
        for _, c := range config.Channels {
            if c.Channel == "RAPID" {
                for i, v := range c.ValidVersions {
                    if i == 0 {
                        version = v
                    } else {
                        sliceVersion := strings.Split(version, ".")
                        sliceV := strings.Split(v, ".") //Compare major version at first and then minor version
                        if (sliceVersion[1] < sliceV[1]) || (sliceVersion[1] == sliceV[1] && sliceVersion[3] < sliceV[3]) {
                            version = v
                        }
                    }
                }
                return version, strings.ToLower(c.Channel), nil
            }
        }
    }

    for _, c := range config.Channels {
        for _, v := range c.ValidVersions {
            if strings.HasPrefix(v, cr.Spec.ClusterVersion) {
                return v, strings.ToLower(c.Channel), nil
            }
        }
    }

    return "", "" , fmt.Errorf("Could not find a valid cluster version match for %v", cr.Spec.ClusterVersion)
}

func getRemoteCluster(name string, log *logrus.Entry) (*RemoteCluster, error) {
    var out []byte
    var err error
    MAX_RETRY := 3
    for i := 0; i < MAX_RETRY; i++ {
        cmd := exec.Command("gcloud", "container", "clusters", "list",
        "--filter", "name="+name, "--format", "json", "--verbosity", "error")
        out, err = cmd.CombinedOutput()
        if err == nil {
            var gkeclusters []RemoteCluster
            err = json.Unmarshal(out, &gkeclusters)
            if err == nil {
                if len(gkeclusters) == 0 {
                    return nil, nil
                }

                res := &gkeclusters[0]
                if res.Status == "RUNNING" {
                    if err := getGkeKubeConfig(res, log); err != nil {
                        return nil, err
                    }
                    token, err := getAdminToken(res)
                    if err == nil {
                        res.MasterAuth.Token = token
                    }
                }
                return res, nil
            } else {
                log.Warningf("could not parse cluster list: %s, %v, will retry in 10s", out, err)
                time.Sleep(time.Duration(int(time.Second) * 10))
            }
        } else {
            log.Warningf("Could not list clusters, will retry in 10s")
            time.Sleep(time.Duration(int(time.Second) * 10))
        }

    }

    err = fmt.Errorf("Had tried 3 times but still get error: %v", err)
    log.Error(err)
    return nil, err


}

func getRemoteClusters(log *logrus.Entry) ([]RemoteCluster, error) {
    var out []byte
    var err error
    MAX_RETRY := 3
    for i := 0; i < MAX_RETRY; i++ {
        cmd := exec.Command("gcloud", "container", "clusters", "list",
        "--format", "json", "--verbosity", "error")
        out, err = cmd.Output()
        if err == nil {
            var gkeclusters []RemoteCluster
            err = json.Unmarshal(out, &gkeclusters)
            if err == nil {
                return gkeclusters, nil
            } else {
                log.Errorf("Could not parse cluster list: %v , will retry in 10s", err)
                time.Sleep(time.Duration(int(time.Second) * 10))
            }
        } else {
            log.Warningf("Could not list clusters, will retry in 10s")
            time.Sleep(time.Duration(int(time.Second) * 10))
        }

    }
    log.Errorf("Had tried 3 times but still get error: %v", err)
    return nil, err
}

func GcLoop(maxAge string, interval int, log *logrus.Entry) {
    log.Infof("Entering gc loop")

    for ;; {
        go cleanUpClusters(maxAge, log)
        time.Sleep(time.Duration(int(time.Second) * interval))
    }
}

func cleanUpClusters(maxAge string, log *logrus.Entry) {
    log.Infof("Starting GC")

    clusters, err := getOutdatedClusters(maxAge, log)
    if err != nil {
        log.Error("Error get outdated clusters")
        return
    }

    log.Debug("Start clean up clusters")

    for _, cluster := range clusters {
        if cluster.Status == "STOPPING" {
            continue
        }

        if _, err := cleanupK8s(&cluster, log); err != nil {
            log.Errorf("Error clean up cluster: %v", err)
        }

        log.Infof("Deleting cluster %s", cluster.Name)
        cmd := exec.Command("gcloud", "-q", "container", "clusters", "delete", cluster.Name, "--async", "--zone", cluster.Zone)
        out, err := cmd.CombinedOutput()
        if err != nil {
            log.Errorf("Failed to delete cluster: %v", err)
            log.Error(string(out))
        }
    }

    log.Info("GC done")
}

func getOutdatedClusters(maxAge string, log *logrus.Entry) ([]RemoteCluster, error) {
    cmd := exec.Command("bash", "-c", "gcloud container clusters list " +
        "--filter='createTime<-P" + maxAge + " AND name:ib-*' --format json")

    out, err := cmd.Output()

    if err != nil {
        log.Errorf("Could not list outdated clusters: %v, %v", err, out)
        return nil, err
    }

    var gkeclusters []RemoteCluster
    err = json.Unmarshal(out, &gkeclusters)

    if err != nil {
        log.Errorf("Could not parse cluster list: %v", err)
        return nil, err
    }

    return gkeclusters, nil
}

func generateKubeconfig(c *RemoteCluster) []byte {
    caCrt, _ := b64.StdEncoding.DecodeString(c.MasterAuth.ClusterCaCertificate)
    clusters := make(map[string]*clientcmdapi.Cluster)
    clusters[c.Name] = &clientcmdapi.Cluster{
        Server:                   "https://" + c.Endpoint,
        CertificateAuthorityData: caCrt,
    }

    contexts := make(map[string]*clientcmdapi.Context)
    contexts["default-context"] = &clientcmdapi.Context{
        Cluster:   c.Name,
        AuthInfo:  "admin",
    }

    authinfos := make(map[string]*clientcmdapi.AuthInfo)
    authinfos["admin"] = &clientcmdapi.AuthInfo{
        Token: c.MasterAuth.Token,
    }

    clientConfig := clientcmdapi.Config{
        Kind:           "Config",
        APIVersion:     "v1",
        Clusters:       clusters,
        Contexts:       contexts,
        CurrentContext: "default-context",
        AuthInfos:      authinfos,
    }

    kc, _ := clientcmd.Write(clientConfig)
    return kc
}

func newTokenSecret() *v1.Secret {

    secretName := adminSAName + "-token"

    annotations := make(map[string]string)
    annotations["kubernetes.io/service-account.name"]=adminSAName
    return &v1.Secret{
        TypeMeta: metav1.TypeMeta{
            Kind:       "Secret",
            APIVersion: "v1",
        },
        ObjectMeta: metav1.ObjectMeta{
            Name:      secretName,
            Namespace: "kube-system",
            Annotations: annotations,
        },
        Type: "kubernetes.io/service-account-token",
    }
}

func newSecret(cluster *v1alpha1.GKECluster, gke *RemoteCluster) *v1.Secret {
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
            "token":      []byte(gke.MasterAuth.Token),
            "kubeconfig": generateKubeconfig(gke),
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

    req.Header.Add("Authorization", "Bearer " + cluster.MasterAuth.Token)

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

    if resp.StatusCode != 200 {
        return &bodyText, goerrors.New(string(bodyText))
    }

    return &bodyText, nil
}

func uploadToArchive(cr *v1alpha1.GKECluster, log *logrus.Entry, data *[]byte, filename string) error {
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

    if response.StatusCode != 200 {
        return goerrors.New(string(bodyText))
    }

    return nil
}

type CollectedPod struct {
    NamespaceID string   `json:"namespace_id"`
    PodID       string   `json:"pod_id"`
    Pod         string   `json:"pod_name"`
    Containers  []string `json:"containers"`
    Namespace   string   `json:"namespace_name"`
}

func retrieveLogs(cr *v1alpha1.GKECluster, cluster *RemoteCluster, log *logrus.Entry, logPath string, done chan error) {
    log.Infof("Collecting data from GKE cluster %s", cluster.Name)
    defer close(done)

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
            log.Debug("Collecting logs for pod: ", pod.PodID)
            data, err := doCollectorRequest(cluster, log, "/api/pods/"+pod.PodID+"/log/"+container)
            if err != nil {
                log.Warningf("Failed to get collected pod logs: %v", err)
                continue
            }

            filename := "pod_" + pod.Namespace + "_" + pod.Pod + "_" + container + ".txt"
            filename = path.Join(logPath, filename)
            if err := ioutil.WriteFile(filename, *data, os.ModePerm); err != nil {
                log.Debugf("Failed to write pod logs: %v", err)
                continue
            }
        }
    }

    archivePath := path.Join(logPath, "pods_log.zip")
    err = archiver.Archive([]string{logPath}, archivePath)
    if err != nil {
        log.Debugf("Failed to archive log: %v", err)
        return
    }

    archiveData, err := ioutil.ReadFile(archivePath)
    if err != nil {
        log.Debugf("Failed to archive log: %v", err)
        return
    }
    err = uploadToArchive(cr, log, &archiveData, archivePath)
    if err != nil {
        log.Warningf("Failed to upload log to archive: %v", err)
    }
}

func injectCollector(cluster *RemoteCluster, log *logrus.Entry) error {
    client, err := newRemoteClusterSDK(cluster)

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
        log.Errorf("Failed to create object: %v", err)
        return err
    }

    // Update the arg object with the result
    err = k8sutil.UnstructuredIntoRuntimeObject(unstructObj, object)
    if err != nil {
        return fmt.Errorf("failed to unmarshal the retrieved data: %v", err)
    }

    return nil
}

func newRemoteClusterSDK(cluster *RemoteCluster) (*RemoteClusterSDK, error) {
    kubeConfigPath := "/tmp/kubeconfig-" + cluster.Name

    kubeConfig, err := clientcmd.BuildConfigFromFlags("", kubeConfigPath)
    if err != nil {
        return nil, err
    }

    if len(cluster.MasterAuth.Token) > 0 {
        kubeConfig.BearerToken = cluster.MasterAuth.Token
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

func apiResource(gvk schema.GroupVersionKind, restMapper *discovery.DeferredDiscoveryRESTMapper) (*metav1.APIResource, error) {
    mapping, err := restMapper.RESTMapping(gvk.GroupKind(), gvk.Version)
    if err != nil {
        return nil, fmt.Errorf("failed to get the resource REST mapping for GroupVersionKind(%s): %v", gvk.String(), err)
    }
    resource := &metav1.APIResource{
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
    collectorImage := os.Getenv("COLLECTOR_IMAGE")
    if collectorImage == "" {
        collectorImage = "quay.io/infrabox/collector-api"
    }
    return &appsv1.Deployment{
        TypeMeta: metav1.TypeMeta{
            Kind:       "Deployment",
            APIVersion: "apps/v1",
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
                        Image: collectorImage,
                    }},
                },
            },
        },
    }
}

func newFluentbitConfigMap() *v1.ConfigMap {
    return &v1.ConfigMap{
        TypeMeta: metav1.TypeMeta{
            Kind:       "ConfigMap",
            APIVersion: "v1",
        },
        ObjectMeta: metav1.ObjectMeta{
            Name:      "infrabox-fluent-bit",
            Namespace: "infrabox-collector",
        },
        Data: map[string]string{
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
            APIVersion: "apps/v1",
        },
        ObjectMeta: metav1.ObjectMeta{
            Name:      "infrabox-collector-fluent-bit",
            Namespace: "infrabox-collector",
        },
        Spec: appsv1.DaemonSetSpec{
            Selector: &metav1.LabelSelector{
                MatchLabels: map[string]string{
                    "app": "fluentbit.collector.infrabox.net",
                },
            },
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
