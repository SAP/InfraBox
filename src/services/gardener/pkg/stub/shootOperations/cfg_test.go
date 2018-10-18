package shootOperations

import (
	"fmt"
	"os"
	"strings"
	"testing"

	"github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	"github.com/golang/mock/gomock"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/mocks"
)

func TestFillSpecWK8sVer_Failures(t *testing.T) {
	t.Run("version too big", func(t *testing.T) {
		k8sVersionWanted := "1.30"
		supportedVersions := []string{"1.11.2", "1.9.1", "1.10.8"}
		testInvalidK8sVersionRequirements(supportedVersions, k8sVersionWanted, t)
	})

	t.Run("version too small", func(t *testing.T) {
		k8sVersionWanted := "1.1"
		supportedVersions := []string{"1.11.2", "1.9.1", "1.10.8"}
		testInvalidK8sVersionRequirements(supportedVersions, k8sVersionWanted, t)
	})

	t.Run("no supported versions", func(t *testing.T) {
		k8sVersionWanted := "1.10"
		supportedVersions := []string{}
		testInvalidK8sVersionRequirements(supportedVersions, k8sVersionWanted, t)
	})
}

func testInvalidK8sVersionRequirements(supportedVersions []string, k8sVersionWanted string, t *testing.T) {
	mockCtrl, cpMock := setupMocksForCloudProfile(t)
	defer mockCtrl.Finish()
	shootCluster, shoot := expectCallAndCreateStructs(supportedVersions, cpMock, k8sVersionWanted)

	err := fillSpecWithK8sVersion(shoot, shootCluster, cpMock)

	if err == nil {
		t.Fatal("expected err, but got none")
	}
}

func setupMocksForCloudProfile(t *testing.T) (*gomock.Controller, *mocks.MockCloudProfileInterface) {
	mockCtrl := gomock.NewController(t)
	cpMock := mocks.NewMockCloudProfileInterface(mockCtrl)
	return mockCtrl, cpMock
}

func TestFillSpecWK8sVer_OnBogusExpectedVersion_Fail(t *testing.T) {
	mockCtrl, cpMock := setupMocksForCloudProfile(t)
	defer mockCtrl.Finish()

	shootCluster := createShootClusterCr()
	shoot := DefaultAwsConfig()
	shootCluster.Spec.ClusterVersion = "fasdfasd"

	err := fillSpecWithK8sVersion(shoot, shootCluster, cpMock)

	if err == nil {
		t.Fatal("expected err, but got none")
	}
}

func TestFillSpecWK8sVer_Successes(t *testing.T) {
	t.Run("version fits 1", func(t *testing.T) {
		k8sVersionWanted := "1.9"
		k8sVersionExpected := "1.9.1"
		supportedVersions := []string{"1.11.2", "1.9.1", "1.10.8"}
		testValidK8sVersionRequirements(supportedVersions, k8sVersionWanted, k8sVersionExpected, t)
	})

	t.Run("version fits 2", func(t *testing.T) {
		k8sVersionWanted := "1.11"
		k8sVersionExpected := "1.11.2"
		supportedVersions := []string{"1.11.2", "1.9.1", "1.10.8"}
		testValidK8sVersionRequirements(supportedVersions, k8sVersionWanted, k8sVersionExpected, t)
	})

	t.Run("can handle full semver", func(t *testing.T) {
		k8sVersionWanted := "1.11.2"
		k8sVersionExpected := "1.11.2"
		supportedVersions := []string{"1.11.2", "1.9.1", "1.10.8"}
		testValidK8sVersionRequirements(supportedVersions, k8sVersionWanted, k8sVersionExpected, t)
	})

	t.Run("updates full semver", func(t *testing.T) {
		k8sVersionWanted := "1.11.1"
		k8sVersionExpected := "1.11.2"
		supportedVersions := []string{"1.11.2", "1.9.1", "1.10.8"}
		testValidK8sVersionRequirements(supportedVersions, k8sVersionWanted, k8sVersionExpected, t)
	})

	t.Run("downgrades full semver", func(t *testing.T) {
		k8sVersionWanted := "1.11.8"
		k8sVersionExpected := "1.11.2"
		supportedVersions := []string{"1.11.2", "1.9.1", "1.10.8"}
		testValidK8sVersionRequirements(supportedVersions, k8sVersionWanted, k8sVersionExpected, t)
	})

	t.Run("tolerates bogus supported version", func(t *testing.T) {
		k8sVersionWanted := "1.9.1"
		k8sVersionExpected := "1.9.1"
		supportedVersions := []string{"a.b.c", "1.9.1", "foo"}
		testValidK8sVersionRequirements(supportedVersions, k8sVersionWanted, k8sVersionExpected, t)
	})
}

