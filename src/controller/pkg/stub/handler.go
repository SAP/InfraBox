package stub

import (
	"context"

	"github.com/sap/infrabox/src/controller/pkg/apis/core/v1alpha1"

	"github.com/operator-framework/operator-sdk/pkg/sdk"
	"github.com/sirupsen/logrus"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"

    "github.com/onrik/logrus/filename"

	"crypto/rsa"
	jwt "github.com/dgrijalva/jwt-go"
	"io/ioutil"
	"os"
	"strconv"

	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"

    "k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
    "github.com/operator-framework/operator-sdk/pkg/k8sclient"

	goerr "errors"
)

func NewHandler() sdk.Handler {
	data, err := ioutil.ReadFile("/etc/docker/daemon.json")
	if err != nil {
		panic(err)
	}

	return &Controller{
		generalDontCheckCertificates: os.Getenv("INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES"),
		localCacheEnabled:            os.Getenv("INFRABOX_LOCAL_CACHE_ENABLED"),
		jobMaxOutputSize:             os.Getenv("INFRABOX_JOB_MAX_OUTPUT_SIZE"),
		jobMountdockerSocket:         os.Getenv("INFRABOX_JOB_MOUNT_DOCKER_SOCKET"),
		daemonJSON:                   string(data),
		rootURL:                      os.Getenv("INFRABOX_ROOT_URL"),
		tag:                          os.Getenv("INFRABOX_VERSION"),
		dockerRegistry:               os.Getenv("INFRABOX_GENERAL_DOCKER_REGISTRY"),
		localCacheHostPath:           os.Getenv("INFRABOX_LOCAL_CACHE_HOST_PATH"),
		gerritEnabled:                os.Getenv("INFRABOX_GERRIT_ENABLED"),
    }
}

type Controller struct {
	generalDontCheckCertificates string
	localCacheEnabled            string
	jobMaxOutputSize             string
	jobMountdockerSocket         string
	daemonJSON                   string
	rootURL                      string
	tag                          string
	dockerRegistry               string
	localCacheHostPath           string
	gerritEnabled                string
	gerritUsername               string
	gerritHostname               string
	gerritPort                   string
}

func init() {
    logrus.AddHook(filename.NewHook())
    logrus.SetLevel(logrus.WarnLevel)
}

func (h *Controller) Handle(ctx context.Context, event sdk.Event) error {
	switch o := event.Object.(type) {
	case *v1alpha1.IBJob:
        job := o

        log := logrus.WithFields(logrus.Fields{
            "namespace": job.Namespace,
            "name": job.Name,
        })

        if event.Deleted {
            return nil
        }

        delTimestamp := job.GetDeletionTimestamp()
        if delTimestamp != nil {
            return h.deleteJob(job, log)
        } else {
            err := h.syncJob(job, log)

            if job.Status.State.Terminated != nil {
                log.Infof("job terminated, ignoring")
                return nil
            }

            if err == nil {
                return nil
            }

            if errors.IsConflict(err) {
                // we just wait for the next update
                return nil
            }

            // Update status in case of error
            status := job.Status
			status.State.Terminated= &v1alpha1.JobStateTerminated{
                ExitCode: 1,
                Message: err.Error(),
			}

            err = updateStatus(job, &status, log)

            if err != nil && errors.IsConflict(err) {
                return err
            }
        }
	}
	return nil
}

