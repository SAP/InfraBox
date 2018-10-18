package utils

import "testing"

func TestCreateDHInfra(t *testing.T) {
	d := CreateShootCluster()

	if d.GetName() == "" {
		t.Fatal("name must be set")
	}
	if d.GetNamespace() == "" {
		t.Fatal("namespace must be set")
	}
}
