package stub

import (
    goerr "errors"
	"github.com/sap/infrabox/src/controller/pkg/apis/core/v1alpha1"

	"github.com/operator-framework/operator-sdk/pkg/sdk"
	"github.com/sirupsen/logrus"

	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/runtime/schema"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	corev1 "k8s.io/api/core/v1"

    "k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
    "github.com/operator-framework/operator-sdk/pkg/k8sclient"
)

func (c *Controller) deletePipelineInvocation(cr *v1alpha1.IBPipelineInvocation, log *logrus.Entry) error {
	err := c.deleteServices(cr, log)
	if err != nil {
		log.Errorf("Failed to delete services: %v", err)
		return err
	}

    cr.SetFinalizers([]string{})
    err = updateStatus(cr, log)
    if err != nil {
        logrus.Errorf("Failed to remove finalizers: %v", err)
        return err
    }

	return nil
}

func (c *Controller) deleteService(pi *v1alpha1.IBPipelineInvocation, service *v1alpha1.IBPipelineService, log *logrus.Entry) error {
	log.Infof("Deleting Service")
	id, _ := service.Metadata.Labels["service.infrabox.net/id"]
    resourceClient, _, err := k8sclient.GetResourceClient(service.APIVersion, service.Kind, pi.Namespace)
    if err != nil {
        log.Errorf("failed to get resource client: %v", err)
        return err
    }

    err = resourceClient.Delete(id, metav1.NewDeleteOptions(0))
    if err != nil && !errors.IsNotFound(err) {
        log.Errorf("Failed to delete service: %s", err.Error())
        return err
    }

	return nil
}


func (c *Controller) deleteServices(pi *v1alpha1.IBPipelineInvocation, log *logrus.Entry) error {
	if pi.Spec.Services == nil {
		return nil
	}

	log.Info("Delete additional services")

	for _, s := range pi.Spec.Services {
        l := log.WithFields(logrus.Fields{
            "service_version": s.APIVersion,
            "service_kind": s.Kind,
        })
		err := c.deleteService(pi, &s, l)

		if err != nil {
			return nil
		}

		l.Info("Service deleted")
	}

	return nil
}


func updateStatus(pi *v1alpha1.IBPipelineInvocation, log *logrus.Entry) error {
    resourceClient, _, err := k8sclient.GetResourceClient(pi.APIVersion, pi.Kind, pi.Namespace)
    if err != nil {
        log.Errorf("failed to get resource client: %v", err)
        return err
    }

    j, err := resourceClient.Get(pi.Name, metav1.GetOptions{})
    if err != nil {
        log.Errorf("failed to get pi: %v", err)
        return err
    }

    j.Object["status"] = pi.Status
    j.SetFinalizers(pi.GetFinalizers())
    _, err = resourceClient.Update(j)

    if err != nil {
        return err
    }

    return sdk.Get(pi)
}

func (c *Controller) syncFunctionInvocations(cr *v1alpha1.IBPipelineInvocation, log *logrus.Entry) error {
	pipeline := newPipeline(cr)
	err := sdk.Get(pipeline)

	if err != nil {
        logrus.Errorf("Pipeline not found: ", cr.Spec.PipelineName)
        return err
	}

    // Sync all functions
    for index, pipelineStep := range pipeline.Spec.Steps {
        if len(cr.Status.StepStatuses) <= index {
            // No state yet for this step
            cr.Status.StepStatuses = append(cr.Status.StepStatuses, v1alpha1.IBFunctionInvocationStatus {
                State: corev1.ContainerState {
                    Waiting: &corev1.ContainerStateWaiting {
                        Message: "Containers are being created",
                    },
                },
            })
        }

        status := &cr.Status.StepStatuses[index]

        if status.State.Terminated != nil {
            // step already finished
            log.Info("Step already finished")
            continue
        }

        stepInvocation, _ := cr.Spec.Steps[pipelineStep.Name]

        fi := newFunctionInvocation(cr, stepInvocation, &pipelineStep)
        err = sdk.Create(fi)

        if err != nil && !errors.IsAlreadyExists(err) {
            log.Errorf("Failed to create function invocation: %s", err.Error())
            return err
        }

        fi = newFunctionInvocation(cr, stepInvocation, &pipelineStep)
        err = sdk.Get(fi)
        if err != nil {
            return err
        }

        cr.Status.StepStatuses[index] = fi.Status
        if fi.Status.State.Terminated != nil {
            // don't continue with next step until this one finished
            break
        }
    }

    firstState := cr.Status.StepStatuses[0].State

    if firstState.Running != nil {
        cr.Status.Message = ""
        cr.Status.Status = "running"
        cr.Status.StartTime = &firstState.Running.StartedAt
    } else if firstState.Terminated != nil {
        cr.Status.Message = ""
        cr.Status.Status = "running"
        cr.Status.StartTime = &firstState.Terminated.StartedAt
    }

    // Determine current status
    allTerminated := true
    for _, stepStatus := range cr.Status.StepStatuses {
        if stepStatus.State.Terminated == nil {
            allTerminated = false
        }
    }

    if allTerminated {
        cr.Status.Message = ""
        cr.Status.Status = "terminated"
        cr.Status.StartTime = &firstState.Terminated.StartedAt
        cr.Status.CompletionTime = &cr.Status.StepStatuses[len(cr.Status.StepStatuses)-1].State.Terminated.FinishedAt
    }

    return nil
}