func (c *Controller) newBatchJob(job *v1alpha1.IBJob, token string) *batchv1.Job {
	volumes := []corev1.Volume{
		corev1.Volume{
			Name: "data-dir",
		},
		corev1.Volume{
			Name: "repo",
		},
	}

	volumeMounts := []corev1.VolumeMount{
		corev1.VolumeMount{
			MountPath: "/data",
			Name:      "data-dir",
		},
		corev1.VolumeMount{
			MountPath: "/repo",
			Name:      "repo",
		},
	}

	mem, _ := job.Spec.Resources.Limits.Memory().AsInt64()
	mem = mem / 1024 / 1024

	env := []corev1.EnvVar{
		corev1.EnvVar{
			Name:  "INFRABOX_JOB_ID",
			Value: job.Name,
		},
		corev1.EnvVar{
			Name:  "INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES",
			Value: c.generalDontCheckCertificates,
		},
		corev1.EnvVar{
			Name:  "INFRABOX_JOB_API_URL",
			Value: c.rootURL + "/api/job",
		},
		corev1.EnvVar{
			Name:  "INFRABOX_JOB_GIT_URL",
			Value: "http://localhost:8080",
		},
		corev1.EnvVar{
			Name:  "INFRABOX_SERVICE",
			Value: "job",
		},
		corev1.EnvVar{
			Name:  "INFRABOX_VERSION",
			Value: c.tag,
		},
		corev1.EnvVar{
			Name:  "INFRABOX_LOCAL_CACHE_ENABLED",
			Value: c.localCacheEnabled,
		},
		corev1.EnvVar{
			Name:  "INFRABOX_JOB_MAX_OUTPUT_SIZE",
			Value: c.jobMaxOutputSize,
		},
		corev1.EnvVar{
			Name:  "INFRABOX_JOB_MOUNT_DOCKER_SOCKET",
			Value: c.jobMountdockerSocket,
		},
		corev1.EnvVar{
			Name:  "INFRABOX_JOB_DAEMON_JSON",
			Value: c.daemonJSON,
		},
		corev1.EnvVar{
			Name:  "INFRABOX_ROOT_URL",
			Value: c.rootURL,
		},
		corev1.EnvVar{
			Name:  "INFRABOX_JOB_TOKEN",
			Value: token,
		},
		corev1.EnvVar{
			Name:  "INFRABOX_JOB_RESOURCES_LIMITS_MEMORY",
			Value: strconv.FormatInt(mem, 10),
		},
		corev1.EnvVar{
			Name:  "INFRABOX_JOB_RESOURCES_LIMITS_CPU",
			Value: job.Spec.Resources.Limits.Cpu().String(),
		},
	}

	env = append(env, job.Spec.Env...)

	if c.localCacheEnabled == "true" {
		volumes = append(volumes, corev1.Volume{
			Name: "local-cache",
			VolumeSource: corev1.VolumeSource{
				HostPath: &corev1.HostPathVolumeSource{
					Path: c.localCacheHostPath,
				},
			},
		})

		volumeMounts = append(volumeMounts, corev1.VolumeMount{
			MountPath: "/local-cache",
			Name:      "local-cache",
		})
	}

	cloneEnv := []corev1.EnvVar{
		corev1.EnvVar{
			Name:  "INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES",
			Value: c.generalDontCheckCertificates,
		},
	}
	cloneVolumeMounts := []corev1.VolumeMount{
		corev1.VolumeMount{
			MountPath: "/repo",
			Name:      "repo",
		},
	}

	if c.gerritEnabled == "true" {
		gerritEnv := []corev1.EnvVar{
			corev1.EnvVar{
				Name:  "INFRABOX_GERRIT_HOSTNAME",
				Value: c.gerritHostname,
			},
			corev1.EnvVar{
				Name:  "INFRABOX_GERRIT_USERNAME",
				Value: c.gerritUsername,
			},
			corev1.EnvVar{
				Name:  "INFRABOX_GERRIT_PORT",
				Value: c.gerritPort,
			},
		}

		env = append(env, gerritEnv...)
		cloneEnv = append(env, gerritEnv...)

		cloneVolumeMounts = append(cloneVolumeMounts, corev1.VolumeMount{
			Name:      "gerrit-ssh",
			MountPath: "/tmp/gerrit/",
		})

		volumes = append(volumes, corev1.Volume{
			Name: "gerrit-ssh",
			VolumeSource: corev1.VolumeSource{
				Secret: &corev1.SecretVolumeSource{
					SecretName: "infrabox-gerrit-ssh",
				},
			},
		})
	}

	for _, s := range job.Spec.Services {
		id, _ := s.Metadata.Labels["service.infrabox.net/id"]

		volumes = append(volumes, corev1.Volume{
			Name: id,
			VolumeSource: corev1.VolumeSource{
				Secret: &corev1.SecretVolumeSource{
					SecretName: id,
				},
			},
		})

		volumeMounts = append(volumeMounts, corev1.VolumeMount{
			Name:      id,
			MountPath: "/var/run/infrabox.net/services/" + s.Metadata.Name,
		})
	}

	t := true
	f := false

	runJob := corev1.Container{
		Name:            "run-job",
		ImagePullPolicy: "Always",
		Image:           c.dockerRegistry + "/job:" + c.tag,
		SecurityContext: &corev1.SecurityContext{
			Privileged: &t,
		},
		Env: env,
		Resources: corev1.ResourceRequirements{
			Requests: corev1.ResourceList{
				"cpu":    job.Spec.Resources.Limits.Cpu().DeepCopy(),
				"memory": job.Spec.Resources.Limits.Memory().DeepCopy(),
			},
			Limits: corev1.ResourceList{
				"cpu": job.Spec.Resources.Limits.Cpu().DeepCopy(),
			},
		},
		VolumeMounts: volumeMounts,
	}

	gitJob := corev1.Container{
		Name:            "git-clone",
		ImagePullPolicy: "Always",
		Image:           c.dockerRegistry + "/job-git:" + c.tag,
		Env:             cloneEnv,
		VolumeMounts:    cloneVolumeMounts,
	}

	containers := []corev1.Container{
		gitJob, runJob,
	}

    var zero int32 = 0
    var one int32 = 1
	return &batchv1.Job{
        TypeMeta: metav1.TypeMeta{
            Kind:       "Job",
            APIVersion: "batch/v1",
        },
		ObjectMeta: metav1.ObjectMeta{
			Name:      job.Name,
			Namespace: job.Namespace,
			OwnerReferences: []metav1.OwnerReference{
				*metav1.NewControllerRef(job, schema.GroupVersionKind{
					Group:   v1alpha1.SchemeGroupVersion.Group,
					Version: v1alpha1.SchemeGroupVersion.Version,
					Kind:    "Job",
				}),
			},
			Labels: map[string]string{
				"job.infrabox.net/id": job.Name,
			},
		},
		Spec: batchv1.JobSpec{
			Template: corev1.PodTemplateSpec{
				Spec: corev1.PodSpec{
					AutomountServiceAccountToken: &f,
					Containers:                   containers,
					Volumes:                      volumes,
					RestartPolicy:                "Never",
				},
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						"job.infrabox.net/id": job.Name,
					},
				},
			},
            Completions: &one,
            Parallelism: &one,
            BackoffLimit: &zero,
		},
	}
}

