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
        DiskSize                   int32  `json:"diskSize,omitempty"`
        MachineType                string `json:"machineType,omitempty"`
        EnableNetworkPolicy        bool   `json:"enableNetworkPolicy,omitempty"`
        DisableLegacyAuthorization bool   `json:"disableLegacyAuthorization,omitempty"`
        EnablePodSecurityPolicy    bool   `json:"enablePodSecurityPolicy,omitempty"`
        NumNodes                   int32  `json:"numNodes,omitempty"`
        Preemptible                bool   `json:"preemptible,omitempty"`
        EnableAutoscaling          bool   `json:"enableAutoscaling,omitempty"`
        MaxNodes                   int32  `json:"maxNodes,omitempty"`
        MinNodes                   int32  `json:"minNodes,omitempty"`
        ClusterVersion             string `json:"clusterVersion,omitempty"`
        Zone                       string `json:"zone"`
        ServiceCidr                string `json:"serviceCidr,omitempty"`
        ClusterCidr                string `json:"clusterCidr,omitempty"`
}

type GKEClusterStatus struct {
        Status         string `json:"status,omitempty"`
        Message        string `json:"message,omitempty"`
        ClusterName    string `json:"clusterName,omitempty"`
        FirstCleanedAt string `json:"firstCleanedAt,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object
type GKEClusterList struct {
        metav1.TypeMeta `json:",inline"`
        metav1.ListMeta `json:"metadata"`

        Items []GKECluster `json:"items"`
}
