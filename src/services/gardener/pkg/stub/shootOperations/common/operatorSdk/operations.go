package operatorSdk

import (
	"github.com/operator-framework/operator-sdk/pkg/sdk/action"
	"github.com/operator-framework/operator-sdk/pkg/sdk/query"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
)

/*
 Simple struct used to decouple operations code from operator-sdk code. Necessary for easier testing because
 operator-sdk code has init() functions which assume that the process runs in a pod.
*/
type Operations struct{}

func (s *Operations) Create(o runtime.Object) error { return action.Create(o) }
func (s *Operations) Update(o runtime.Object) error { return action.Update(o) }
func (s *Operations) Delete(o runtime.Object, opts ...interface{}) error {
	result := make([]action.DeleteOption, len(opts))
	for i, v := range opts {
		result[i] = v.(action.DeleteOption)
	}
	return action.Delete(o, result...)

}
func (s *Operations) Get(o runtime.Object) error                    { return query.Get(o) }
func (s *Operations) List(namespace string, o runtime.Object) error { return query.List(namespace, o) }
func (s *Operations) WithDeleteOptions(metaDeleteOptions *v1.DeleteOptions) interface{} {
	return action.WithDeleteOptions(metaDeleteOptions)
}
