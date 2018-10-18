package utils

import (
	"bytes"
	"fmt"
	"io"
	"io/ioutil"
	"os"

	"github.com/sirupsen/logrus"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

type K8sClientSetCreator interface {
	Create(cfg []byte) (kubernetes.Interface, error)
}

// always returns the same client set. Used for testing
type StaticK8sClientSetFactory struct {
	ClientSet kubernetes.Interface
}

func (f *StaticK8sClientSetFactory) Create([]byte) (kubernetes.Interface, error) {
	return f.ClientSet, nil
}

// Does the real work: Always create a new clientset from the given config
type DynamicK8sK8sClientSetFactory struct {
	tmpFileRootDir string
}

func NewDefaultDynamicK8sK8sClientSetFactory() *DynamicK8sK8sClientSetFactory {
	return &DynamicK8sK8sClientSetFactory{
		tmpFileRootDir: "/dev/shm", // try to store it on a ramdisk. /dev/shm is a ramdisk per default on linux >=  2.6.X
	}
}

func NewDynamicK8sK8sClientSetFactory(tmpFileRootdir string) *DynamicK8sK8sClientSetFactory {
	return &DynamicK8sK8sClientSetFactory{
		tmpFileRootDir: tmpFileRootdir, // try to store it on a ramdisk. /dev/shm is a ramdisk per default on linux >=  2.6.X
	}
}

func (fac *DynamicK8sK8sClientSetFactory) Create(cfg []byte) (kubernetes.Interface, error) {
	tmpfileRootdir := fac.tmpFileRootDir
	if _, err := os.Stat(tmpfileRootdir); err == os.ErrNotExist {
		tmpfileRootdir = os.TempDir()
	}

	k8sCfg, err := BuildK8sConfig(tmpfileRootdir, cfg)
	if err != nil {
		return nil, err
	}

	k8sClient, err := kubernetes.NewForConfig(k8sCfg)
	if err != nil {
		logrus.Errorf("couldn't get k8sClient from config. err: %s", err)
		return nil, err
	}

	return k8sClient, nil
}

func BuildK8sConfig(tmpfileRootdir string, cfg []byte) (*rest.Config, error) {
	f, err := ioutil.TempFile(tmpfileRootdir, "")
	if err != nil {
		logrus.Errorf("Couldn't create temporary file in %s, err: %s", tmpfileRootdir, err)
		return nil, fmt.Errorf("Couldn't create temporary file in %s, err: %s", tmpfileRootdir, err)
	}

	defer f.Close()
	defer os.Remove(f.Name())

	if err := writeKubecfgToFile(cfg, f); err != nil {
		logrus.Errorf("Couldn't write config to file %s, err: %s", f.Name(), err)
		return nil, fmt.Errorf("Couldn't write config to file %s, err: %s", f.Name(), err)
	}

	k8sCfg, err := clientcmd.BuildConfigFromFlags("", f.Name())
	if err != nil {
		logrus.Errorf("Couldn't parse config from file %s, err: %s", f.Name(), err)
		return nil, err
	}

	return k8sCfg, err
}

type SyncWriter interface {
	io.Writer
	Sync() error
}

func writeKubecfgToFile(kubecfg []byte, f SyncWriter) error {
	if err := writeToFile(kubecfg, f); err != nil {
		logrus.Errorf("couldn't write kubecfg file. err: %s", err)
		return err
	}

	if err := f.Sync(); err != nil {
		logrus.Errorf("couldn't sync file, err: %s", err)
		return err
	}

	return nil
}

func writeToFile(kubecfg []byte, f io.Writer) error {
	buf := bytes.NewBuffer(kubecfg)
	if _, err := buf.WriteTo(f); err != nil { // no check for nwritten bytes here because buf.WriteTo guarantees that it writes everything or an err is returned
		return err
	}

	return nil
}
