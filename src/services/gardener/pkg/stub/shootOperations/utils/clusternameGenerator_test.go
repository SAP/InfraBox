package utils

import (
	"os"
	"strings"
	"testing"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
)

func TestCreateUniqueShootName_NameStartsWithPrefix(t *testing.T) {
	list := &v1alpha1.ShootClusterList{
		Items: make([]v1alpha1.ShootCluster, 0),
	}

	name := CreateUniqueClusterName(list)

	if !strings.Contains(name, clusterNamePrefix) {
		t.Fatalf("generated name must start with '%s'", clusterNamePrefix)
	}
	if name[:len(clusterNamePrefix)] != clusterNamePrefix {
		t.Fatalf("generated name must start with '%s'", clusterNamePrefix)
	}
}

func TestCreateUniqueShootName_NameLength(t *testing.T) {
	list := &v1alpha1.ShootClusterList{
		Items: make([]v1alpha1.ShootCluster, 0),
	}

	const maxNameLength = 21 - len(projectName)
	for i := 0; i < 100; i++ {
		name := CreateUniqueClusterName(list)

		if l := len(name); l != maxNameLength {
			t.Fatalf("name length plus length of project name (%s) must not exceed 21 chars => max name length is %d, but actually is %d long", projectName, maxNameLength, l)
		}
	}
}

func TestCreateUniqueShootName_NoNameCollisions(t *testing.T) {
	list := &v1alpha1.ShootClusterList{
		Items: make([]v1alpha1.ShootCluster, 0),
	}

	givenNames := make(map[string]struct{})

	for i := 0; i < 1000; i++ {
		name := CreateUniqueClusterName(list)

		if _, exists := givenNames[name]; exists {
			t.Fatalf("Name %s already given", name)
		} else {
			givenNames[name] = struct{}{}
			list.Items = append(list.Items, v1alpha1.ShootCluster{
				Status: v1alpha1.ShootClusterStatus{ClusterName: name},
			})
		}
	}
}

func TestCreateUniqueShootName_RespectsPROJECTEnvVar(t *testing.T) {
	const newProjectName = "fooproject"
	env := map[string]string{
		"GARDENER_PROJECTNAME": newProjectName,
	}

	resetEnv := updateEnvAndReturnResetFunc(env)
	defer resetEnv()

	list := &v1alpha1.ShootClusterList{
		Items: make([]v1alpha1.ShootCluster, 0),
	}

	const maxNameLength = 21 - len(newProjectName)
	for i := 0; i < 100; i++ {
		name := CreateUniqueClusterName(list)

		if l := len(name); l != maxNameLength {
			t.Fatalf("name length plus length of project name (%s) must not exceed 21 chars => max name length is %d, but actually is %d long", newProjectName, maxNameLength, l)
		}
	}
}

func updateEnvAndReturnResetFunc(env map[string]string) func() {
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
	for k, newVal := range env {
		os.Setenv(k, newVal)
	}
	return resetEnv
}
