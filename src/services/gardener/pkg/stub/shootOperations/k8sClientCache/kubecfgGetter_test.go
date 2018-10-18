package k8sClientCache

import (
	"os"
	"testing"

	"k8s.io/client-go/kubernetes/fake"

	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/common"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/common/testUtils"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/utils"
)

func TestStaticKubecfgGetter_Get(t *testing.T) {
	g := NewStaticKubecfgGetter("foo")
	if s, _ := g.Get(nil); s != "foo" {
		t.Fatal("expected 'foo'")
	}
}

func TestSecretGetter_OnNilInjput_GetReturnsErr(t *testing.T) {
	cfgGetter := NewSecretKubecfgGetter(nil)

	if _, err := cfgGetter.Get(nil); err == nil {
		t.Fatal("expected an error")
	}
}

func TestSecretGetter_OnNonexistingSecret_ReturnsError(t *testing.T) {
	m := testUtils.NewSdkMockBackedByFake(t, fake.NewSimpleClientset())
	cfgGetter := NewSecretKubecfgGetter(m)

	cluster := utils.CreateShootCluster()
	os.Setenv(common.EnvCredentialSecretName, cluster.GetName())
	defer os.Unsetenv(common.EnvCredentialSecretName)

	if _, err := cfgGetter.Get(cluster); err == nil {
		t.Fatal("expected an error")
	}
}

func TestSecretGetter_OnNonexistingEntryInSecret_ReturnsError(t *testing.T) {
	m := testUtils.NewSdkMockBackedByFake(t, fake.NewSimpleClientset())
	cfgGetter := NewSecretKubecfgGetter(m)

	shootCluster := utils.CreateShootCluster()
	s := utils.NewSecret(shootCluster)
	m.Create(s)

	os.Setenv(common.EnvCredentialSecretName, s.GetName())
	defer os.Unsetenv(common.EnvCredentialSecretName)
	if _, err := cfgGetter.Get(shootCluster); err == nil {
		t.Fatal("expected an error")
	}
}

func TestSecretGetter_OnNotSetEnvVariable_ReturnsError(t *testing.T) {
	m := testUtils.NewSdkMockBackedByFake(t, fake.NewSimpleClientset())
	cfgGetter := NewSecretKubecfgGetter(m)

	if _, err := cfgGetter.Get(utils.CreateShootCluster()); err == nil {
		t.Fatal("expected an error")
	}
}

func TestSecretGetter_OnExistingEntryInSecret_ReturnsSecretAndNoError(t *testing.T) {
	m := testUtils.NewSdkMockBackedByFake(t, fake.NewSimpleClientset())
	cfgGetter := NewSecretKubecfgGetter(m)

	shootCluster := utils.CreateShootCluster()
	s := utils.NewSecret(shootCluster)
	cfgData := "foodata"
	s.Data[common.KeyGardenKubectlInSecret] = []byte(cfgData)

	m.Create(s)

	os.Setenv(common.EnvCredentialSecretName, s.GetName())
	defer os.Unsetenv(common.EnvCredentialSecretName)

	if cfg, err := cfgGetter.Get(shootCluster); err != nil {
		t.Fatal("expected an error")
	} else if cfgData != cfg {
		t.Fatal("returned cfg is wrong")
	}
}
