package utils

import (
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/common"
	"testing"
)

func TestNewSecret_FailsOnNilInput(t *testing.T) {
	t.Run("failsOnNilInput", func(t *testing.T) {
		if NewSecret(nil) != nil {
			t.Error("should fail")
		}
	})

	t.Run("namesMatchLabelSpec", func(t *testing.T) {
		c := CreateShootCluster()
		s := NewSecret(c)
		if s == nil {
			t.Error("should not fail")
		}

		if s.GetName() != c.GetLabels()[common.LabelForTargetSecret] {
			t.Fatal("name mismatch")
		} else if s.GetNamespace() != c.GetNamespace() {
			t.Fatal("namespace mismatch")
		}
	})

	t.Run("Data map is nonnil", func(t *testing.T) {
		s := NewSecret(CreateShootCluster())
		if s == nil {
			t.Error("should not fail")
		}

		if s.Data == nil {
			t.Error("map must be set")
		}
	})

	t.Run("label for target secret isn't set", func(t *testing.T) {
		cluster := CreateShootCluster()
		cluster.Labels = make(map[string]string)
		if NewSecret(cluster) != nil {
			t.Error("should fail")
		}
	})
}
