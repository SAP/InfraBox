package shootOperations

import (
	"bytes"
	"fmt"
	"testing"

	"github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	gardenFake "github.com/gardener/gardener/pkg/client/garden/clientset/versioned/fake"
	"github.com/golang/mock/gomock"
	"github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/kubernetes"
	k8sFake "k8s.io/client-go/kubernetes/fake"

	"github.com/sap/infrabox/src/services/garden/pkg/apis/garden/v1alpha1"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/common"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/common/testUtils"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/mocks"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/utils"
)

func TestDeleteSecret_CallsSdkDelete(t *testing.T) {
	mockCtrl, sdkMock := testUtils.CreateMock(t)
	defer mockCtrl.Finish()

	var deletedObject runtime.Object
	sdkMock.EXPECT().Delete(gomock.Any()).Return(nil).Do(func(o runtime.Object) { deletedObject = o.DeepCopyObject() })

	cache := mocks.NewK8sClientCacheMock(k8sFake.NewSimpleClientset(), gardenFake.NewSimpleClientset())
	sop := NewShootOperator(sdkMock, cache, &utils.StaticK8sClientSetFactory{}, logrus.WithField("test", "test"))
	ShootCluster := createShootClusterCr()

	err := sop.deleteSecret(ShootCluster)
	if err != nil {
		t.Fatal(err)
	}

	_, ok := deletedObject.(*corev1.Secret)
	if !ok {
		t.Fatal("called with wrong type. expected secret")
	}
}

func TestDeleteSecret_AnyNonNOTFOUNDErrorIsReturned(t *testing.T) {
	mockCtrl, sdkMock := testUtils.CreateMock(t)
	defer mockCtrl.Finish()

	errToReturn := fmt.Errorf("foo")
	sdkMock.EXPECT().Delete(gomock.Any()).Return(errToReturn)

	cache := mocks.NewK8sClientCacheMock(k8sFake.NewSimpleClientset(), gardenFake.NewSimpleClientset())
	sop := NewShootOperator(sdkMock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))
	ShootCluster := createShootClusterCr()

	err := sop.deleteSecret(ShootCluster)
	if err != errToReturn {
		t.Fatalf("got invalid error. want: '%s'; got: '%s'", errToReturn, err)
	}
}

func TestShootOperator_SecretExists_CorrectlyIndicatesSecretExistence(t *testing.T) {
	mockCtrl, sdkMock := testUtils.CreateMock(t)
	defer mockCtrl.Finish()

	gomock.InOrder(
		sdkMock.EXPECT().Get(gomock.Any()).Return(nil), // first call signals that the secret exists
		sdkMock.EXPECT().Get(gomock.Any()).Return(errors.NewNotFound(schema.GroupResource{"foogroup", "fooResource"}, "name")),
		sdkMock.EXPECT().Get(gomock.Any()).Return(fmt.Errorf("some other error")),
	)

	cache := mocks.NewK8sClientCacheMock(k8sFake.NewSimpleClientset(), gardenFake.NewSimpleClientset())
	sop := NewShootOperator(sdkMock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))

	ShootCluster := createShootClusterCr()
	if _, exists := sop.secretExists(ShootCluster); !exists {
		t.Fatal("first secret should exist!")
	}

	if _, exists := sop.secretExists(ShootCluster); exists {
		t.Fatal("second secret should not exist!")
	}

	if _, exists := sop.secretExists(ShootCluster); exists {
		t.Fatal("second secret should not exist!")
	}
}

func TestSyncSecret_ForNonExistentSecret_NewSecretIsSet(t *testing.T) {
	mockCtrl, sdkMock := testUtils.CreateMock(t)
	defer mockCtrl.Finish()

	gomock.InOrder(
		sdkMock.EXPECT().Get(gomock.Any()).Return(errors.NewNotFound(schema.GroupResource{"foogroup", "fooResource"}, "name")),
		sdkMock.EXPECT().Create(gomock.Any()).Return(nil), // secret should be created
	)

	ShootCluster := createShootClusterCr()
	gK8sCs := createFakeK8sFilledWithKubecfgSecret(ShootCluster, t)
	cache := mocks.NewK8sClientCacheMock(gK8sCs, gardenFake.NewSimpleClientset())
	sop := NewShootOperator(sdkMock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))

	s := createSecretWithKubecfg(ShootCluster, make([]byte, 0))
	sop.syncSecret(ShootCluster, s, cache.Get(ShootCluster))
}

