package testUtils

import (
	"reflect"
	"testing"

	batchv1 "k8s.io/api/batch/v1"
	"k8s.io/api/batch/v1beta1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/kubernetes"

	shootCluster "github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
)

// NewSdkMockBackedByFake creates a new sdk mock, which keeps state and uses k8s for known CRs. Note that the
// implementation doesn't perform all checks a full kubernetes would do. For example, for an update, a k8s would check
// if the resourceVersion of the stored object matches the version of the new version.
func NewSdkMockBackedByFake(t *testing.T, k8sCs kubernetes.Interface) *SdkMockStateful {
	return &SdkMockStateful{
		t:    t,
		cs:   k8sCs,
		omap: make(map[string]runtime.Object),
	}
}

// SdkMockStateful sdk operator mock that creates, updates, gets and deletes CRs. Note that the implementation doesn't
// perform all checks a full kubernetes would do. For example, for an update, a k8s would check if the resourceVersion
// of the stored object matches the version of the new version.
type SdkMockStateful struct {
	t    *testing.T
	cs   kubernetes.Interface
	omap map[string]runtime.Object
}

type interfaceCr interface {
	GroupVersionKind() schema.GroupVersionKind
	GetNamespace() string
	GetName() string
	GetFinalizers() []string
}

func hash(object interfaceCr) string {
	gkv := object.GroupVersionKind()
	return object.GetName() + object.GetNamespace() + gkv.Kind + gkv.Group + gkv.Version
}

func deepCopy(from runtime.Object, to runtime.Object) {
	switch source := from.(type) {
	case *shootCluster.ShootCluster:
		switch destination := to.(type) {
		case *shootCluster.ShootCluster:
			source.DeepCopyInto(destination)
		}
	case *corev1.Secret:
		switch destination := to.(type) {
		case *corev1.Secret:
			source.DeepCopyInto(destination)
		}
	case *batchv1.Job:
		switch destination := to.(type) {
		case *batchv1.Job:
			source.DeepCopyInto(destination)
		}
	case *v1beta1.CronJob:
		switch destination := to.(type) {
		case *v1beta1.CronJob:
			source.DeepCopyInto(destination)
		}
	}
}

// Create creates the CR
func (m *SdkMockStateful) Create(o runtime.Object) error {
	switch object := o.(type) {
	case *corev1.Secret:
		_, err := m.cs.CoreV1().Secrets(object.GetNamespace()).Create(object)
		return err
	case *batchv1.Job:
		_, err := m.cs.BatchV1().Jobs(object.GetNamespace()).Create(object)
		return err
	case *v1beta1.CronJob:
		_, err := m.cs.BatchV1beta1().CronJobs(object.GetNamespace()).Create(object)
		return err
	case interfaceCr:
		key := hash(object)
		m.omap[key] = o.DeepCopyObject()
		m.t.Log("adding " + reflect.TypeOf(o).String() + " with hash " + key)
		return nil
	default:
		m.t.Fatalf("unexpected type during create: %v", o.GetObjectKind())
	}
	return nil
}

// Update updates the CR
func (m *SdkMockStateful) Update(o runtime.Object) error {
	switch object := o.(type) {
	case *corev1.Secret:
		_, err := m.cs.CoreV1().Secrets(object.GetNamespace()).Update(object)
		return err
	case *batchv1.Job:
		_, err := m.cs.BatchV1().Jobs(object.GetNamespace()).Update(object)
		return err
	case *v1beta1.CronJob:
		_, err := m.cs.BatchV1beta1().CronJobs(object.GetNamespace()).Update(object)
		return err
	case interfaceCr:
		key := hash(object)
		m.omap[key] = o.DeepCopyObject()
		m.t.Log("update " + reflect.TypeOf(o).String() + " with hash " + key)
		return nil
	default:
		m.t.Fatalf("unexpected type during update: %v", o.GetObjectKind())
	}
	return nil
}

// Delete deletes the CR
func (m *SdkMockStateful) Delete(o runtime.Object, opts ...interface{}) error {
	switch object := o.(type) {
	case *corev1.Secret:
		return m.cs.CoreV1().Secrets(object.GetNamespace()).Delete(object.GetName(), &v1.DeleteOptions{})
	case *batchv1.Job:
		return m.cs.BatchV1().Jobs(object.GetNamespace()).Delete(object.GetName(), &v1.DeleteOptions{})
	case *v1beta1.CronJob:
		return m.cs.BatchV1beta1().CronJobs(object.GetNamespace()).Delete(object.GetName(), &v1.DeleteOptions{})
	case interfaceCr:
		key := hash(object)
		if storedObj, ok := m.omap[key]; ok {
			storedCr, _ := storedObj.(interfaceCr)
			if fin := storedCr.GetFinalizers(); (fin != nil) && (len(fin) != 0) {
				m.t.Log("skipping delete " + reflect.TypeOf(o).String() + " with hash " + key + " because finalizers are set")
				return nil
			}
			m.t.Log("delete " + reflect.TypeOf(o).String() + " with hash " + key)
			delete(m.omap, key)
		}
		return nil
	default:
		m.t.Fatalf("unexpected type during delete: %v", o.GetObjectKind())
		return nil
	}
	return nil
}

// Get returns the CR
func (m *SdkMockStateful) Get(o runtime.Object) error {
	var retrievedObject runtime.Object
	switch object := o.(type) {
	case *corev1.Secret:
		if obj, err := m.cs.CoreV1().Secrets(object.GetNamespace()).Get(object.GetName(), v1.GetOptions{}); err != nil {
			m.t.Log("did not find secret with name " + object.GetName())
			return err
		} else {
			retrievedObject = obj
		}
	case *batchv1.Job:
		if obj, err := m.cs.BatchV1().Jobs(object.GetNamespace()).Get(object.GetName(), v1.GetOptions{}); err != nil {
			m.t.Log("did not find job with name " + object.GetName())
			return err
		} else {
			retrievedObject = obj
		}
	case *v1beta1.CronJob:
		if obj, err := m.cs.BatchV1beta1().CronJobs(object.GetNamespace()).Get(object.GetName(), v1.GetOptions{}); err != nil {
			m.t.Log("did not find job with name " + object.GetName())
			return err
		} else {
			retrievedObject = obj
		}
	case interfaceCr:
		key := hash(object)
		m.t.Log("get " + reflect.TypeOf(o).String() + " with hash " + key)
		obj, ok := m.omap[key]
		if !ok {
			r := schema.GroupResource{
				Group:    object.GroupVersionKind().Group,
				Resource: "don't care",
			}
			m.t.Log("did not find " + reflect.TypeOf(object).String() + " with key " + key)
			return errors.NewNotFound(r, object.GetName())
		} else {
			retrievedObject = obj
		}
	default:
		m.t.Fatalf("unexpected type during get: %v", o.GetObjectKind())
		return nil
	}
	deepCopy(retrievedObject, o)
	return nil
}

// List returns nothing
func (m *SdkMockStateful) List(namespace string, o runtime.Object) error {
	return nil
}

// WithDeleteOptions does nothing
func (m *SdkMockStateful) WithDeleteOptions(metaDeleteOptions *metav1.DeleteOptions) interface{} {
	return nil
}
