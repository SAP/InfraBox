package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type GKECluster struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   GKEClusterSpec   `json:"spec"`
	Status GKEClusterStatus `json:"status"`
}

type GKEClusterSpec struct {
	DiskSize        string `json:"diskSize,omitempty"`
	MachineType     string `json:"machineType,omitempty"`
	EnableNetworkPolicy string `json:"enableNetworkPolicy,omitempty"`
	NumNodes        string `json:"numNodes,omitempty"`
	Preemptible    string `json:"preemptible,omitempty"`
	EnableAutoscaling string `json:"enableAutoscaling,omitempty"`
	MaxNodes string `json:"maxNodes,omitempty"`
	MinNodes string `json:"minNodes,omitempty"`
	Zone string `json:"zone"`
}

type GKEClusterStatus struct {
	Status string `json:"status"`
	Message string `json:"message"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object
type GKEClusterList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`

	Items []GKECluster `json:"items"`
}
