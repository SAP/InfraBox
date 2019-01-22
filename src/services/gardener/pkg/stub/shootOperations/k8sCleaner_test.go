package shootOperations

import (
	"fmt"
	"strconv"
	"testing"
	"time"

	"github.com/golang/mock/gomock"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/api/extensions/v1beta1"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	k8sFake "k8s.io/client-go/kubernetes/fake"

	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/mocks"
)

func addPersistentVolumeClaim(i int, namespace string, cs *k8sFake.Clientset) corev1.PersistentVolumeClaim {
	claim := &corev1.PersistentVolumeClaim{}
	claim.SetName("claim_" + strconv.Itoa(i))
	claim.SetNamespace(namespace)
	claim.SetUID(types.UID("claim_" + strconv.Itoa(i)))
	setFinalizerAndMarkForDeletion(claim)
	cs.CoreV1().PersistentVolumeClaims(namespace).Create(claim)

	return *claim
}

func addIngress(i int, namespace string, cs *k8sFake.Clientset) v1beta1.Ingress {
	ingress := &v1beta1.Ingress{}
	ingress.SetName("ingress_" + strconv.Itoa(i))
	ingress.SetNamespace(namespace)
	ingress.SetUID(types.UID("ingress_" + strconv.Itoa(i)))
	setFinalizerAndMarkForDeletion(ingress)
	cs.ExtensionsV1beta1().Ingresses(namespace).Create(ingress)

	return *ingress
}

func addPod(i int, namespace string, cs *k8sFake.Clientset) corev1.Pod {
	pod := &corev1.Pod{}
	pod.SetName("pod_" + strconv.Itoa(i))
	pod.SetNamespace(namespace)
	pod.SetUID(types.UID("pod_" + strconv.Itoa(i)))
	setFinalizerAndMarkForDeletion(pod)
	cs.CoreV1().Pods(namespace).Create(pod)

	return *pod
}

func TestDeletePersistentVolumes_FailsOnError(t *testing.T) {
	t.Run("list call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		pvcMock := mocks.NewMockPersistentVolumeInterface(mockCtrl)

		pvcMock.EXPECT().List(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))
		err := cleaner.deletePersistentVolumes(pvcMock)
		require.New(t).Error(err)
	})

	t.Run("update call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		pvcMock := mocks.NewMockPersistentVolumeInterface(mockCtrl)

		pv := corev1.PersistentVolume{}
		fillWithBasicMetadata(&pv, "namespace")
		setFinalizerAndMarkForDeletion(&pv)

		pvcMock.EXPECT().List(gomock.Any()).Return(&corev1.PersistentVolumeList{
			Items: []corev1.PersistentVolume{pv},
		}, nil)

		pvcMock.EXPECT().Update(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))

		err := cleaner.deletePersistentVolumes(pvcMock)
		require.New(t).Error(err)
	})

	t.Run("deletion call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		pvcMock := mocks.NewMockPersistentVolumeInterface(mockCtrl)

		pv := corev1.PersistentVolume{}
		fillWithBasicMetadata(&pv, "namespace")

		pvcMock.EXPECT().List(gomock.Any()).Return(&corev1.PersistentVolumeList{
			Items: []corev1.PersistentVolume{pv},
		}, nil)

		pvcMock.EXPECT().DeleteCollection(gomock.Any(), gomock.Any()).Return(fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))

		err := cleaner.deletePersistentVolumes(pvcMock)
		require.New(t).Error(err)
	})
}

func fillWithBasicMetadata(pv v1.Object, namespace string) {
	pv.SetName("someName")
	pv.SetNamespace(namespace)
	pv.SetUID(types.UID("someUid"))
}

func TestCleanupCluster_IfClusterIsEmpty_ReturnsEmptyCluster(t *testing.T) {
	ns := &corev1.Namespace{}
	ns.SetName("foo")
	cs := k8sFake.NewSimpleClientset(ns)

	cleaner := NewK8sCleaner(cs, logrus.WithField("test", "test"))

	err := cleaner.Cleanup()
	require.New(t).NoError(err)
}

