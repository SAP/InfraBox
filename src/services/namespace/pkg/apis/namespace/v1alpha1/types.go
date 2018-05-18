package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    apiv1 "k8s.io/api/core/v1"
)

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type ClusterNamespaceList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`
	Items           []ClusterNamespace `json:"items"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type ClusterNamespace struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata"`
	Spec              ClusterNamespaceSpec   `json:"spec"`
	Status            ClusterNamespaceStatus `json:"status,omitempty"`
}

type ClusterNamespaceSpec struct {
    ResourceQuota apiv1.ResourceQuotaSpec `json:"resourceQuota,omitempty" protobuf:"bytes,2,opt,name=resourceQuota"`
}

type ClusterNamespaceStatus struct {
	Status string `json:"status"`
	Message string `json:"message"`
}
