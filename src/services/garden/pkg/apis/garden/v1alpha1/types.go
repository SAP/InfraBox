package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const (
	ShootClusterStateCreating   = "creating"
	ShootClusterStateShootReady = "shoot ready"
	ShootClusterStateReady      = "ready"
	ShootClusterStateDeleting   = "deleting"
	ShootClusterStateError      = "error"
)

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type ShootCluster struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   ShootClusterSpec   `json:"spec"`
	Status ShootClusterStatus `json:"status"`
}

type ShootClusterSpec struct {
	DiskSize          int32  `json:"diskSize,omitempty"`
	MachineType       string `json:"machineType,omitempty"`
	NumNodes          int32  `json:"numNodes,omitempty"`
	EnableAutoscaling bool   `json:"enableAutoscaling,omitempty"`
	MaxNodes          int32  `json:"maxNodes,omitempty"`
	MinNodes          int32  `json:"minNodes,omitempty"`
	ClusterVersion    string `json:"clusterVersion,omitempty"`
	Zone              string `json:"zone"`
}

type ShootClusterStatus struct {
	Status            string `json:"status,omitempty"`
	Message           string `json:"message,omitempty"`
	SecretName        string `json:"clusterName,omitempty"`
	NumNodes          int    `json:"numNodes,omitempty"`
	ClusterName       string `json:"shootName,omitempty"`
	GardenerNamespace string `json:"gardenerNamespace,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object
type ShootClusterList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`

	Items []ShootCluster `json:"items"`
}
