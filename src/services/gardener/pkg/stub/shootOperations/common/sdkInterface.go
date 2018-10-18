package common

import (
	"k8s.io/apimachinery/pkg/runtime"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

type SdkOperations interface {
	Create(o runtime.Object) error
	Update(o runtime.Object) error
	Delete(o runtime.Object, opts ...interface{}) error
	Get(o runtime.Object) error
	List(namespace string, o runtime.Object) error
	WithDeleteOptions(metaDeleteOptions *metav1.DeleteOptions) interface{}
}
