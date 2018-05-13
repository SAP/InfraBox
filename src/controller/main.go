package main

import (
	"flag"
	"time"

	"github.com/golang/glog"
	clientset "github.com/infrabox/infrabox/src/controller/pkg/client/clientset/versioned"
	informers "github.com/infrabox/infrabox/src/controller/pkg/client/informers/externalversions"
	"github.com/infrabox/infrabox/src/controller/pkg/signals"
	kubeinformers "k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
)

var (
	masterURL  string
	kubeconfig string
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

	kubeInformerFactory := kubeinformers.NewSharedInformerFactory(kubeClient, time.Second*30)
	clusterInformerFactory := informers.NewSharedInformerFactory(clusterClient, time.Second*30)

	controller := NewController(kubeClient, clusterClient, kubeInformerFactory, clusterInformerFactory, cfg)

	go kubeInformerFactory.Start(stopCh)
	go clusterInformerFactory.Start(stopCh)

	if err = controller.Run(2, stopCh); err != nil {
		glog.Fatalf("Error running controller: %s", err.Error())
	}
}

func init() {
	flag.StringVar(&kubeconfig, "kubeconfig", "", "Path to a kubeconfig. Only required if out-of-cluster.")
	flag.StringVar(&masterURL, "master", "", "The address of the Kubernetes API server. Overrides any value in kubeconfig. Only required if out-of-cluster.")
}