func TestCleanupNamespace_ReturnsErrorIfSomethingFailed(t *testing.T) {
	const namespace = "foonamespace"

	t.Run("failure during pvc cleaning", func(t *testing.T) {
		cs := k8sFake.NewSimpleClientset()
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		pvcMock := addErrorDuringPvcDeletion(mockCtrl)
		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))

		_, err := cleaner.cleanupNamespace(namespace, pvcMock, cs.ExtensionsV1beta1().Ingresses(namespace), cs.CoreV1().Pods(namespace), cs.AppsV1().Deployments(namespace), cs.BatchV1().Jobs(namespace), cs.AppsV1().StatefulSets(namespace))

		require.New(t).Error(err)
	})

	t.Run("failure during ingress cleaning", func(t *testing.T) {
		cs := k8sFake.NewSimpleClientset()
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		ingIfMock := addErrorDuringIngressDeletion(mockCtrl)
		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))

		_, err := cleaner.cleanupNamespace(namespace, cs.CoreV1().PersistentVolumeClaims(namespace), ingIfMock, cs.CoreV1().Pods(namespace), cs.AppsV1().Deployments(namespace), cs.BatchV1().Jobs(namespace), cs.AppsV1().StatefulSets(namespace))

		require.New(t).Error(err)
	})

	t.Run("failure during pod cleaning", func(t *testing.T) {
		cs := k8sFake.NewSimpleClientset()
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		podIfMock := addErrorDuringPodDeletion(mockCtrl)
		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))

		_, err := cleaner.cleanupNamespace(namespace, cs.CoreV1().PersistentVolumeClaims(namespace), cs.ExtensionsV1beta1().Ingresses(namespace), podIfMock, cs.AppsV1().Deployments(namespace), cs.BatchV1().Jobs(namespace), cs.AppsV1().StatefulSets(namespace))

		require.New(t).Error(err)
	})
}

func addErrorDuringIngressDeletion(mockCtrl *gomock.Controller) *mocks.MockIngressInterface {
	ingIfMock := mocks.NewMockIngressInterface(mockCtrl)
	ingIfMock.EXPECT().List(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))
	return ingIfMock
}

func addErrorDuringPvcDeletion(mockCtrl *gomock.Controller) *mocks.MockPersistentVolumeClaimInterface {
	pvcMock := mocks.NewMockPersistentVolumeClaimInterface(mockCtrl)
	pvcMock.EXPECT().List(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))
	return pvcMock
}

func addErrorDuringPodDeletion(mockCtrl *gomock.Controller) *mocks.MockPodInterface {
	podIfMock := mocks.NewMockPodInterface(mockCtrl)
	podIfMock.EXPECT().List(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))
	return podIfMock
}

func TestCleanAllNamespace_DoesNotCleanupInSystemNamespace(t *testing.T) {
	cs := k8sFake.NewSimpleClientset()

	addNamespace := func(name string) {
		ns := &corev1.Namespace{}
		ns.SetName(name)
		cs.CoreV1().Namespaces().Create(ns)
	}

	addNamespace(v1.NamespaceSystem)
	fillupNamespace(v1.NamespaceSystem, cs)

	addNamespace(v1.NamespaceDefault)
	fillupNamespace(v1.NamespaceDefault, cs)

	for i := 0; i < 20; i++ {
		nsName := "ns_" + strconv.Itoa(i)
		addNamespace(nsName)
		fillupNamespace(nsName, cs)
	}

	cleaner := NewK8sCleaner(cs, logrus.WithField("test", "test"))
	err := cleaner.cleanAllNamespaces(cs)
	require.Equal(t, errNotYetClean, err) // first try will report notCleanYet

	pvcList, err := cs.CoreV1().PersistentVolumeClaims(v1.NamespaceSystem).List(v1.ListOptions{})
	assert.NotEqual(t, 0, len(pvcList.Items))
}

func TestCollectResults(t *testing.T) {
	t.Run("for err result return that error", func(t *testing.T) {
		outChan := make(chan *helperResultStruct, 1)
		e := fmt.Errorf("fooerror")
		outChan <- &helperResultStruct{isClean: false, err: e}

		cc := &clusterCleaner{}
		_, err := cc.collectResults(time.Minute, 2, outChan)
		assert.Equal(t, e, err)
	})

	t.Run("for timeout return error", func(t *testing.T) {
		outChan := make(chan *helperResultStruct, 1)

		cc := &clusterCleaner{}
		_, err := cc.collectResults(0, 2, outChan)
		assert.Contains(t, err.Error(), "timeout")
	})
}