func createSecretWithKubecfg(ShootCluster *v1alpha1.ShootCluster, kubecfg []byte) *corev1.Secret {
	s := utils.NewSecret(ShootCluster)
	s.Data["kubeconfig"] = kubecfg // gardener puts the kubeconfig under the key 'kubeconfig'
	return s
}

func createFakeK8sFilledWithKubecfgSecret(ShootCluster *v1alpha1.ShootCluster, t *testing.T) *k8sFake.Clientset {
	gK8sCs := k8sFake.NewSimpleClientset()
	setKubeconfigSecret(ShootCluster, gK8sCs, t)
	return gK8sCs
}

func setKubeconfigSecret(ShootCluster *v1alpha1.ShootCluster, gK8sCs *k8sFake.Clientset, t *testing.T) {
	s := &corev1.Secret{}
	s.SetName(ShootCluster.Spec.ShootName + ".kubeconfig")
	s.SetNamespace(ShootCluster.Spec.GardenerNamespace)
	s.Data = map[string][]byte{"kubeconfig": []byte("kubeconfig data")}
	if _, err := gK8sCs.CoreV1().Secrets(ShootCluster.Spec.GardenerNamespace).Create(s); err != nil {
		t.Fatal(err)
	}
}

func TestNewSecret_ReturnsNilIfInputIsNil(t *testing.T) {
	if s := newSecret(nil, make([]byte, 0)); s != nil {
		t.Fatal("expected nil")
	}
}

func TestSyncSecret_ForExistentSecretWithDifferentData_ExistentSecretIsUpdated(t *testing.T) {
	mockCtrl, sdkMock := testUtils.CreateMock(t)
	defer mockCtrl.Finish()

	// create old version of secret
	ShootCluster := createShootClusterCr()
	oldSecretStoredInCrSourceCluster := newSecret(ShootCluster, []byte("old secret data"))

	var newStoredVersionOfSecret corev1.Secret
	expectSuccessfulKubecfgGetAndSecretUpdate(sdkMock, oldSecretStoredInCrSourceCluster, &newStoredVersionOfSecret)

	gK8sCs := createFakeK8sFilledWithKubecfgSecret(ShootCluster, t)
	cache := mocks.NewK8sClientCacheMock(gK8sCs, gardenFake.NewSimpleClientset())
	sop := NewShootOperator(sdkMock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))

	shootKubeCfg := []byte("kubeconfig data")
	s := createSecretWithKubecfg(ShootCluster, shootKubeCfg)

	sop.syncSecret(ShootCluster, s, cache.Get(ShootCluster))

	if !bytes.Equal(newStoredVersionOfSecret.Data["config"], shootKubeCfg) {
		t.Fatalf("kubecfg mismatch, got: %v", newStoredVersionOfSecret.Data["config"])
	}
}

func expectSuccessfulKubecfgGetAndSecretUpdate(sdkMock *testUtils.MockSdkOperations, oldSecretStoredInCrSourceCluster *corev1.Secret, newStoredVersionOfSecret *corev1.Secret) {
	gomock.InOrder(
		sdkMock.EXPECT().Get(gomock.Any()).Return(nil).Do(func(s *corev1.Secret) {
			oldSecretStoredInCrSourceCluster.DeepCopyInto(s)
		}),
		sdkMock.EXPECT().Update(gomock.Any()).Return(nil).Do(
			func(s *corev1.Secret) {
				s.DeepCopyInto(newStoredVersionOfSecret)
			},
		), // secret should be updated
	)
}