func (c *Controller) syncPipelineInvocation(cr *v1alpha1.IBPipelineInvocation, log *logrus.Entry) error {
    logrus.Info("Sync pipeline invocation")

	finalizers := cr.GetFinalizers()
	if len(finalizers) == 0 {
        cr.SetFinalizers([]string{"core.service.infrabox.net"})
        cr.Status.Status = "pending"
    }

    servicesCreated, err := c.createServices(cr, log)

    if err != nil {
        log.Errorf("Failed to create services: %s", err.Error())
        return err
    }

    if servicesCreated {
        log.Infof("Services are ready")
        err = c.syncFunctionInvocations(cr, log)

        if err != nil {
            return err
        }
    } else {
        log.Infof("Services not yet ready")
        cr.Status.Message = "Services are being created"
    }

    log.Info("Updating state")
    return updateStatus(cr, log)
}

func (c *Controller) createService(service *v1alpha1.IBPipelineService, pi *v1alpha1.IBPipelineInvocation, log *logrus.Entry) (bool, error) {
	id, ok := service.Metadata.Labels["service.infrabox.net/id"]
	if !ok {
		log.Errorf("Infrabox service id not set")
		return false, goerr.New("Infrabox service id not set")
	}

    resourceClient, _, err := k8sclient.GetResourceClient(pi.APIVersion, pi.Kind, pi.Namespace)
    if err != nil {
        log.Errorf("failed to get resource client: %v", err)
        return false, err
    }

    j, err := resourceClient.Get(pi.Name, metav1.GetOptions{})
    if err != nil {
        log.Errorf("failed to get pi: %v", err)
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
                "namespace": pi.Namespace,
                "labels": map[string]string{
                    "service.infrabox.net/secret-name": id,
                },
            },
            "spec": *spec,
        },
    }

    resourceClient, _, err = k8sclient.GetResourceClient(service.APIVersion, service.Kind, pi.Namespace)
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

func (c *Controller) createServices(pi *v1alpha1.IBPipelineInvocation, log *logrus.Entry) (bool, error) {
	if pi.Spec.Services == nil {
        log.Info("No services specified")
		return true, nil
	}

	log.Info("Creating additional services")

	ready := true
	for _, s := range pi.Spec.Services {
        l := log.WithFields(logrus.Fields{
            "service_version": s.APIVersion,
            "service_kind": s.Kind,
        })

		r, err := c.createService(&s, pi, l)

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


func newPipeline(cr *v1alpha1.IBPipelineInvocation) *v1alpha1.IBPipeline {
	return &v1alpha1.IBPipeline {
		TypeMeta: metav1.TypeMeta{
            APIVersion: v1alpha1.SchemeGroupVersion.Group + "/" + v1alpha1.SchemeGroupVersion.Version,
			Kind:       "IBPipeline",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      cr.Spec.PipelineName,
			Namespace: cr.Namespace,
        },
    }
}

func newFunctionInvocation(pi *v1alpha1.IBPipelineInvocation,
				      invocationStep v1alpha1.IBPipelineInvocationStep,
					  step *v1alpha1.IBPipelineStep) *v1alpha1.IBFunctionInvocation {
	env := step.Env
	resources := step.Resources

	env = append(env, invocationStep.Env...)
	if invocationStep.Resources != nil {
		resources = invocationStep.Resources
	}

    fi := &v1alpha1.IBFunctionInvocation{
		TypeMeta: metav1.TypeMeta{
            APIVersion: v1alpha1.SchemeGroupVersion.Group + "/" + v1alpha1.SchemeGroupVersion.Version,
			Kind:       "IBFunctionInvocation",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      pi.Name + "-" + step.Name,
			Namespace: pi.Namespace,
			OwnerReferences: newOwnerReferenceForPipelineInvocation(pi),
        },
		Spec: v1alpha1.IBFunctionInvocationSpec {
			FunctionName: step.FunctionName,
			Env: env,
			Resources: resources,
			Volumes: step.Volumes,
			VolumeMounts: step.VolumeMounts,
		},
    }

	for _, s := range pi.Spec.Services {
		id, _ := s.Metadata.Labels["service.infrabox.net/id"]

		fi.Spec.Volumes = append(fi.Spec.Volumes, corev1.Volume{
			Name: id,
			VolumeSource: corev1.VolumeSource{
				Secret: &corev1.SecretVolumeSource{
					SecretName: id,
				},
			},
		})

		fi.Spec.VolumeMounts = append(fi.Spec.VolumeMounts, corev1.VolumeMount{
			Name:      id,
			MountPath: "/var/run/infrabox.net/services/" + s.Metadata.Name,
		})
	}

    return fi
}

func newOwnerReferenceForPipelineInvocation(cr *v1alpha1.IBPipelineInvocation) []metav1.OwnerReference {
    return []metav1.OwnerReference{
        *metav1.NewControllerRef(cr, schema.GroupVersionKind{
            Group:   v1alpha1.SchemeGroupVersion.Group,
            Version: v1alpha1.SchemeGroupVersion.Version,
            Kind:    "IBPipelineInvocation",
        }),
    }
}

