package stub

import (
	"encoding/json"
	//goerr "errors"
	"github.com/sap/infrabox/src/controller/pkg/apis/core/v1alpha1"

	"github.com/operator-framework/operator-sdk/pkg/sdk"
	"github.com/sirupsen/logrus"

	"k8s.io/apiextensions-apiserver/pkg/apis/apiextensions"
	"k8s.io/apimachinery/pkg/api/errors"

	//"k8s.io/apimachinery/pkg/api/errors"
	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"

	"github.com/operator-framework/operator-sdk/pkg/k8sclient"
)

type Function struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata"`
	Spec              FunctionSpec `json:"spec"`
}

type FunctionSpec struct {
	Image            string                        `json:"image,omitempty" protobuf:"bytes,2,opt,name=image"`
	Command          []string                      `json:"command,omitempty" protobuf:"bytes,3,rep,name=command"`
	Args             []string                      `json:"args,omitempty" protobuf:"bytes,4,rep,name=args"`
	Env              []corev1.EnvVar               `json:"env,omitempty" patchStrategy:"merge" patchMergeKey:"name" protobuf:"bytes,7,rep,name=env"`
	Resources        corev1.ResourceRequirements   `json:"resources,omitempty" protobuf:"bytes,8,opt,name=resources"`
	SecurityContext  *corev1.SecurityContext       `json:"securityContext,omitempty" protobuf:"bytes,15,opt,name=securityContext"`
	VolumeMounts     []corev1.VolumeMount          `json:"volumeMounts,omitempty" patchStrategy:"merge" patchMergeKey:"mountPath" protobuf:"bytes,9,rep,name=volumeMounts"`
	Volumes          []corev1.Volume               `json:"volumes,omitempty" patchStrategy:"merge,retainKeys" patchMergeKey:"name" protobuf:"bytes,1,rep,name=volumes"`
	ImagePullSecrets []corev1.LocalObjectReference `json:"imagePullSecrets,omitempty" patchStrategy:"merge" patchMergeKey:"name" protobuf:"bytes,15,rep,name=imagePullSecrets"`
}

type FunctionValidation struct {
	OpenAPIV3Schema *apiextensions.JSONSchemaProps
}

func getFunction(name string, log *logrus.Entry) (*Function, error) {
	logrus.Infof("Get function: %s", name)

	resourceClient, _, err := k8sclient.GetResourceClient("core.infrabox.net/v1alpha1", "IBFunction", "")
	if err != nil {
		log.Errorf("failed to get resource client: %v", err)
		return nil, err
	}

	f, err := resourceClient.Get(name, metav1.GetOptions{})
	if err != nil {
		log.Errorf("failed to get function: %v", err)
		return nil, err
	}

	j, err := f.MarshalJSON()

	if err != nil {
		log.Errorf("failed to marshal json: %v", err)
		return nil, err
	}

	var function Function
	err = json.Unmarshal(j, &function)

	if err != nil {
		log.Errorf("failed to unmarshal json: %v", err)
		return nil, err
	}

	return &function, nil
}

func validateFunctionInvocation(cr *v1alpha1.IBFunctionInvocation) error {
	return nil
}

func (c *Controller) syncFunctionInvocation(cr *v1alpha1.IBFunctionInvocation, log *logrus.Entry) error {
	logrus.Info("Sync function invocation")

	finalizers := cr.GetFinalizers()

	// validate workflow on first occurence
	if len(finalizers) == 0 {
		err := validateFunctionInvocation(cr)

		if err != nil {
			return err
		}

		// Set finalizers
		cr.SetFinalizers([]string{"core.service.infrabox.net"})
		cr.Status.State = corev1.ContainerState{
			Waiting: &corev1.ContainerStateWaiting{
				Message: "Container is being created",
			},
		}

		err = sdk.Update(cr)
		if err != nil {
			logrus.Errorf("Failed to set finalizers: %v", err)
			return err
		}
	}

	batch := c.newBatch(cr)
	err := sdk.Get(batch)

	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Failed to get batch jobs: %s", err.Error())
		return err
	}

	// Create job if does not already exist
	if err != nil && errors.IsNotFound(err) {
		function, err := getFunction(cr.Spec.FunctionName, log)

		if err != nil {
			logrus.Errorf("Failed to get function %v: ", err)
			return err
		}

		// TODO(validate)
		err = sdk.Create(c.newBatchJob(cr, function))

		if err != nil && !errors.IsAlreadyExists(err) {
			log.Errorf("Failed to create job: %s", err.Error())
			return err
		}

		log.Info("Batch job created")

		// Get job again so we can sync it
		err = sdk.Get(batch)
		if err != nil && !errors.IsNotFound(err) {
			log.Errorf("Failed to get batch job: %s", err.Error())
			return err
		}
	}

	pods := &corev1.PodList{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Pod",
			APIVersion: "v1",
		},
	}

	options := &metav1.ListOptions{
		LabelSelector: "function.infrabox.net/function-invocation-name=" + cr.Name,
	}
	err = sdk.List(cr.Namespace, pods, sdk.WithListOptions(options))

	if err != nil {
		log.Errorf("Failed to list pods: %v", err)
		return err
	}

	if len(pods.Items) != 0 {
		pod := pods.Items[0]
		if len(pod.Status.ContainerStatuses) != 0 {
			cr.Status.State = pod.Status.ContainerStatuses[0].State
            cr.Status.NodeName = pod.Spec.NodeName
			log.Info("Updating job status")
			return sdk.Update(cr)
		}

		if pod.Status.Phase == "Failed" {
			cr.Status.State = corev1.ContainerState{
				Terminated: &corev1.ContainerStateTerminated{
					ExitCode: 200,
					Reason:   pod.Status.Reason,
					Message:  pod.Status.Message,
				},
			}

			log.Errorf("%+v\n", pod)

			log.Info("Updating job status")
			return sdk.Update(cr)
		}
	}

	return nil
}

