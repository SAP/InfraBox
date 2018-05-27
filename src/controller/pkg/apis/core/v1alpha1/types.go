package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	corev1 "k8s.io/api/core/v1"
)

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type IBJobList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`
	Items           []IBJob `json:"items"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type IBJob struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata"`
	Spec              IBJobSpec   `json:"spec"`
	Status            IBJobStatus `json:"status,omitempty"`
}

type IBJobSpec struct {
	Resources corev1.ResourceRequirements `json:"resources,omitempty" protobuf:"bytes,8,opt,name=resources"`
    Env []corev1.EnvVar `json:"env,omitempty" patchStrategy:"merge" patchMergeKey:"name" protobuf:"bytes,7,rep,name=env"`
    Services []IBJobService `json:"services,omitempty"`
}

type IBJobService struct {
	APIVersion string `json:"apiVersion"`
	Kind string `json:"kind"`
    Metadata IBJobServiceMetadata `json:"metadata"`
}

type IBJobServiceMetadata struct {
    Name string `json:"name"`
    Labels map[string]string `json:"labels,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object
type IBService struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Status ServiceStatus `json:"status,omitempty"`
}

type ServiceStatus struct {
	Status string `json:"status,omitempty"`
    Message string `json:"message,omitempty"`
}

type JobStateWaiting struct {
    Message string `json:"message,omitempty" protobuf:"bytes,2,opt,name=message"`
}

type JobStateRunning struct {
    StartTime *metav1.Time `json:"startTime,omitempty" protobuf:"bytes,2,opt,name=startTime"`
    CompletionTime *metav1.Time `json:"completionTime,omitempty" protobuf:"bytes,3,opt,name=completionTime"`
}

type JobStateFinalizing struct {
	Phase string `json:"phase,omitempty"`
}

type JobStateTerminated struct {
	ExitCode int32 `json:"exitCode" protobuf:"varint,1,opt,name=exitCode"`
	Message string `json:"message,omitempty" protobuf:"bytes,4,opt,name=message"`
}

type JobState struct {
	Waiting 	*JobStateWaiting `json:"waiting,omitempty"`
	Running 	*JobStateRunning `json:"running,omitempty"`
	Finalizing  *JobStateFinalizing `json:"finalizing,omitempty"`
	Terminated 	*JobStateTerminated `json:"terminated,omitempty"`
}

type IBJobStatus struct {
	State JobState `json:"state,omitempty" protobuf:"bytes,2,opt,name=state"`
}
