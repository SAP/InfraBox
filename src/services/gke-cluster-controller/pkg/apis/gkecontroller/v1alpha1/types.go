package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type Cluster struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   ClusterSpec   `json:"spec"`
	Status ClusterStatus `json:"status"`
}

type ClusterSpec struct {
	DiskSize        int `json:"diskSize,omitempty"`
	MachineType     string `json:"machineType,omitempty"`
	EnableNetworkPolicy bool `json:"enableNetworkPolicy,omitempty"`
	NumNodes        int     `json:"numNodes,omitempty"`
	Preemptible    bool `json:"preemptible,omitempty"`
	EnableAutoscaling bool `json:"enableAutoscaling,omitempty"`
	MaxNodes int `json:"maxNodes,omitempty"`
	MinNodes int `json:"minNodes,omitempty"`
	Infrabox InfraBoxSpec `json:"infrabox"`
}

type InfraBoxSpec struct {
	SecretName string `json:"SecretName"`
}

type InfraBoxStatus struct {
	Status string `json:"status"`
	Message string `json:"message"`
}

type ClusterStatus struct {
	Status string `json:"status"`
    Infrabox InfraBoxStatus `json:"infrabox"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object
type ClusterList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`

	Items []Cluster `json:"items"`
}
