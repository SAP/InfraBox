package k8sClientCache

import (
	"bytes"
	"fmt"
	"io"
	"testing"

	gardenFake "github.com/gardener/gardener/pkg/client/garden/clientset/versioned/fake"
	k8sFake "k8s.io/client-go/kubernetes/fake"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/utils"
)

func TestClientGetter(t *testing.T) {
	cg := clientGetter{nil, nil}
	if cg.GetK8sClientSet() != nil {
		t.Fail()
	}
	if cg.GetK8sClientSet() != nil {
		t.Fail()
	}

	cg = clientGetter{k8sFake.NewSimpleClientset(), gardenFake.NewSimpleClientset()}
	if cg.GetK8sClientSet() != cg.k8sClient {
		t.Fail()
	}
	if cg.GetGardenClientSet() != cg.gardenK8sClient {
		t.Fail()
	}
}

func TestClientCache_cancreate(t *testing.T) {
	confGetter := &StaticKubecfgGetter{config: ""}
	_ = NewClientCache(confGetter)
}

const testKubecfgYaml = `apiVersion: v1
clusters:
- cluster:
    certificate-authority-data:
      "Zm9vCg=="
    server: https://api.blue.gardener.canary.k8s.ondemand.com:443
  name: canary
contexts:
- context:
    cluster: canary
    user: api-user
  name: canary-context
current-context: canary-context
kind: Config
preferences: {}
users:
- name: api-user
  user:
    token:
      Zm9vCg==
`

func TestClientCache_GetsClients(t *testing.T) {
	confGetter := &StaticKubecfgGetter{config: testKubecfgYaml}
	cc := NewClientCache(confGetter)

	if cgetter := cc.Get(utils.CreateShootCluster()); cgetter == nil {
		t.Fatal("expected nonnil")
	}
}

func TestClientCache_ForInvalidKubeCfg_Fails(t *testing.T) {
	confGetter := &StaticKubecfgGetter{config: ""}
	cc := NewClientCache(confGetter)

	if cgetter := cc.Get(utils.CreateShootCluster()); cgetter != nil {
		t.Fatal("expected failure")
	}
}

func TestClientCache_CachesClients(t *testing.T) {
	confGetter := &StaticKubecfgGetter{config: testKubecfgYaml}
	cc := NewClientCache(confGetter)

	firstCGetter := cc.Get(utils.CreateShootCluster())
	if firstCGetter == nil {
		t.Fatal("expected nonnil")
	}

	secondCGetter := cc.Get(utils.CreateShootCluster())
	if secondCGetter == nil {
		t.Fatal("expected nonnil")
	}

	if firstCGetter != secondCGetter {
		t.Fatal("client getter wasn't cached")
	}
}

type dummyWriter struct{}

func (w *dummyWriter) Write([]byte) (n int, err error) { return 0, io.ErrClosedPipe }

func writeToFile(kubecfg string, f io.Writer) error {
	buf := bytes.NewBufferString(kubecfg)
	nBytesToWrite := buf.Len()
	if n, err := buf.WriteTo(f); (err != nil) || (n != int64(nBytesToWrite)) {
		if err != nil {
			return err
		} else {
			return fmt.Errorf("expected to write %d bytes, but wrote %d", nBytesToWrite, n)
		}
	}

	return nil
}

func TestWriteToFile_OnIncompleteWrite_ReturnsError(t *testing.T) {
	data := "foo"
	if err := writeToFile(data, &dummyWriter{}); err == nil {
		t.Fatal("expected error")
	}
}

func TestClientCache_OnFailingCfgGetter_GetAlsoFails(t *testing.T) {
	confGetter := &failingKubecfgGetter{}
	cc := NewClientCache(confGetter)

	if cgetter := cc.Get(utils.CreateShootCluster()); cgetter != nil {
		t.Fatal("expected failure")
	}
}

type failingKubecfgGetter struct{}

func (g *failingKubecfgGetter) Get(cluster *v1alpha1.ShootCluster) (string, error) {
	return "", fmt.Errorf("fooerror")
}