func newBatch(job *v1alpha1.IBJob) *batchv1.Job {
    return &batchv1.Job{
        TypeMeta: metav1.TypeMeta{
            Kind:       "Job",
            APIVersion: "batch/v1",
        },
		ObjectMeta: metav1.ObjectMeta{
			Name:      job.Name,
			Namespace: job.Namespace,
		},
	}
}

func (c *Controller) deletePods(job *v1alpha1.IBJob, log *logrus.Entry) (error) {
    pods := &corev1.PodList{
        TypeMeta: metav1.TypeMeta{
            Kind:       "Pod",
            APIVersion: "v1",
        },
	}

    options := &metav1.ListOptions {
        LabelSelector: "job.infrabox.net/id=" + job.Name,
    }
    err := sdk.List(job.Namespace, pods, sdk.WithListOptions(options))

	if err != nil {
        log.Errorf("Failed to list pods: %v", err)
		return err
	}

	for _, pod := range pods.Items {
		log.Infof("Deleting pod")

        err := sdk.Delete(&pod, sdk.WithDeleteOptions(metav1.NewDeleteOptions(0)))
        if err != nil && !errors.IsNotFound(err) {
            log.Errorf("Failed to delete pod: %v", err)
            return err
        }
	}

    return nil
}

func updateStatus(job *v1alpha1.IBJob, status *v1alpha1.IBJobStatus, log *logrus.Entry) error {
    resourceClient, _, err := k8sclient.GetResourceClient(job.APIVersion, job.Kind, job.Namespace)
    if err != nil {
        log.Errorf("failed to get resource client: %v", err)
        return err
    }

    j, err := resourceClient.Get(job.Name, metav1.GetOptions{})
    if err != nil {
        log.Errorf("failed to get job: %v", err)
        return err
    }

    j.Object["status"] = *status
    _, err = resourceClient.Update(j)
	return err
}


