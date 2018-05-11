package main

import (
	"flag"
	"os/exec"
	"time"

	"github.com/golang/glog"
	kubeinformers "k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
	// Uncomment the following line to load the gcp plugin (only required to authenticate against GKE clusters).
	// _ "k8s.io/client-go/plugin/pkg/client/auth/gcp"

	clientset "github.com/infrabox/infrabox/src/services/gcp/pkg/client/clientset/versioned"
	informers "github.com/infrabox/infrabox/src/services/gcp/pkg/client/informers/externalversions"
	"github.com/infrabox/infrabox/src/services/gcp/pkg/signals"
)

var (
	masterURL         string
	kubeconfig        string
	gcpserviceaccount string
)

func main() {
	flag.Parse()

	// set up signals so we handle the first shutdown signal gracefully
	stopCh := signals.SetupSignalHandler()

	cfg, err := clientcmd.BuildConfigFromFlags(masterURL, kubeconfig)
	if err != nil {
		glog.Fatalf("Error building kubeconfig: %s", err.Error())
	}

	kubeClient, err := kubernetes.NewForConfig(cfg)
	if err != nil {
		glog.Fatalf("Error building kubernetes clientset: %s", err.Error())
	}

	clusterClient, err := clientset.NewForConfig(cfg)
	if err != nil {
		glog.Fatalf("Error building cluster clientset: %s", err.Error())
	}

	if gcpserviceaccount == "" {
		glog.Fatalf("-gcpserviceaccount is required")
	}

	glog.Info("Activating service account")
	authCmd := exec.Command("gcloud", "auth", "activate-service-account", "--key-file", gcpserviceaccount)
	authOut, err := authCmd.Output()
	if err != nil {
		glog.Fatalf(string(authOut))
	}
	glog.Info("Successfully activated service account")

	kubeInformerFactory := kubeinformers.NewSharedInformerFactory(kubeClient, time.Second*30)
	clusterInformerFactory := informers.NewSharedInformerFactory(clusterClient, time.Second*30)

	controller := NewController(kubeClient, clusterClient, kubeInformerFactory, clusterInformerFactory)

	go kubeInformerFactory.Start(stopCh)
	go clusterInformerFactory.Start(stopCh)

	if err = controller.Run(2, stopCh); err != nil {
		glog.Fatalf("Error running controller: %s", err.Error())
	}
}

func init() {
	flag.StringVar(&kubeconfig, "kubeconfig", "", "Path to a kubeconfig. Only required if out-of-cluster.")
	flag.StringVar(&masterURL, "master", "", "The address of the Kubernetes API server. Overrides any value in kubeconfig. Only required if out-of-cluster.")
	flag.StringVar(&gcpserviceaccount, "gcpserviceaccount", "", "Path to the GCP Service account")
}
