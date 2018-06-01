package v1alpha1

import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	//"k8s.io/api/core/v1"
)

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type IBPipelineList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`
	Items           []IBPipeline `json:"items"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type IBPipeline struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata"`
	Spec              IBPipelineSpec `json:"spec"`
}

type IBPipelineSpec struct {
	Steps []IBPipelineStep `json:"steps"`
}

type IBPipelineStep struct {
	Name         string `json:"name"`
	FunctionName string `json:"functionName"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type WorkflowList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`
	Items           []Workflow `json:"items"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type Workflow struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata"`
	Spec              WorkflowSpec   `json:"spec"`
	Status            WorkflowStatus `json:"status"`
}

type WorkflowStatus struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

type WorkflowSpec struct {
	Pipelines []IBPipelineDefinitionSpec `json:"pipelines"`
}

type IBPipelineDefinitionSpec struct {
	Name string `json:"name"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type IBPipelineInvocationList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`
	Items           []IBPipelineInvocation `json:"items"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type IBPipelineInvocation struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata"`
	Spec              IBPipelineInvocationSpec   `json:"spec"`
	Status            IBPipelineInvocationStatus `json:"status"`
}

type IBPipelineInvocationStatus struct {
	State          string                       `json:"state"`
	Message        string                       `json:"message"`
	StartTime      *metav1.Time                 `json:"startTime,omitempty" protobuf:"bytes,2,opt,name=startTime"`
	CompletionTime *metav1.Time                 `json:"completionTime,omitempty" protobuf:"bytes,3,opt,name=completionTime"`
	StepStatuses   []IBFunctionInvocationStatus `json:"stepStatuses,omitempty"`
}

type IBPipelineInvocationSpec struct {
	PipelineName string                              `json:"pipelineName"`
	Steps        map[string]IBPipelineInvocationStep `json:"steps"`
	Services     []IBPipelineService                 `json:"services,omitempty"`
}

type IBPipelineService struct {
	APIVersion string                    `json:"apiVersion"`
	Kind       string                    `json:"kind"`
	Metadata   IBPipelineServiceMetadata `json:"metadata"`
}

type IBPipelineServiceMetadata struct {
	Name        string            `json:"name"`
	Labels      map[string]string `json:"labels,omitempty"`
	Annotations map[string]string `json:"annotations,omitempty"`
}

type IBPipelineInvocationStep struct {
	Name      string
	Env       []corev1.EnvVar              `json:"env,omitempty" patchStrategy:"merge" patchMergeKey:"name" protobuf:"bytes,7,rep,name=env"`
	Resources *corev1.ResourceRequirements `json:"resources,omitempty" protobuf:"bytes,8,opt,name=resources"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type IBFunctionInvocationList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata"`
	Items           []IBFunctionInvocationList `json:"items"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

type IBFunctionInvocation struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata"`
	Spec              IBFunctionInvocationSpec   `json:"spec"`
	Status            IBFunctionInvocationStatus `json:"status"`
}

type IBFunctionInvocationStatus struct {
	State corev1.ContainerState
}

type IBFunctionInvocationSpec struct {
	FunctionName string                       `json:"functionName"`
	Env          []corev1.EnvVar              `json:"env,omitempty" patchStrategy:"merge" patchMergeKey:"name" protobuf:"bytes,7,rep,name=env"`
	VolumeMounts []corev1.VolumeMount         `json:"volumeMounts,omitempty" patchStrategy:"merge" patchMergeKey:"mountPath" protobuf:"bytes,9,rep,name=volumeMounts"`
	Resources    *corev1.ResourceRequirements `json:"resources,omitempty" protobuf:"bytes,8,opt,name=resources"`
	Volumes      []corev1.Volume              `json:"volumes,omitempty" patchStrategy:"merge,retainKeys" patchMergeKey:"name" protobuf:"bytes,1,rep,name=volumes"`
}
