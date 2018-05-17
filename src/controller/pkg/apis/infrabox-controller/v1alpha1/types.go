package v1alpha1

import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type IBJob struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   JobSpec   `json:"spec"`
	Status JobStatus `json:"status"`
}

type JobSpec struct {
	Resources corev1.ResourceRequirements `json:"resources,omitempty" protobuf:"bytes,8,opt,name=resources"`
    Env []corev1.EnvVar `json:"env,omitempty" patchStrategy:"merge" patchMergeKey:"name" protobuf:"bytes,7,rep,name=env"`
    Services []IBJobService `json:"services,omitempty"`
}

type IBJobService struct {
	APIVersion string `json:"apiVersion"`
	Kind string `json:"kind"`
    Metadata IBJobServiceMetadata `json:"metadata"`
	Spec map[string]string `json:"spec,omitempty"`
}

type IBJobServiceMetadata struct {
    Name string `json:"name"`
    Labels map[string]string `json:"labels,omitempty"`
}

type IBService struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Status ServiceStatus `json:"status,omitempty"`
}

type ServiceStatus struct {
	Status string `json:"status,omitempty"`
    Message string `json:"message,omitempty"`
}

type JobStatus struct {
	Status string `json:"status,omitempty"`
	Message string `json:"message,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object
type IBJobList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`

	Items []IBJob `json:"items"`
}