func expectGetAndUpdateAndReturnErrorOnSecond(sdkMock *testUtils.MockSdkOperations, oldSecretStoredInCrSourceCluster *corev1.Secret, errNotFound *errors.StatusError) {
	gomock.InOrder(
		sdkMock.EXPECT().Get(gomock.Any()).Return(nil).Do(func(s *corev1.Secret) {
			oldSecretStoredInCrSourceCluster.DeepCopyInto(s)
		}),
		sdkMock.EXPECT().Update(gomock.Any()).Return(errNotFound),
	)
}

func TestSyncSecret_ForNonexistentSecret_IfCreateFails_NewStateIsError(t *testing.T) {
	mockCtrl, sdkMock := testUtils.CreateMock(t)
	defer mockCtrl.Finish()

	gomock.InOrder(
		sdkMock.EXPECT().Get(gomock.Any()).Return(errors.NewNotFound(schema.GroupResource{"foogroup", "fooResource"}, "name")),
		sdkMock.EXPECT().Create(gomock.Any()).Return(errors.NewBadRequest("foo reason")),
	)

	ShootCluster := createShootClusterCr()
	gK8sCs := createFakeK8sFilledWithKubecfgSecret(ShootCluster, t)
	cache := mocks.NewK8sClientCacheMock(gK8sCs, gardenFake.NewSimpleClientset())
	sop := NewShootOperator(sdkMock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))
	s := createSecretWithKubecfg(ShootCluster, make([]byte, 0))

	sop.syncSecret(ShootCluster, s, cache.Get(ShootCluster))

	if ShootCluster.Status.Status != v1alpha1.ShootClusterStateError {
		t.Fatal("expected error state, but got: ", ShootCluster.Status.Status)
	}
}

func TestSyncSecret_ForExistentSecret_IfUpdateFails_NewStateIsError(t *testing.T) {
	mockCtrl, sdkMock := testUtils.CreateMock(t)
	defer mockCtrl.Finish()

	// create old version of secret
	ShootCluster := createShootClusterCr()
	oldSecretStoredInCrSourceCluster := newSecret(ShootCluster, []byte("old secret data"))
	errNotFound := errors.NewNotFound(schema.GroupResource{"foogroup", "fooResource"}, "name")
	expectGetAndUpdateAndReturnErrorOnSecond(sdkMock, oldSecretStoredInCrSourceCluster, errNotFound)

	gK8sCs := createFakeK8sFilledWithKubecfgSecret(ShootCluster, t)
	cache := mocks.NewK8sClientCacheMock(gK8sCs, gardenFake.NewSimpleClientset())
	sop := NewShootOperator(sdkMock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))

	s := createSecretWithKubecfg(ShootCluster, make([]byte, 0))

	sop.syncSecret(ShootCluster, s, cache.Get(ShootCluster))

	if ShootCluster.Status.Status != v1alpha1.ShootClusterStateError {
		t.Fatal("expected error state, but got: ", ShootCluster.Status.Status)
	}
}

func TestShootOperator_SimpleSyncForEmptyCluster(t *testing.T) {
	k8sCs := k8sFake.NewSimpleClientset()
	mock := testUtils.NewSdkMockBackedByFake(t, k8sCs)
	gFake := gardenFake.NewSimpleClientset()
	cache := mocks.NewK8sClientCacheMock(k8sCs, gFake)
	sop := NewShootOperator(mock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))

	ShootCluster := createShootClusterCr()
	addInputSecretForDHInfraOperator(ShootCluster, mock)
	addCloudProfileForAws(ShootCluster, gFake, t)

	err := sop.Sync(ShootCluster)
	if err != nil {
		t.Fatal(err)
	}

	storedCluster := &v1alpha1.ShootCluster{}
	ShootCluster.DeepCopyInto(storedCluster)
	if err := mock.Get(storedCluster); err != nil {
		t.Fatal(err)
	}

	// shoot cluster isn't ready (we didn't set its state accordingly) => state also musn't be ready
	if storedCluster.Status.Status == v1alpha1.ShootClusterStateReady {
		t.Fatalf("wrong state. cluster shouldn't be ready, but got: %s", storedCluster.Status.Status)
	}
}

