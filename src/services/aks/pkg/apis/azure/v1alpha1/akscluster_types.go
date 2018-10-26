package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// EDIT THIS FILE!  THIS IS SCAFFOLDING FOR YOU TO OWN!
// NOTE: json tags are required.  Any new fields you add must have json tags for the fields to be serialized.

// AKSClusterSpec defines the desired state of AKSCluster
type AKSClusterSpec struct {
	// INSERT ADDITIONAL SPEC FIELDS - desired state of cluster
	// Important: Run "operator-sdk generate k8s" to regenerate code after modifying this file
	DiskSize            int32  `json:"diskSize,omitempty"`
	MachineType         string `json:"machineType,omitempty"`
	NumNodes            int32  `json:"numNodes,omitempty"`
	ClusterVersion      string `json:"clusterVersion,omitempty"`
	Zone                string `json:"zone"`
}

// AKSClusterStatus defines the observed state of AKSCluster
type AKSClusterStatus struct {
	// INSERT ADDITIONAL STATUS FIELD - define observed state of cluster
	// Important: Run "operator-sdk generate k8s" to regenerate code after modifying this file
	Status      string `json:"status,omitempty"`
	Message     string `json:"message,omitempty"`
	ClusterName string `json:"clusterName,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// AKSCluster is the Schema for the aksclusters API
// +k8s:openapi-gen=true
type AKSCluster struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   AKSClusterSpec   `json:"spec,omitempty"`
	Status AKSClusterStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// AKSClusterList contains a list of AKSCluster
type AKSClusterList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []AKSCluster `json:"items"`
}

func init() {
	SchemeBuilder.Register(&AKSCluster{}, &AKSClusterList{})
}
