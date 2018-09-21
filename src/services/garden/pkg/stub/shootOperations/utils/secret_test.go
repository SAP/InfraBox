package utils

import "testing"

func TestNewSecret_FailsOnNilInput(t *testing.T) {
	t.Run("failsOnNilInput", func(t *testing.T) {
		if NewSecret(nil) != nil {
			t.Error("should fail")
		}
	})

	t.Run("namesMatchCluster", func(t *testing.T) {
		c := CreateShootCluster()
		s := NewSecret(c)
		if s == nil {
			t.Error("should not fail")
		}

		if s.GetName() != c.GetName() {
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

}