func updateFinalizers(job *v1alpha1.IBJob, finalizers []string, log *logrus.Entry) error {
    resourceClient, _, err := k8sclient.GetResourceClient(job.APIVersion, job.Kind, job.Namespace)
    if err != nil {
        log.Errorf("failed to get resource client: %v", err)
        return err
    }

    j, err := resourceClient.Get(job.Name, metav1.GetOptions{})
    if err != nil {
        log.Errorf("failed to get job: %v", err)
        return err
    }

    j.SetFinalizers(finalizers)
    _, err = resourceClient.Update(j)
	return err
}

func (c *Controller) deleteJob(job *v1alpha1.IBJob, log *logrus.Entry) error {
	err := c.deleteServices(job, log)
	if err != nil {
		log.Errorf("Failed to delete services: %v", err)
		return err
	}

    err = sdk.Delete(newBatch(job), sdk.WithDeleteOptions(metav1.NewDeleteOptions(0)))
    if err != nil && !errors.IsNotFound(err) {
        log.Errorf("Failed to delete batch job: %v", err)
        return err
    }

	err = c.deletePods(job, log)
	if err != nil {
		log.Errorf("Failed to delete pods: %v", err)
		return err
	}

	// Everything deleted, remove finalizers and delete job
	log.Infof("removing finalizers")
	err = updateFinalizers(job, []string{}, log)

	if err != nil {
		return err
	}

	err = sdk.Delete(job)

	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Failed to delete IBJob: %v", err)
	}

	log.Infof("Successfully deleted job")
	return nil
}

func newIBService(name, namespace string, service *v1alpha1.IBJobService) *v1alpha1.IBService {
    return &v1alpha1.IBService{
		TypeMeta: metav1.TypeMeta{
			Kind:       service.Kind,
			APIVersion: service.APIVersion,
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
		},
    }
}


func (c *Controller) deleteService(job *v1alpha1.IBJob, service *v1alpha1.IBJobService, log *logrus.Entry) error {
	log.Infof("Deleting Service")
	id, _ := service.Metadata.Labels["service.infrabox.net/id"]

    s := newIBService(id, job.Namespace, service)
    err := sdk.Delete(s, sdk.WithDeleteOptions(metav1.NewDeleteOptions(0)))

	if err != nil {
		log.Errorf("Failed to delete service: %s", err.Error())
		return err
	}

	return nil
}