func TestShootOperator_Sync_ChangedDHInfraResultsInUpdate(t *testing.T) {
	k8sCs, mock, gFake := setupMocks(t)

	dhInfraInput := createShootClusterCr()
	addReadyShootCluster(dhInfraInput, k8sCs, gFake, mock, t)

	cache := mocks.NewK8sClientCacheMock(k8sCs, gFake)
	sop := NewShootOperator(mock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))

	dhInfraWithUpdate := dhInfraInput.DeepCopy()
	dhInfraWithUpdate.Spec.MaxNodes++
	dhInfraWithUpdate.Spec.MinNodes++

	if err := sop.Sync(dhInfraWithUpdate); err != nil {
		t.Fatal(err)
	}

	shoot, err := gFake.GardenV1beta1().Shoots(dhInfraWithUpdate.Spec.GardenerNamespace).Get(dhInfraWithUpdate.Spec.ShootName, v1.GetOptions{})
	if err != nil {
		t.Fatal(err)
	}

	// compare shoot spec with dhInfra specs
	if got := shoot.Spec.Cloud.AWS.Workers[0].AutoScalerMin; got != int(dhInfraWithUpdate.Spec.MinNodes) {
		t.Fatalf("min nodes mismatch. got: %d, want: %d", got, dhInfraWithUpdate.Spec.MinNodes)
	}
	if got := shoot.Spec.Cloud.AWS.Workers[0].AutoScalerMax; got != int(dhInfraWithUpdate.Spec.MaxNodes) {
		t.Fatalf("max nodes mismatch. got: %d, want: %d", got, dhInfraWithUpdate.Spec.MaxNodes)
	}
}

func setupMocks(t *testing.T) (*k8sFake.Clientset, *testUtils.SdkMockStateful, *gardenFake.Clientset) {
	k8sCs := k8sFake.NewSimpleClientset()
	mock := testUtils.NewSdkMockBackedByFake(t, k8sCs)
	gFake := gardenFake.NewSimpleClientset()
	return k8sCs, mock, gFake
}

func addReadyShootCluster(dhInfraInput *v1alpha1.ShootCluster, k8sFake kubernetes.Interface, gFake *gardenFake.Clientset, sdkops common.SdkOperations, t *testing.T) {
	if err := addInputSecretForDHInfraOperator(dhInfraInput, sdkops); err != nil {
		t.Fatal(err)
	}

	addSecretContainingShootKubeCfg(dhInfraInput, k8sFake, t)
	addCloudProfileForAws(dhInfraInput, gFake, t)

	shoot, err := createAwsConfig(sdkops, dhInfraInput, gFake.GardenV1beta1().CloudProfiles())
	if err != nil {
		t.Fatal(err)
	}
	shoot.Status.LastOperation = &v1beta1.LastOperation{
		Progress: 100,
		State:    v1beta1.ShootLastOperationStateSucceeded,
		Type:     v1beta1.ShootLastOperationTypeReconcile,
	}

	if _, err := gFake.GardenV1beta1().Shoots(dhInfraInput.Spec.GardenerNamespace).Create(shoot); err != nil {
		t.Fatal(err)
	}
}

func addCloudProfileForAws(dhInfraInput *v1alpha1.ShootCluster, gFake *gardenFake.Clientset, t *testing.T) {
	p := &v1beta1.CloudProfile{
		TypeMeta: v1.TypeMeta{
			Kind:       "CloudProfile",
			APIVersion: "garden.sapcloud.io/v1beta1",
		},
		Spec: v1beta1.CloudProfileSpec{
			AWS: &v1beta1.AWSProfile{
				Constraints: v1beta1.AWSConstraints{
					Kubernetes: v1beta1.KubernetesConstraints{
						Versions: []string{dhInfraInput.Spec.ClusterVersion},
					},
				},
			},
		},
	}

	p.SetName("aws")
	if _, err := gFake.GardenV1beta1().CloudProfiles().Create(p); err != nil {
		t.Fatal(err)
	}
}

