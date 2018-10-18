package main

import (
	"encoding/json"
	"context"
	"runtime"
	"os/exec"
	"io/ioutil"

	stub "github.com/sap/infrabox/src/services/gcp/pkg/stub"
	sdk "github.com/operator-framework/operator-sdk/pkg/sdk"
	k8sutil "github.com/operator-framework/operator-sdk/pkg/util/k8sutil"
	sdkVersion "github.com/operator-framework/operator-sdk/version"

	"github.com/sirupsen/logrus"
)

func printVersion() {
	logrus.Infof("Go Version: %s", runtime.Version())
	logrus.Infof("Go OS/Arch: %s/%s", runtime.GOOS, runtime.GOARCH)
	logrus.Infof("operator-sdk Version: %v", sdkVersion.Version)
}

func main() {
	printVersion()

    gcpserviceaccount := "/var/run/infrabox.net/gcp/service_account.json"

	logrus.Info("Activating GCP service account")
	authCmd := exec.Command("gcloud", "auth", "activate-service-account", "--key-file", gcpserviceaccount)
	authOut, err := authCmd.CombinedOutput()
	if err != nil {
		logrus.Fatalf(string(authOut))
	}

	logrus.Info("Setting GCP Project")
	raw, err := ioutil.ReadFile(gcpserviceaccount)

	if err != nil {
		logrus.Fatalf(err.Error())
	}

	var sa map[string]interface{}
	json.Unmarshal(raw, &sa)

	projectId := sa["project_id"].(string)
	authCmd = exec.Command("gcloud", "config", "set", "core/project", projectId)
	authOut, err = authCmd.CombinedOutput()
	if err != nil {
		logrus.Fatalf(string(authOut))
	}


	resource := "gcp.service.infrabox.net/v1alpha1"
	kind := "GKECluster"
	namespace, err := k8sutil.GetWatchNamespace()
	if err != nil {
		logrus.Fatalf("Failed to get watch gcp: %v", err)
	}
	resyncPeriod := 5
	logrus.Infof("Watching %s, %s, %s, %d", resource, kind, namespace, resyncPeriod)

    logrus.SetLevel(logrus.WarnLevel)

	sdk.Watch(resource, kind, namespace, resyncPeriod)
	sdk.Handle(stub.NewHandler())
	sdk.Run(context.TODO())
}