func TestCleanAllPvcInNamespace_OnlyClaimCleaninessIfNothingWasDeleted(t *testing.T) {
	const namespace = "namespace"

	t.Run("empty cluster", func(t *testing.T) {
		cs := k8sFake.NewSimpleClientset()

		cleaner := NewK8sCleaner(cs, logrus.WithField("test", "test"))
		isClean, err := cleaner.cleanAllPvcInNamespace(namespace, cs.CoreV1().PersistentVolumeClaims(namespace))
		require.New(t).NoError(err)
		assert.New(t).True(isClean)
	})

	t.Run("filled cluster", func(t *testing.T) {
		cs := k8sFake.NewSimpleClientset()
		fillupNamespace(namespace, cs)
		cleaner := NewK8sCleaner(cs, logrus.WithField("test", "test"))

		isClean, err := cleaner.cleanAllPvcInNamespace(namespace, cs.CoreV1().PersistentVolumeClaims(namespace))
		require.New(t).NoError(err)
		assert.New(t).False(isClean)
	})
}

func TestCleanAllIngresses_OnlyClaimCleaninessIfNothingWasDeleted(t *testing.T) {
	const namespace = "namespace"

	t.Run("empty cluster", func(t *testing.T) {
		cs := k8sFake.NewSimpleClientset()
		cleaner := NewK8sCleaner(cs, logrus.WithField("test", "test"))

		isClean, err := cleaner.cleanAllIngressInNamespace(namespace, cs.ExtensionsV1beta1().Ingresses(namespace))

		require.New(t).NoError(err)
		assert.New(t).True(isClean)
	})

	t.Run("filled cluster", func(t *testing.T) {
		cs := k8sFake.NewSimpleClientset()
		fillupNamespace(namespace, cs)
		cleaner := NewK8sCleaner(cs, logrus.WithField("test", "test"))

		isClean, err := cleaner.cleanAllIngressInNamespace(namespace, cs.ExtensionsV1beta1().Ingresses(namespace))

		require.New(t).NoError(err)
		assert.New(t).False(isClean)
	})
}

func TestCleanAllPvcInNamespace_FailsOnError(t *testing.T) {
	const namespace = "foonamespace"

	t.Run("list call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		pvcMock := addErrorDuringPvcDeletion(mockCtrl)
		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))

		_, err := cleaner.cleanAllPvcInNamespace(namespace, pvcMock)
		require.New(t).Error(err)
	})

	t.Run("update call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		pvcMock := mocks.NewMockPersistentVolumeClaimInterface(mockCtrl)

		claim := corev1.PersistentVolumeClaim{}
		fillWithBasicMetadata(&claim, namespace)
		setFinalizerAndMarkForDeletion(&claim)
		list := []corev1.PersistentVolumeClaim{claim}
		pvcMock.EXPECT().List(gomock.Any()).Return(&corev1.PersistentVolumeClaimList{Items: list}, nil)

		pvcMock.EXPECT().Update(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))
		_, err := cleaner.cleanAllPvcInNamespace(namespace, pvcMock)
		require.New(t).Error(err)
	})

	t.Run("delete call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		pvcMock := mocks.NewMockPersistentVolumeClaimInterface(mockCtrl)

		claim := corev1.PersistentVolumeClaim{}
		fillWithBasicMetadata(&claim, namespace)
		list := []corev1.PersistentVolumeClaim{claim}
		pvcMock.EXPECT().List(gomock.Any()).Return(&corev1.PersistentVolumeClaimList{Items: list}, nil)

		pvcMock.EXPECT().DeleteCollection(gomock.Any(), gomock.Any()).Return(fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))
		_, err := cleaner.cleanAllPvcInNamespace(namespace, pvcMock)
		require.New(t).Error(err)
	})
}

func setFinalizerAndMarkForDeletion(obj v1.Object) {
	obj.SetFinalizers([]string{"foo"})
	deletionTs := time.Now().Add(-(2 * deletionPeriodTolerance))
	obj.SetDeletionTimestamp(&v1.Time{Time: deletionTs})
}

func TestCleanAllIngresses_FailsOnError(t *testing.T) {
	const namespace = "foonamespace"

	t.Run("list call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		ingIfMock := addErrorDuringIngressDeletion(mockCtrl)

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))

		_, err := cleaner.cleanAllIngressInNamespace(namespace, ingIfMock)
		require.New(t).Error(err)
	})

	t.Run("update call fails", func(t *testing.T) { // in case of an existing finalizer
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		ingressMock := mocks.NewMockIngressInterface(mockCtrl)

		ingress := v1beta1.Ingress{}
		fillWithBasicMetadata(&ingress, namespace)
		setFinalizerAndMarkForDeletion(&ingress)
		list := []v1beta1.Ingress{ingress}
		ingressMock.EXPECT().List(gomock.Any()).Return(&v1beta1.IngressList{Items: list}, nil)

		ingressMock.EXPECT().Update(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))
		_, err := cleaner.cleanAllIngressInNamespace(namespace, ingressMock)
		require.New(t).Error(err)
	})

	t.Run("delete call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		ingressMock := mocks.NewMockIngressInterface(mockCtrl)

		ingress := v1beta1.Ingress{}
		fillWithBasicMetadata(&ingress, namespace)
		list := []v1beta1.Ingress{ingress}
		ingressMock.EXPECT().List(gomock.Any()).Return(&v1beta1.IngressList{Items: list}, nil)

		ingressMock.EXPECT().DeleteCollection(gomock.Any(), gomock.Any()).Return(fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))
		_, err := cleaner.cleanAllIngressInNamespace(namespace, ingressMock)
		require.New(t).Error(err)
	})
}