func (c *Controller) createService(service *v1alpha1.IBJobService, job *v1alpha1.IBJob, log *logrus.Entry) (bool, error) {
	id, ok := service.Metadata.Labels["service.infrabox.net/id"]
	if !ok {
		log.Errorf("Infrabox service id not set")
		return false, goerr.New("Infrabox service id not set")
	}

    resourceClient, _, err := k8sclient.GetResourceClient(job.APIVersion, job.Kind, job.Namespace)
    if err != nil {
        log.Errorf("failed to get resource client: %v", err)
        return false, err
    }

    j, err := resourceClient.Get(job.Name, metav1.GetOptions{})
    if err != nil {
        log.Errorf("failed to get job: %v", err)
        return false, err
    }

    services, ok := unstructured.NestedSlice(j.Object, "spec", "services")

    if !ok {
        return false, goerr.New("services not found")
    }

    var spec *map[string]interface{} = nil
    for _, ser := range(services) {
        m := ser.(map[string]interface{})
        un := unstructured.Unstructured{Object: m}
        name := un.GetName()

        if name == service.Metadata.Name {
            newSpec, ok := unstructured.NestedMap(m, "spec")

            if !ok {
               newSpec = make(map[string]interface{})
            }

            spec = &newSpec
        }
    }

    if spec == nil {
        return false, goerr.New("service not found")
    }

    newService := &unstructured.Unstructured{
        Object: map[string]interface{}{
            "apiVersion": service.APIVersion,
            "kind":       service.Kind,
            "metadata": map[string]interface{}{
                "name":      id,
                "namespace": job.Namespace,
                "labels": map[string]string{
                    "service.infrabox.net/secret-name": id,
                },
            },
            "spec": *spec,
        },
    }

    resourceClient, _, err = k8sclient.GetResourceClient(service.APIVersion, service.Kind, job.Namespace)
    if err != nil {
        log.Errorf("failed to get resource client: %v", err)
        return false, err
    }

    _, err = resourceClient.Create(newService)
    if err != nil && !errors.IsAlreadyExists(err) {
        log.Errorf("Failed to post service: %s", err.Error())
        return false, err
    }

    log.Infof("Service %s/%s created", service.APIVersion, service.Kind)

    s, err := resourceClient.Get(id, metav1.GetOptions{})
    if err != nil {
        return false, err
    }

    status, ok := unstructured.NestedString(s.Object, "status", "status")

    if !ok {
        return false, nil
    }

    if status == "ready" {
        return true, nil
    }

    if status == "error" {
        msg, ok := unstructured.NestedString(s.Object, "status", "message")

        if !ok {
            msg = "Internal Error"
        }

        log.Errorf("service is in state error: %s", msg)
        return false, goerr.New(msg)
    }

	return false, nil
}

func (c *Controller) deleteServices(job *v1alpha1.IBJob, log *logrus.Entry) error {
	if job.Spec.Services == nil {
		return nil
	}

	log.Info("Delete additional services")

	for _, s := range job.Spec.Services {
        l := log.WithFields(logrus.Fields{
            "service_version": s.APIVersion,
            "service_kind": s.Kind,
        })
		err := c.deleteService(job, &s, l)

		if err != nil {
			return nil
		}

		l.Info("Service deleted")
	}

	return nil
}

func (c *Controller) createServices(job *v1alpha1.IBJob, log *logrus.Entry) (bool, error) {
	if job.Spec.Services == nil {
		return true, nil
	}

	log.Info("Create additional services")

	ready := true
	for _, s := range job.Spec.Services {
        l := log.WithFields(logrus.Fields{
            "service_version": s.APIVersion,
            "service_kind": s.Kind,
        })

		r, err := c.createService(&s, job, l)

		if err != nil {
			l.Errorf("Failed to create service: %s", err.Error())
			return false, err
		}

		if r {
			l.Info("Service ready")
		} else {
			ready = false
			l.Infof("Service not yet ready")
		}
	}

	return ready, nil
}

