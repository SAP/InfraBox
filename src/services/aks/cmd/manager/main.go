package main

import (
	"flag"
	"log"
	"runtime"

	"github.com/operator-framework/operator-sdk/pkg/util/k8sutil"
	sdkVersion "github.com/operator-framework/operator-sdk/version"
	"github.com/sap/infrabox/src/services/aks/pkg/apis"
	"github.com/sap/infrabox/src/services/aks/pkg/controller"
	_ "k8s.io/client-go/plugin/pkg/client/auth/gcp"
	"sigs.k8s.io/controller-runtime/pkg/client/config"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/runtime/signals"
    "os"
    "os/exec"
)

func printVersion() {
	log.Printf("Go Version: %s", runtime.Version())
	log.Printf("Go OS/Arch: %s/%s", runtime.GOOS, runtime.GOARCH)
	log.Printf("operator-sdk Version: %v", sdkVersion.Version)
}

func azureLogin() {
    log.Println("Checking environments")
    tenantID := os.Getenv("TENANT_ID")
    if tenantID == "" {
        log.Fatalln("environment variable TENANT_ID not set")
        os.Exit(1)
    }

    subscriptionID := os.Getenv("SUBSCRIPTION_ID")
    if subscriptionID == "" {
        log.Fatalln("environment variable SUBSCRIPTION_ID not set")
        os.Exit(1)
    }

    servicePrincipal := os.Getenv("SERVICE_PRINCIPAL")
    if servicePrincipal == "" {
        log.Fatalln("environment variable SERVICE_PRINCIPAL not set")
        os.Exit(1)
    }

    clientSecret := os.Getenv("CLIENT_SECRET")
    if clientSecret == "" {
        log.Fatalln("environment variable CLIENT_SECRET not set")
        os.Exit(1)
    }

    cmd := exec.Command("az", "login", "--service-principal", "--username", servicePrincipal, "--password", clientSecret, "--tenant", tenantID)
    out, err := cmd.CombinedOutput()
    if err != nil {
        log.Fatalln("Could not login azure account: %s", string(out))
        os.Exit(2)
    }

    cmd = exec.Command("az", "account", "set", "--subscription", subscriptionID)
    out, err = cmd.CombinedOutput()
    if err != nil {
        log.Fatalln("Could not set account subscription: %s", string(out))
        os.Exit(2)
    }

    log.Println("Successfully logged in azure account")
}


func main() {
	printVersion()
	flag.Parse()
	azureLogin()

	namespace, err := k8sutil.GetWatchNamespace()
	if err != nil {
		log.Fatalf("failed to get watch namespace: %v", err)
	}

	// Get a config to talk to the apiserver
	cfg, err := config.GetConfig()
	if err != nil {
		log.Fatal(err)
	}

	// Create a new Cmd to provide shared dependencies and start components
	mgr, err := manager.New(cfg, manager.Options{Namespace: namespace})
	if err != nil {
		log.Fatal(err)
	}

	log.Print("Registering Components.")

	// Setup Scheme for all resources
	if err := apis.AddToScheme(mgr.GetScheme()); err != nil {
		log.Fatal(err)
	}

	// Setup all Controllers
	if err := controller.AddToManager(mgr); err != nil {
		log.Fatal(err)
	}

	log.Print("Starting the Cmd.")

	// Start the Cmd
	log.Fatal(mgr.Start(signals.SetupSignalHandler()))
}
