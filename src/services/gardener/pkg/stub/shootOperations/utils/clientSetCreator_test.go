package utils

import (
	"io"
	"testing"

	"k8s.io/client-go/kubernetes/fake"
)

func TestStaticK8sClientSetFactory_Create(t *testing.T) {
	s := StaticK8sClientSetFactory{ClientSet: fake.NewSimpleClientset()}

	if tmp, err := s.Create(nil); err != nil {
		t.Fatal(err)
	} else if tmp != s.ClientSet {
		t.Fatal("mismatch")
	}
}

func TestDynamicFactory_Create_OnInvalidCfg_ReturnsErr(t *testing.T) {
	tests := []struct {
		name string
		cfg  []byte
	}{
		{"nil", nil},
		{"empty", []byte("")},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {

			fac := DynamicK8sK8sClientSetFactory{}
			if _, err := fac.Create(test.cfg); err == nil {
				t.Fatal("expected error, but got none")
			}
		})
	}
}

func TestDynamicFactory_Create_OnValidCfg_ReturnsClient(t *testing.T) {

	fac := NewDefaultDynamicK8sK8sClientSetFactory()

	if cs, err := fac.Create([]byte(ValidDummyKubeconfig())); err != nil {
		t.Fatal(err)
	} else if cs == nil {
		t.Fatal("valid cs must not be nil")
	}

}

func TestDynamicFactory_Create_OnInValidTempDir_Fails(t *testing.T) {
	fac := NewDynamicK8sK8sClientSetFactory("/fasdfa/fdasa/sdaf/sfd/sfd")

	if _, err := fac.Create([]byte(ValidDummyKubeconfig())); err == nil {
		t.Fatal("expected error")
	}
}

type failingWriter struct {
	nSuccessfulBytes int
}

func (f *failingWriter) Write(p []byte) (n int, err error) {
	return f.nSuccessfulBytes, io.ErrClosedPipe
}

func TestWriteToFile_FailsIfWriteFails(t *testing.T) {
	cfg := []byte("foo")
	if err := writeToFile(cfg, &failingWriter{nSuccessfulBytes: 0}); err == nil {
		t.Fatal("expected error")
	}

	if err := writeToFile(cfg, &failingWriter{nSuccessfulBytes: 1}); err == nil {
		t.Fatal("expected error")
	}
}

type writeFailer struct{} // fulfills the interface SyncWriter

func (w *writeFailer) Sync() error { return nil }
func (w *writeFailer) Write(p []byte) (n int, err error) {
	return 0, io.ErrClosedPipe
}

type syncFailer struct{} // fulfills the interface SyncWriter

func (w *syncFailer) Sync() error { return io.ErrClosedPipe }
func (w *syncFailer) Write(p []byte) (n int, err error) {
	return len(p), nil
}

func TestWriteKubecfgToFile_FailureBahavior(t *testing.T) {
	t.Run("fails if write fails", func(t *testing.T) {
		if err := writeKubecfgToFile([]byte("foo"), &writeFailer{}); err == nil {
			t.Fatal("expected error")
		}
	})

	t.Run("fails if sync fails", func(t *testing.T) {
		if err := writeKubecfgToFile([]byte("foo"), &syncFailer{}); err == nil {
			t.Fatal("expected error")
		}
	})
}
