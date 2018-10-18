package shootOperations

import (
	"github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	"testing"
)

func TestReadycheck_NoLastOperation(t *testing.T) {
	shoot := v1beta1.Shoot{}
	if isShootReady(&shoot) == true {
		t.Fatal("Shoot without last operation is not ready!")
	}
}

func TestReadycheck_SuccessfulCreate(t *testing.T) {
	shoot := v1beta1.Shoot{}
	shoot.Status.LastOperation = &v1beta1.LastOperation{
		Type:  v1beta1.ShootLastOperationTypeCreate,
		State: v1beta1.ShootLastOperationStateSucceeded,
	}

	if !isShootReady(&shoot) {
		t.Fatal("create was successfull -> must be consideres as ready")
	}
}

func TestReadycheck_FailedCreate(t *testing.T) {
	shoot := v1beta1.Shoot{}
	shoot.Status.LastOperation = &v1beta1.LastOperation{
		Type:  v1beta1.ShootLastOperationTypeCreate,
		State: v1beta1.ShootLastOperationStateFailed,
	}

	if isShootReady(&shoot) {
		t.Fatal("create failed -> must be consideres as failed")
	}
}

func TestReadycheck_ProcessingCreate(t *testing.T) {
	shoot := v1beta1.Shoot{}
	shoot.Status.LastOperation = &v1beta1.LastOperation{
		Type:  v1beta1.ShootLastOperationTypeCreate,
		State: v1beta1.ShootLastOperationStateProcessing,
	}

	if isShootReady(&shoot) {
		t.Fatal("create still is being processed -> must be consideres as failed")
	}
}

func TestReadycheck_SuccessfulReconcile(t *testing.T) {
	shoot := v1beta1.Shoot{}
	shoot.Status.LastOperation = &v1beta1.LastOperation{
		Type:  v1beta1.ShootLastOperationTypeReconcile,
		State: v1beta1.ShootLastOperationStateSucceeded,
	}

	if !isShootReady(&shoot) {
		t.Fatal("reconcile always must be considered as 'cluster ready'")
	}
}

func TestReadycheck_FailedReconcile(t *testing.T) {
	shoot := v1beta1.Shoot{}
	shoot.Status.LastOperation = &v1beta1.LastOperation{
		Type:  v1beta1.ShootLastOperationTypeReconcile,
		State: v1beta1.ShootLastOperationStateFailed,
	}

	if !isShootReady(&shoot) {
		t.Fatal("reconcile always must be considered as 'cluster ready'")
	}
}

func TestReadycheck_Delete(t *testing.T) {
	shoot := v1beta1.Shoot{}
	shoot.Status.LastOperation = &v1beta1.LastOperation{
		Type:  v1beta1.ShootLastOperationTypeDelete,
		State: v1beta1.ShootLastOperationStateProcessing,
	}

	if isShootReady(&shoot) {
		t.Fatal("delete always must be considered as 'cluster isn't'")
	}
}

func TestIsShootReconciling_DetectsReconcile(t *testing.T) {
	testCases := []struct {
		name     string
		expected bool
		shoot    *v1beta1.Shoot
	}{
		{
			"runningReconcile",
			true,
			&v1beta1.Shoot{Status: v1beta1.ShootStatus{LastOperation: &v1beta1.LastOperation{Type: v1beta1.ShootLastOperationTypeReconcile, State: v1beta1.ShootLastOperationStateProcessing}}},
		},
		{
			"finishedReconcile",
			false,
			&v1beta1.Shoot{Status: v1beta1.ShootStatus{LastOperation: &v1beta1.LastOperation{Type: v1beta1.ShootLastOperationTypeReconcile, State: v1beta1.ShootLastOperationStateSucceeded}}},
		},
		{
			"failedReconcile",
			false,
			&v1beta1.Shoot{Status: v1beta1.ShootStatus{LastOperation: &v1beta1.LastOperation{Type: v1beta1.ShootLastOperationTypeReconcile, State: v1beta1.ShootLastOperationStateFailed}}},
		},
		{
			"pendingReconcile",
			false,
			&v1beta1.Shoot{Status: v1beta1.ShootStatus{LastOperation: &v1beta1.LastOperation{Type: v1beta1.ShootLastOperationTypeReconcile, State: v1beta1.ShootLastOperationStatePending}}},
		},
		{
			"creating",
			false,
			&v1beta1.Shoot{Status: v1beta1.ShootStatus{LastOperation: &v1beta1.LastOperation{Type: v1beta1.ShootLastOperationTypeCreate, State: v1beta1.ShootLastOperationStateProcessing}}},
		},
		{
			"creatingFinished",
			false,
			&v1beta1.Shoot{Status: v1beta1.ShootStatus{LastOperation: &v1beta1.LastOperation{Type: v1beta1.ShootLastOperationTypeCreate, State: v1beta1.ShootLastOperationStateSucceeded}}},
		},
		{
			"creatingFailed",
			false,
			&v1beta1.Shoot{Status: v1beta1.ShootStatus{LastOperation: &v1beta1.LastOperation{Type: v1beta1.ShootLastOperationTypeCreate, State: v1beta1.ShootLastOperationStateFailed}}},
		},
		{
			"deleting",
			false,
			&v1beta1.Shoot{Status: v1beta1.ShootStatus{LastOperation: &v1beta1.LastOperation{Type: v1beta1.ShootLastOperationTypeDelete, State: v1beta1.ShootLastOperationStateProcessing}}},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			if got := isShootReconciling(tc.shoot); got != tc.expected {
				t.Fatalf("failed for test %s. got: %t, wanted: %t", tc.name, got, tc.expected)
			}
		})
	}
}
