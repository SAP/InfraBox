package shootOperations

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/evanphx/json-patch"
	gardenV1beta1 "github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	"github.com/golang/mock/gomock"
	"github.com/sirupsen/logrus"
	apiErrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/mocks"
)

func TestCreateDeletionConfirmationPatch_NilCfg(t *testing.T) {
	_, err := createDeletionConfirmationJPatch(nil)

	if err == nil {
		t.Fatal("should fail for nil input")
	}
}

func TestCreateDeletionConfirmationPatch_VaildCfgDoesNotLeadToError(t *testing.T) {
	cfg := DefaultAwsConfig()
	p, err := createDeletionConfirmationJPatch(cfg)

	if err != nil {
		t.Fatalf("should not fail for valid input. err: %s", err.Error())
	}

	if p == nil {
		t.Fatal("patch must not be nil")
	}
}

func TestCreateDeletionConfirmationPatch_PatchContainsConfirmation(t *testing.T) {
	cfg := DefaultAwsConfig()
	jcfg, _ := json.Marshal(cfg)

	patch, err := createDeletionConfirmationJPatch(cfg)

	if err != nil {
		t.Fatalf("should not fail for valid input. err: %s", err.Error())
	}

	merged, err := jsonpatch.MergePatch(jcfg, patch)
	if err != nil {
		t.Fatalf("cannot merge patch: %s", err.Error())
	}

	var patched = &gardenV1beta1.Shoot{}
	err = json.Unmarshal(merged, patched)
	if err != nil {
		t.Fatalf("couldn't unmarshal : %s", err.Error())
	}

	if patched.Annotations == nil {
		t.Fatal("no annotation was created")
	} else if v, ok := patched.GetAnnotations()[confirmationAnnotationName]; !ok {
		t.Fatal("no entry 'confirmation.gardener.sapcloud.io/deletion' created. json patch is: ", string(merged))
	} else if v != "true" {
		t.Fatalf("invalid value created: %s", v)
	}
}

func TestCreateDeletionTimestamp_NilCfg(t *testing.T) {
	_, err := createDeletionConfirmationTimestampPatch(nil)

	if err == nil {
		t.Fatal("should fail for nil input")
	}
}

func TestCreateDeletionTimestamp_VaildCfgDoesNotLeadToError(t *testing.T) {
	cfg := DefaultAwsConfig()
	p, err := createDeletionConfirmationTimestampPatch(cfg)

	if err != nil {
		t.Fatalf("should not fail for valid input. err: %s", err.Error())
	}

	if p == nil {
		t.Fatal("patch must not be nil")
	}
}

func TestCreateDeletionTimestamp_PatchContainsTimestamp(t *testing.T) {
	cfg := DefaultAwsConfig()

	now := v1.Now()
	cfg.SetDeletionTimestamp(&now)
	jcfg, _ := json.Marshal(cfg)

	patch, err := createDeletionConfirmationTimestampPatch(cfg)

	if err != nil {
		t.Fatalf("should not fail for valid input. err: %s", err.Error())
	}

	merged, err := jsonpatch.MergePatch(jcfg, patch)
	if err != nil {
		t.Fatalf("cannot merge patch: %s", err.Error())
	}

	var patched = &gardenV1beta1.Shoot{}
	err = json.Unmarshal(merged, patched)
	if err != nil {
		t.Fatalf("couldn't unmarshal : %s", err.Error())
	}

	if patched.Annotations == nil {
		t.Fatal("no annotation was created")
	} else if v, ok := patched.GetAnnotations()["confirmation.gardener.sapcloud.io/deletionTimestamp"]; !ok {
		t.Fatal("no entry 'confirmation.gardener.sapcloud.io/deletion' created")
	} else if v != cfg.GetDeletionTimestamp().Format(time.RFC3339) {
		t.Fatalf("invalid timestamp created: want: %s, have: %s", cfg.GetDeletionTimestamp().String(), v)
	}
}

func TestSetDeletionConfirmation_TriesToPatchShoot(t *testing.T) {
	mockCtrl, simock, shoot := setupMockAndShoot(t)
	defer mockCtrl.Finish()

	simock.EXPECT().Get(shoot.GetName(), gomock.Any()).Return(shoot, nil)
	simock.EXPECT().Patch(shoot.GetName(), types.MergePatchType, gomock.Any()).Return(nil, nil)

	log := logrus.WithField("test", "test")
	if err := setDeletionConfirmation(simock, shoot.GetName(), log); err != nil {
		t.Fatal(err)
	}
}

