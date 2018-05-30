package stub

import (
    "strconv"
	b64 "encoding/base64"
	"encoding/json"
	"github.com/sap/infrabox/src/services/gcp/pkg/apis/gcp/v1alpha1"
	"os/exec"
    "github.com/satori/go.uuid"

	"github.com/operator-framework/operator-sdk/pkg/sdk/action"
	"github.com/operator-framework/operator-sdk/pkg/sdk/handler"
	"github.com/operator-framework/operator-sdk/pkg/sdk/types"
	"github.com/sirupsen/logrus"
	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
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

func NewHandler() handler.Handler {
	return &Handler{}
}

type Handler struct {}

func syncGKECluster(cr *v1alpha1.GKECluster) (*v1alpha1.GKEClusterStatus, error) {
    if cr.Status.Status == "ready" || cr.Status.Status == "error"  {
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
            logrus.Errorf("Failed to set finalizers: %v", err)
            return nil, err
        }
    }

	// Get the GKE Cluster
	gkecluster, err := getRemoteCluster(cr.Status.ClusterName)
	if err != nil && !errors.IsNotFound(err) {
        logrus.Errorf("Could not get GKE Cluster: %v", err)
        return nil, err
	}

	if gkecluster == nil {
		args := []string{"container", "clusters",
			"create", cr.Status.ClusterName, "--async", "--zone", "us-east1-b", "--enable-autorepair"}

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

		cmd := exec.Command("gcloud", args...)
		out, err := cmd.CombinedOutput()

		if err != nil {
            logrus.Errorf("Failed to create GKE Cluster: %v", err)
            logrus.Error(string(out))
			return nil, err
		}

        status := cr.Status
        status.Status = "pending"
        status.Message = "Cluser is being created"
        return &status, nil
	} else {
		if err != nil {
            logrus.Errorf("Failed to create secret: %v", err)
			return nil, err
		}

		if gkecluster.Status == "RUNNING" {
            err = action.Create(newSecret(cr, gkecluster))
            if err != nil && !errors.IsAlreadyExists(err) {
                logrus.Errorf("Failed to create secret: %v", err)
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

func deleteGKECluster(cr *v1alpha1.GKECluster) error {
    cr.Status.Status = "pending"
    cr.Status.Message = "deleting"

    err := action.Update(cr)
    if err != nil {
        logrus.Errorf("Failed to set finalizers: %v", err)
        return err
    }

	// Get the GKE Cluster
	gkecluster, err := getRemoteCluster(cr.Status.ClusterName)
	if err != nil && !errors.IsNotFound(err) {
        logrus.Errorf("Failed to get GKE Cluster: %v", err)
        return err
	}

	if gkecluster != nil {
        // Cluster still exists, delete it
        cmd := exec.Command("gcloud", "-q", "container", "clusters", "delete", cr.Status.ClusterName, "--async", "--zone", "us-east1-b")
        out, err := cmd.CombinedOutput()

        if err != nil {
            logrus.Errorf("Failed to delete cluster: %v", err)
            logrus.Error(string(out))
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
        logrus.Errorf("Failed to delete secret: %v", err)
        return err
    }

    cr.SetFinalizers([]string{})
    err = action.Update(cr)
    if err != nil {
        logrus.Errorf("Failed to remove finalizers: %v", err)
        return err
    }

    err = action.Delete(cr)
    if err != nil && !errors.IsNotFound(err) {
        logrus.Errorf("Failed to delete cr: %v", err)
        return err
    }

    return nil
}

func (h *Handler) Handle(ctx types.Context, event types.Event) error {
	switch o := event.Object.(type) {
	case *v1alpha1.GKECluster:
        ns := o
        if event.Deleted {
            return nil
        }

        delTimestamp := ns.GetDeletionTimestamp()
        if delTimestamp != nil {
            return deleteGKECluster(ns)
        } else {
            status, err := syncGKECluster(ns)

            if err != nil {
                ns.Status.Status = "error"
                ns.Status.Message = err.Error()
                err = action.Update(ns)
                return err
            } else {
                if ns.Status.Status != status.Status || ns.Status.Message != status.Message   {
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
    return map[string]string {}
}

func getRemoteCluster(name string) (*RemoteCluster, error) {
	cmd := exec.Command("gcloud", "container", "clusters", "list",
		"--filter", "name=" + name, "--format", "json")

	out, err := cmd.CombinedOutput()

	if err != nil {
        logrus.Errorf("Cloud not list clusters: %v", err)
		logrus.Error(string(out))
		return nil, err
	}

	var gkeclusters []RemoteCluster
	err = json.Unmarshal(out, &gkeclusters)

	if err != nil {
        logrus.Errorf("Cloud not parse cluster list: %v", err)
		return nil, err
	}

	if len(gkeclusters) == 0 {
		return nil, nil
	}

	return &gkeclusters[0], nil
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
		},
	}
}