func addSecretContainingShootKubeCfg(dhInfraInput *v1alpha1.ShootCluster, k8sFake kubernetes.Interface, t *testing.T) {
	s := utils.NewSecret(dhInfraInput)
	sName := dhInfraInput.Spec.ShootName + ".kubeconfig"
	s.SetName(sName)
	s.SetNamespace(dhInfraInput.Spec.GardenerNamespace)
	s.Data["kubeconfig"] = []byte(utils.ValidDummyKubeconfig())
	if _, err := k8sFake.CoreV1().Secrets(dhInfraInput.Spec.GardenerNamespace).Create(s); err != nil {
		t.Fatal(err)
	}
}

func removeSecretContainingShootKubeCfg(dhInfraInput *v1alpha1.ShootCluster, k8sFake kubernetes.Interface, t *testing.T) {
	sName := dhInfraInput.Spec.ShootName + ".kubeconfig"
	if err := k8sFake.CoreV1().Secrets(dhInfraInput.Spec.GardenerNamespace).Delete(sName, &v1.DeleteOptions{}); err != nil {
		t.Fatal(err)
	}
}

func addInputSecretForDHInfraOperator(dhInfraInput *v1alpha1.ShootCluster, sdkmock common.SdkOperations) error {
	s := utils.NewSecret(dhInfraInput)
	s.Data[common.KeySecretBindingRefInSecret] = []byte("foo")
	return sdkmock.Create(s)
}

func TestShootOperator_Sync_OnReconcilingShoot_DHInfraState_NumNodesDoesNotGetUpdated(t *testing.T) {
	k8sCs, mock, gFake := setupMocks(t)

	dhInfraInput := createShootClusterCr()
	addReconcilingShootCluster(dhInfraInput, k8sCs, gFake, mock, t)
	sop := NewShootOperator(mock, mocks.NewK8sClientCacheMock(k8sCs, gFake), &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))

	if err := sop.Sync(dhInfraInput); err != nil {
		t.Fatal(err)
	}

	if dhInfraInput.Status.NumNodes != 0 {
		t.Fatalf("wrong NumNodes. expected %d, got: %d", 0, dhInfraInput.Status.NumNodes)
	}
}

func addReconcilingShootCluster(dhInfraInput *v1alpha1.ShootCluster, k8sFake kubernetes.Interface, gFake *gardenFake.Clientset, sdkops common.SdkOperations, t *testing.T) {
	if err := addInputSecretForDHInfraOperator(dhInfraInput, sdkops); err != nil {
		t.Fatal(err)
	}

	addSecretContainingShootKubeCfg(dhInfraInput, k8sFake, t)
	addCloudProfileForAws(dhInfraInput, gFake, t)

	shoot, err := createAwsConfig(sdkops, dhInfraInput, gFake.GardenV1beta1().CloudProfiles())
	if err != nil {
		t.Fatal(err)
	}
	shoot.Status.LastOperation = &v1beta1.LastOperation{
		Progress: 50,
		State:    v1beta1.ShootLastOperationStateProcessing,
		Type:     v1beta1.ShootLastOperationTypeReconcile,
	}

	if _, err := gFake.GardenV1beta1().Shoots(dhInfraInput.Spec.GardenerNamespace).Create(shoot); err != nil {
		t.Fatal(err)
	}
}

func TestShootOperator_Sync_DHInfraState_NumNodesGetsUpdated(t *testing.T) {
	k8sCs := k8sFake.NewSimpleClientset()
	mock := testUtils.NewSdkMockBackedByFake(t, k8sCs)
	gFake := gardenFake.NewSimpleClientset()

	const numNodes = 4217
	dhInfraInput := createShootClusterCr()
	dhInfraInput.Spec.MinNodes = numNodes
	dhInfraInput.Spec.MaxNodes = numNodes

	addReadyShootCluster(dhInfraInput, k8sCs, gFake, mock, t)
	sop := NewShootOperator(mock, mocks.NewK8sClientCacheMock(k8sCs, gFake), &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))

	if err := sop.Sync(dhInfraInput); err != nil {
		t.Fatal(err)
	}

	if dhInfraInput.Status.NumNodes != numNodes {
		t.Fatalf("wrong NumNodes. expected %d, got: %d", numNodes, dhInfraInput.Status.NumNodes)
	}
}