func setupMockAndShoot(t *testing.T) (*gomock.Controller, *mocks.MockShootInterface, *gardenV1beta1.Shoot) {
	mockCtrl := gomock.NewController(t)
	var simock = mocks.NewMockShootInterface(mockCtrl)
	shoot := DefaultAwsConfig()
	return mockCtrl, simock, shoot
}

func TestSetDeletionConfirmation_ReturnsNotFoundIfShootDoesntExist(t *testing.T) {
	mockCtrl, simock, shoot := setupMockAndShoot(t)
	defer mockCtrl.Finish()

	simock.EXPECT().Get(shoot.GetName(), gomock.Any()).Return(nil, apiErrors.NewNotFound(schema.GroupResource{}, shoot.Name))

	log := logrus.WithField("test", "test")
	if err := setDeletionConfirmation(simock, shoot.GetName(), log); !apiErrors.IsNotFound(err) {
		t.Fatalf("expectes NotFound error, but got: %s", err)
	}
}

func TestSetDeletionTimestampConfirmation_TriesToPatchShoot(t *testing.T) {
	mockCtrl, simock, shoot := setupMockAndShoot(t)
	defer mockCtrl.Finish()

	simock.EXPECT().Get(shoot.GetName(), gomock.Any()).Return(shoot, nil)
	simock.EXPECT().Patch(shoot.GetName(), types.MergePatchType, gomock.Any()).Return(nil, nil)

	if err := setDeletionTimestampConfirmation(simock, shoot.GetName()); err != nil {
		t.Fatal(err)
	}
}

func TestSetDeletionTimestampConfirmation_ReturnsNotFoundIfShootDoesntExist(t *testing.T) {
	mockCtrl, simock, shoot := setupMockAndShoot(t)
	defer mockCtrl.Finish()

	simock.EXPECT().Get(shoot.GetName(), gomock.Any()).Return(nil, apiErrors.NewNotFound(schema.GroupResource{}, shoot.Name))

	if err := setDeletionTimestampConfirmation(simock, shoot.GetName()); !apiErrors.IsNotFound(err) {
		t.Fatalf("expectes NotFound error, but got: %s", err)
	}
}

func TestDeleteShootCluster_TriesToDeleteShoot(t *testing.T) {
	mockCtrl, simock, shoot := setupMockAndShoot(t)
	defer mockCtrl.Finish()

	var shootCluster v1alpha1.ShootCluster
	shootCluster.Status.ClusterName = shoot.GetName()
	log := logrus.WithField("test", "test")

	simock.EXPECT().Get(shoot.GetName(), gomock.Any()).Return(shoot, nil).AnyTimes()
	simock.EXPECT().Patch(shoot.GetName(), types.MergePatchType, gomock.Any()).Return(shoot, nil).Times(2) // two patches because of two different confirmations
	simock.EXPECT().Delete(shoot.GetName(), gomock.Any()).Times(1)

	deleteShootCluster(simock, &shootCluster, log)
}

func TestDeleteShootCluster_DoesNotDeleteIfFirstPatchingFails(t *testing.T) {
	mockCtrl, simock, shoot := setupMockAndShoot(t)
	defer mockCtrl.Finish()

	var shootCluster v1alpha1.ShootCluster
	shootCluster.Status.ClusterName = shoot.GetName()
	log := logrus.WithField("test", "test")

	simock.EXPECT().Get(shoot.GetName(), gomock.Any()).Return(nil, apiErrors.NewNotFound(schema.GroupResource{}, shoot.Name)).AnyTimes()

	deleteShootCluster(simock, &shootCluster, log)
}

func TestDeleteShootCluster_DoesNotApplySecondPatchIfDeleteFails(t *testing.T) {
	mockCtrl, simock, shoot := setupMockAndShoot(t)
	defer mockCtrl.Finish()

	var shootCluster v1alpha1.ShootCluster
	shootCluster.Status.ClusterName = shoot.GetName()
	log := logrus.WithField("test", "test")

	simock.EXPECT().Get(shoot.GetName(), gomock.Any()).Return(shoot, nil).AnyTimes()
	simock.EXPECT().Patch(shoot.GetName(), types.MergePatchType, gomock.Any()).Return(shoot, nil).Times(1)
	simock.EXPECT().Delete(shoot.GetName(), gomock.Any()).Return(apiErrors.NewNotFound(schema.GroupResource{}, shoot.Name))

	deleteShootCluster(simock, &shootCluster, log)
}
