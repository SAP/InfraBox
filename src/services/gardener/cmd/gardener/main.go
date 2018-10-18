package main

import (
	"context"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/common/operatorSdk"
	"os"
	"runtime"
	"strings"

	"github.com/operator-framework/operator-sdk/pkg/sdk"
	"github.com/operator-framework/operator-sdk/pkg/util/k8sutil"
	sdkVersion "github.com/operator-framework/operator-sdk/version"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub"

	"github.com/sirupsen/logrus"
)

func printVersion() {
	logrus.Infof("Go Version: %s", runtime.Version())
	logrus.Infof("Go OS/Arch: %s/%s", runtime.GOOS, runtime.GOARCH)
	logrus.Infof("operator-sdk Version: %v", sdkVersion.Version)
}

const ENVLogLevel = "LOGLVL"

func setLogLvl() {
	logrus.SetLevel(logrus.WarnLevel)
	lvl := os.Getenv(ENVLogLevel)

	lvl = strings.ToLower(lvl)

	switch lvl {
	case "debug":
		logrus.SetLevel(logrus.DebugLevel)
	case "info":
		logrus.SetLevel(logrus.InfoLevel)
	case "warn":
		logrus.SetLevel(logrus.WarnLevel)
	case "error":
		logrus.SetLevel(logrus.ErrorLevel)
	}
}

func main() {
	setLogLvl()
	printVersion()

	resource := "gardener.service.infrabox.net/v1alpha1"
	kind := "ShootCluster"
	namespace, err := k8sutil.GetWatchNamespace()
	if err != nil {
		logrus.Fatalf("Failed to get watch gardener: %v", err)
	}
	resyncPeriod := 5
	logrus.Infof("Watching %s, %s, %s, %d", resource, kind, namespace, resyncPeriod)

	sdk.Watch(resource, kind, namespace, resyncPeriod)
	sdk.Handle(stub.NewHandler(&operatorSdk.Operations{}))
	sdk.Run(context.TODO())
}