func TestCleanAllPods_FailsOnError(t *testing.T) {
	const namespace = "foonamespace"

	t.Run("list call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		podIfMock := mocks.NewMockPodInterface(mockCtrl)
		podIfMock.EXPECT().List(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))

		_, err := cleaner.cleanAllPodsInNamespace(namespace, podIfMock)
		require.New(t).Error(err)
	})

	t.Run("update call fails", func(t *testing.T) { // in case of an existing finalizer
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		podIfMock := mocks.NewMockPodInterface(mockCtrl)

		pod := corev1.Pod{}
		fillWithBasicMetadata(&pod, namespace)
		setFinalizerAndMarkForDeletion(&pod)
		list := []corev1.Pod{pod}
		podIfMock.EXPECT().List(gomock.Any()).Return(&corev1.PodList{Items: list}, nil)

		podIfMock.EXPECT().Update(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))
		_, err := cleaner.cleanAllPodsInNamespace(namespace, podIfMock)
		require.New(t).Error(err)
	})

	t.Run("delete call fails", func(t *testing.T) {
		mockCtrl := gomock.NewController(t)
		defer mockCtrl.Finish()
		podIfMock := mocks.NewMockPodInterface(mockCtrl)

		pod := corev1.Pod{}
		fillWithBasicMetadata(&pod, namespace)
		list := []corev1.Pod{pod}
		podIfMock.EXPECT().List(gomock.Any()).Return(&corev1.PodList{Items: list}, nil)

		podIfMock.EXPECT().DeleteCollection(gomock.Any(), gomock.Any()).Return(fmt.Errorf("fooerror"))

		cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))
		_, err := cleaner.cleanAllPodsInNamespace(namespace, podIfMock)
		require.New(t).Error(err)
	})
}

func fillupNamespace(namespace string, cs *k8sFake.Clientset) {
	for i := 0; i < 10; i++ {
		addPersistentVolumeClaim(i, namespace, cs)
		addIngress(i, namespace, cs)
		addPod(i, namespace, cs)
	}
}

func TestCleanAllPvcInNamespace_FailsOnListErr(t *testing.T) {
	mockCtrl := gomock.NewController(t)
	defer mockCtrl.Finish()
	pvcMock := mocks.NewMockPersistentVolumeClaimInterface(mockCtrl)

	pvcMock.EXPECT().List(gomock.Any()).Return(nil, fmt.Errorf("fooerror"))

	cleaner := NewK8sCleaner(nil, logrus.WithField("test", "test"))

	_, err := cleaner.cleanAllPvcInNamespace("foo", pvcMock)
	require.New(t).Error(err)
}

func TestCleanup_FailsIfNoNamespacesCanBeRead(t *testing.T) {
	cs := k8sFake.NewSimpleClientset()

	mockCtrl := gomock.NewController(t)
	defer mockCtrl.Finish()

	nsMock := mocks.NewMockNamespaceInterface(mockCtrl)
	nsMock.EXPECT().List(gomock.Any()).Return(nil, fmt.Errorf("foorerror"))

	cc := NewK8sCleaner(cs, logrus.WithField("test", "test"))
	cc.nsIf = nsMock

	err := cc.Cleanup()
	require.Error(t, err)
}

func TestCleanup_FailsIfPersistentVolumeCleanupFails(t *testing.T) {
	cs := k8sFake.NewSimpleClientset()

	mockCtrl := gomock.NewController(t)
	defer mockCtrl.Finish()

	pvMock := mocks.NewMockPersistentVolumeInterface(mockCtrl)
	pvMock.EXPECT().List(gomock.Any()).Return(nil, fmt.Errorf("foorerror"))

	cc := NewK8sCleaner(cs, logrus.WithField("test", "test"))
	cc.pvIf = pvMock

	err := cc.Cleanup()
	require.Error(t, err)
}