func (c *Controller) createBatchJob(job *v1alpha1.IBJob, log *logrus.Entry) error {
	log.Infof("%s/%s: Creating Batch Job", job.Namespace, job.Name)

	keyPath := os.Getenv("INFRABOX_RSA_PRIVATE_KEY_PATH")

	if keyPath == "" {
		keyPath = "/var/run/secrets/infrabox.net/rsa/id_rsa"
	}

	var signKey *rsa.PrivateKey

	signBytes, err := ioutil.ReadFile(keyPath)
	if err != nil {
		log.Errorf("Failed to create token")
		return err
	}

	signKey, err = jwt.ParseRSAPrivateKeyFromPEM(signBytes)
	if err != nil {
		log.Errorf("Failed to create token")
		return err
	}

	t := jwt.NewWithClaims(jwt.GetSigningMethod("RS256"), jwt.MapClaims{
		"job": map[string]string{
			"id": job.Name,
		},
		"type": "job",
	})

	token, err := t.SignedString(signKey)

	if err != nil {
		log.Errorf("Failed to creat token")
		return err
	}

	sdk.Create(c.newBatchJob(job, token))

	if err != nil && !errors.IsAlreadyExists(err) {
		log.Errorf("Failed to create job: %s", err.Error())
		return err
	}

	log.Infof("Successfully created batch job")
	return nil
}

func updateJobStatus(status v1alpha1.IBJobStatus, batch *batchv1.Job, pod *corev1.Pod) v1alpha1.IBJobStatus {
	if len(pod.Status.ContainerStatuses) < 2 {
       status.State.Waiting = &v1alpha1.JobStateWaiting {
           Message: "Containers are being created",
       }
    } else {
        s := pod.Status.ContainerStatuses[1].State

        // Still waiting
        if s.Waiting != nil {
            msg := s.Waiting.Message

            if len(msg) == 0 {
                msg = "Containers are being created"
            }

            status.State.Waiting = &v1alpha1.JobStateWaiting {
               Message: msg,
            }
        }

        if s.Running != nil || s.Terminated != nil {
            status.State.Running = &v1alpha1.JobStateRunning {
                StartTime: batch.Status.StartTime,
            }
        }

        if s.Terminated != nil {
            status.State.Running.CompletionTime = &s.Terminated.FinishedAt
            status.State.Terminated = &v1alpha1.JobStateTerminated {
                ExitCode: s.Terminated.ExitCode,
                Message: s.Terminated.Message,
            }
        }
    }

    return status
}

func (c *Controller) syncJob(job *v1alpha1.IBJob, log *logrus.Entry) error {
	// First set finalizers so we don't forget to delete it later on
    if len(job.GetFinalizers()) == 0 {
        err := updateFinalizers(job, []string{"job.infrabox.net"}, log)

        if err != nil {
            return err
        }
    }

	batch := newBatch(job)
	err := sdk.Get(batch)

	if err != nil && !errors.IsNotFound(err) {
		return err
	}

	// Create job if does not already exist
	if err != nil && errors.IsNotFound(err) {
		servicesCreated, err := c.createServices(job, log)

		if err != nil {
			log.Errorf("Failed to create services: %s", err.Error())
			return err
		}

		if !servicesCreated {
			log.Infof("Services not yet ready")
            status := job.Status
            status.State.Waiting = &v1alpha1.JobStateWaiting {
                Message: "Services not yet ready",
            }
            return updateStatus(job, &status, log)
		}

		err = c.createBatchJob(job, log)

		if err != nil {
			log.Errorf("Failed to create batch job: %s", err.Error())
			return err
		}

		log.Infof("Batch job created")

		// Get job again so we can sync it
		err = sdk.Get(batch)
		if err != nil && !errors.IsNotFound(err) {
			return err
		}
	}

    pods := &corev1.PodList{
        TypeMeta: metav1.TypeMeta{
            Kind:       "Pod",
            APIVersion: "v1",
        },
	}

    options := &metav1.ListOptions {
        LabelSelector: "job.infrabox.net/id=" + job.Name,
    }
    err = sdk.List(job.Namespace, pods, sdk.WithListOptions(options))

	if err != nil {
        log.Errorf("Failed to list pods: %v", err)
		return err
	}

    status := job.Status
	if len(pods.Items) != 0 {
		pod := pods.Items[0]
		status = updateJobStatus(status, batch, &pod)
	}

	return updateStatus(job, &status, log)
}