func TestUpdateShootSpecIfNecessary(t *testing.T) {
	cache := mocks.NewK8sClientCacheMock(nil, nil)
	sop := NewShootOperator(nil, cache, nil, nil)

	dhInfra := createShootClusterCr()
	shoot := DefaultAwsConfig()

	if !sop.updateShootSpecIfNecessary(shoot, dhInfra) {
		t.Fatal("multiple values don't match, therefore there must be an update")
	}

	worker := shoot.Spec.Cloud.AWS.Workers[0]
	if worker.AutoScalerMin != int(dhInfra.Spec.MinNodes) {
		t.Fatalf("value mismatch. expected: %d, got: %d", dhInfra.Spec.MinNodes, worker.AutoScalerMin)
	}
	if worker.AutoScalerMax != int(dhInfra.Spec.MaxNodes) {
		t.Fatalf("value mismatch. expected: %d, got: %d", dhInfra.Spec.MaxNodes, worker.AutoScalerMax)
	}
	if expVolSize := fmt.Sprintf("%dGi", dhInfra.Spec.DiskSize); worker.VolumeSize != expVolSize {
		t.Fatalf("value mismatch. expected: %s, got: %s", expVolSize, worker.VolumeSize)
	}
}

func TestShootOperator_IfSecretIsMissing_SyncFails(t *testing.T) {
	_, sop := setupMinimalTestEnv(t)

	ShootCluster := createShootClusterCr()

	err := sop.Sync(ShootCluster)
	if err == nil {
		t.Fatal("secret does not contain bindingRef => shoot creation should fail")
	}
}

func TestShootOperator_IfSecretIsIncomplete_SyncFails(t *testing.T) {
	mock, sop := setupMinimalTestEnv(t)

	ShootCluster := createShootClusterCr()
	addIncompleteSecret(ShootCluster, mock)

	err := sop.Sync(ShootCluster)
	if err == nil {
		t.Fatal("secret does not contain bindingRef => shoot creation should fail")
	}
}

func setupMinimalTestEnv(t *testing.T) (*testUtils.SdkMockStateful, *ShootOperator) {
	k8sCs := k8sFake.NewSimpleClientset()
	mock := testUtils.NewSdkMockBackedByFake(t, k8sCs)
	cache := mocks.NewK8sClientCacheMock(k8sCs, gardenFake.NewSimpleClientset())
	sop := NewShootOperator(mock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))
	return mock, sop
}

func addIncompleteSecret(ShootCluster *v1alpha1.ShootCluster, mock *testUtils.SdkMockStateful) {
	s := utils.NewSecret(ShootCluster)
	mock.Create(s)
}

func TestShootOperator_IfShootCfgIsMissing_SyncFails(t *testing.T) {
	k8sCs, mock, gFake := setupMocks(t)

	dhInfraInput := createShootClusterCr()
	addReadyShootClusterButMissingShootKubeCfg(dhInfraInput, k8sCs, gFake, mock, t)

	cache := mocks.NewK8sClientCacheMock(k8sCs, gFake)
	sop := NewShootOperator(mock, cache, &utils.StaticK8sClientSetFactory{ClientSet: k8sFake.NewSimpleClientset()}, logrus.WithField("test", "test"))

	if err := sop.Sync(dhInfraInput); err == nil {
		t.Fatal("expected an error since the shoot kubeconfig does not exist")
	}
}

func addReadyShootClusterButMissingShootKubeCfg(dhInfraInput *v1alpha1.ShootCluster, k8sFake kubernetes.Interface, gFake *gardenFake.Clientset, sdkops common.SdkOperations, t *testing.T) {
	addReadyShootCluster(dhInfraInput, k8sFake, gFake, sdkops, t)
	removeSecretContainingShootKubeCfg(dhInfraInput, k8sFake, t)
}