func testValidK8sVersionRequirements(supportedVersions []string, k8sVersionWanted string, expVersion string, t *testing.T) {
	mockCtrl, cpMock := setupMocksForCloudProfile(t)
	defer mockCtrl.Finish()
	shootCluster, shoot := expectCallAndCreateStructs(supportedVersions, cpMock, k8sVersionWanted)
	err := fillSpecWithK8sVersion(shoot, shootCluster, cpMock)

	if err != nil {
		t.Fatal(err)
	}

	if expVersion != shoot.Spec.Kubernetes.Version {
		t.Fatal("version mismatch")
	}
}

func expectCallAndCreateStructs(supportedVersions []string, cpMock *mocks.MockCloudProfileInterface, k8sVersionWanted string) (*v1alpha1.ShootCluster, *v1beta1.Shoot) {
	shoot := DefaultAwsConfig()
	shootCluster := createShootClusterCr()
	p := &v1beta1.CloudProfile{
		Spec: v1beta1.CloudProfileSpec{
			AWS: &v1beta1.AWSProfile{
				Constraints: v1beta1.AWSConstraints{
					Kubernetes: v1beta1.KubernetesConstraints{
						Versions: supportedVersions,
					},
				},
			},
		},
	}
	cpMock.EXPECT().Get(gomock.Any(), gomock.Any()).Return(p, nil)
	shootCluster.Spec.ClusterVersion = k8sVersionWanted
	return shootCluster, shoot
}

func TestFillSpecWK8sVer_IfCloudProfileIsntAvailable_Fail(t *testing.T) {
	mockCtrl, cpMock := setupMocksForCloudProfile(t)
	defer mockCtrl.Finish()

	shootCluster, shoot := createShootClusterCr(), DefaultAwsConfig()
	cpMock.EXPECT().Get(gomock.Any(), gomock.Any()).Return(nil, fmt.Errorf("fooerror"))

	err := fillSpecWithK8sVersion(shoot, shootCluster, cpMock)

	if err == nil {
		t.Fatal("expected err, but got none")
	}
}

func TestFillSpecFromEnv(t *testing.T) {
	shoot := DefaultAwsConfig()
	shoot.Spec.Maintenance = nil

	env := map[string]string{
		ENVDnsDomainSuffix:               "fooDNS",
		ENVAwsMaintenanceAutoupdate:      "false",
		ENVAwsMaintenanceAutoUpdateBegin: "100000+0100",
		ENVAwsMaintenanceAutoUpdateEnd:   "120000+0100",
		ENVSecretBindingRef:              "secrBindingRef",
	}

	oldEnv := make(map[string]string, len(env))
	for k := range env {
		if v, exists := os.LookupEnv(k); exists {
			oldEnv[k] = v
		}
	}
	resetEnv := func() {
		for k := range env {
			if oldVal, existedBefore := oldEnv[k]; existedBefore {
				os.Setenv(k, oldVal)
			} else {
				os.Unsetenv(k)
			}
		}
	}
	defer resetEnv()

	for k, newVal := range env {
		os.Setenv(k, newVal)
	}

	fillSpecFromEnv(shoot)

	if !strings.HasSuffix(*shoot.Spec.DNS.Domain, env[ENVDnsDomainSuffix]) {
		t.Fatalf("dns domain wasn't used from env. have: %s", *shoot.Spec.DNS.Domain)
	}

	if shoot.Spec.Maintenance.AutoUpdate.KubernetesVersion == true {
		t.Fatal("autoupdate of maintenance kubernetes version should be false")
	}
	if shoot.Spec.Maintenance.TimeWindow.Begin != env[ENVAwsMaintenanceAutoUpdateBegin] {
		t.Fatal("time window begin mismatch")
	}
	if shoot.Spec.Maintenance.TimeWindow.End != env[ENVAwsMaintenanceAutoUpdateEnd] {
		t.Fatal("time window end mismatch")
	}
	if shoot.Spec.Cloud.SecretBindingRef.Name != env[ENVSecretBindingRef] {
		t.Fatal("secret binding ref mismatch")
	}
}
