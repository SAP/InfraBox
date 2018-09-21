package shootOperations

import (
	"testing"

	"github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	"github.com/gardener/gardener/pkg/client/garden/clientset/versioned/fake"
	"github.com/sirupsen/logrus"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	k8sFake "k8s.io/client-go/kubernetes/fake"

	"github.com/sap/infrabox/src/services/garden/pkg/apis/garden/v1alpha1"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/common/testUtils"
)

func TestCreateShootCluster(t *testing.T) {
	log := logrus.WithField("test", "test")
	shootCluster := createShootClusterCr()
	fk := fake.NewSimpleClientset()
	sdkmock := testUtils.NewSdkMockBackedByFake(t, k8sFake.NewSimpleClientset())
	addInputSecretForDHInfraOperator(shootCluster, sdkmock)
	addCloudProfileForAws(shootCluster, fk, t)

	_, err := CreateShootCluster(sdkmock, fk, shootCluster, log)
	if err != nil {
		t.Fatalf("create shoot cluster failed: %s", err)
	}

	s, err := fk.GardenV1beta1().Shoots(shootCluster.Spec.GardenerNamespace).Get(shootCluster.Spec.ShootName, v1.GetOptions{})
	if err != nil {
		t.Fatalf("getting shoot cluster failed: %s", err)
	}

	checkIfShootHasCorrectVals(s, shootCluster, t)
}

func createShootClusterCr() *v1alpha1.ShootCluster {
	ShootCluster := &v1alpha1.ShootCluster{}
	ShootCluster.Spec.GardenerNamespace = "gnamespace"
	ShootCluster.Spec.ShootName = "shootname"
	ShootCluster.Spec.VpcCIDR = "172.0.0.0/16"
	ShootCluster.Spec.MinNodes = 42
	ShootCluster.Spec.MaxNodes = 42
	ShootCluster.Spec.DiskSize = 100
	ShootCluster.Spec.Zone = "us-east-1a"
	ShootCluster.Spec.ClusterVersion = "10.1"
	ShootCluster.SetName("ShootClusterName")
	ShootCluster.SetNamespace("ShootClusterNamespace")
	ShootCluster.SetGroupVersionKind(schema.GroupVersionKind{Group: "garden.service.infrabox.net", Version: "v1alpha1", Kind: "ShootCluster"})
	return ShootCluster
}

func checkShootAgainstSpec(s *v1beta1.Shoot, ShootCluster *v1alpha1.ShootCluster, t *testing.T) {
	if s.Spec.Cloud.AWS.Workers[0].Worker.AutoScalerMin != int(ShootCluster.Spec.MinNodes) {
		t.Fatal("min worker mismatch")
	}
	if s.Spec.Cloud.AWS.Workers[0].Worker.AutoScalerMax != int(ShootCluster.Spec.MaxNodes) {
		t.Fatal("max worker mismatch")
	}
	if string(*s.Spec.Cloud.AWS.Networks.VPC.CIDR) != ShootCluster.Spec.VpcCIDR {
		t.Fatal("aws vpc mismatch")
	}
	if s.GetName() != ShootCluster.Spec.ShootName {
		t.Fatal("name mismatch")
	}
	if s.GetNamespace() != ShootCluster.Spec.GardenerNamespace {
		t.Fatal("namespace mismatch")
	}
}

func checkIfShootHasCorrectVals(s *v1beta1.Shoot, shootCluster *v1alpha1.ShootCluster, t *testing.T) {
	if s.Spec.Cloud.AWS.Workers[0].Worker.AutoScalerMin != int(shootCluster.Spec.MinNodes) {
		t.Fatal("min worker mismatch")
	}
	if s.Spec.Cloud.AWS.Workers[0].Worker.AutoScalerMax != int(shootCluster.Spec.MaxNodes) {
		t.Fatal("max worker mismatch")
	}
	if s.GetName() != shootCluster.Spec.ShootName {
		t.Fatal("name mismatch")
	}
	if s.GetNamespace() != shootCluster.Spec.GardenerNamespace {
		t.Fatal("namespace mismatch")
	}
}

func TestCreateShootCluster_IfAlreadyExist_DontChangeAnything(t *testing.T) {
	log := logrus.WithField("test", "test")

	shootCluster := createShootClusterCr()
	fk := fake.NewSimpleClientset()
	sdkmock := testUtils.NewSdkMockBackedByFake(t, k8sFake.NewSimpleClientset())
	addInputSecretForDHInfraOperator(shootCluster, sdkmock)
	addCloudProfileForAws(shootCluster, fk, t)

	_, err := CreateShootCluster(sdkmock, fk, shootCluster, log)
	if err != nil {
		t.Fatalf("create shoot cluster failed: %s", err)
	}

	_, err = CreateShootCluster(sdkmock, fk, shootCluster, log)
	if !errors.IsAlreadyExists(err) {
		t.Fatalf("expected an AlreadyExists error, but got: %s", err)
	}

	l, err := fk.GardenV1beta1().Shoots(shootCluster.Spec.GardenerNamespace).List(v1.ListOptions{})
	if len(l.Items) != 1 {
		t.Fatalf("only one shoot should exist: %s", err)
	}

	s, err := fk.GardenV1beta1().Shoots(shootCluster.Spec.GardenerNamespace).Get(shootCluster.Spec.ShootName, v1.GetOptions{})
	if err != nil {
		t.Fatalf("getting shoot cluster failed: %s", err)
	}
	checkShootAgainstSpec(s, shootCluster, t)
}