func (c *Controller) createBatchJob(fi *v1alpha1.IBFunctionInvocation, function *Function, log *logrus.Entry) error {
	log.Infof("Creating Batch Job")

	log.Infof("Successfully created batch job")
	return nil
}

func (c *Controller) deletePods(fi *v1alpha1.IBFunctionInvocation, log *logrus.Entry) error {
	pods := &corev1.PodList{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Pod",
			APIVersion: "v1",
		},
	}

	options := &metav1.ListOptions{
		LabelSelector: "function.infrabox.net/function-invocation-name=" + fi.Name,
	}
	err := sdk.List(fi.Namespace, pods, sdk.WithListOptions(options))

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

func (c *Controller) deleteFunctionInvocation(cr *v1alpha1.IBFunctionInvocation, log *logrus.Entry) error {
	err := sdk.Delete(c.newBatch(cr), sdk.WithDeleteOptions(metav1.NewDeleteOptions(0)))
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Failed to delete batch function invocation: %v", err)
		return err
	}

	err = c.deletePods(cr, log)
	if err != nil {
		log.Errorf("Failed to delete pods: %v", err)
		return err
	}

	cr.SetFinalizers([]string{})
	err = sdk.Update(cr)
	if err != nil {
		logrus.Errorf("Failed to remove finalizers: %v", err)
		return err
	}

	// Workaround for older K8s versions which don't properly gc
	err = sdk.Delete(cr, sdk.WithDeleteOptions(metav1.NewDeleteOptions(0)))
	if err != nil && !errors.IsNotFound(err) {
		log.Errorf("Failed to delete function invocation: %v", err)
		return err
	}

	return nil
}

func (c *Controller) newBatchJob(fi *v1alpha1.IBFunctionInvocation, function *Function) *batchv1.Job {
	f := false

	job := corev1.Container{
		Name:            "function",
		ImagePullPolicy: "Always",
		Image:           function.Spec.Image,
		Resources:       function.Spec.Resources,
		Env:             function.Spec.Env,
		SecurityContext: function.Spec.SecurityContext,
		VolumeMounts:    function.Spec.VolumeMounts,
	}

	job.VolumeMounts = append(job.VolumeMounts, fi.Spec.VolumeMounts...)
	job.Env = append(job.Env, fi.Spec.Env...)

	if fi.Spec.Resources != nil {
		job.Resources = *fi.Spec.Resources
	}

	containers := []corev1.Container{
		job,
	}

	var zero int32 = 0
	var zero64 int64 = 0
	var one int32 = 1
	batch := &batchv1.Job{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Job",
			APIVersion: "batch/v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      fi.Name,
			Namespace: fi.Namespace,
			OwnerReferences: []metav1.OwnerReference{
				*metav1.NewControllerRef(fi, schema.GroupVersionKind{
					Group:   v1alpha1.SchemeGroupVersion.Group,
					Version: v1alpha1.SchemeGroupVersion.Version,
					Kind:    "IBFunctionInvocation",
				}),
			},
			Labels: map[string]string{
				"function.infrabox.net/function-invocation-name": fi.Name,
			},
		},
		Spec: batchv1.JobSpec{
			Template: corev1.PodTemplateSpec{
				Spec: corev1.PodSpec{
					AutomountServiceAccountToken:  &f,
					Containers:                    containers,
					RestartPolicy:                 "Never",
					TerminationGracePeriodSeconds: &zero64,
					Volumes:          function.Spec.Volumes,
					ImagePullSecrets: function.Spec.ImagePullSecrets,
				},
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						"function.infrabox.net/function-invocation-name": fi.Name,
					},
				},
			},
			Completions:  &one,
			Parallelism:  &one,
			BackoffLimit: &zero,
		},
	}

	batch.Spec.Template.Spec.Volumes = append(batch.Spec.Template.Spec.Volumes, fi.Spec.Volumes...)

	return batch
}

func (c *Controller) newBatch(fi *v1alpha1.IBFunctionInvocation) *batchv1.Job {
	return &batchv1.Job{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Job",
			APIVersion: "batch/v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      fi.Name,
			Namespace: fi.Namespace,
		},
	}
}
