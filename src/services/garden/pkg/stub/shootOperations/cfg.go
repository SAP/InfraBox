package shootOperations

import (
	"bytes"
	"fmt"
	"net"
	"os"
	"strconv"
	"strings"

	"github.com/Masterminds/semver"
	gApiV1beta "github.com/gardener/gardener/pkg/apis/garden/v1beta1"
	"github.com/gardener/gardener/pkg/client/garden/clientset/versioned/typed/garden/v1beta1"
	"github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"github.com/sap/infrabox/src/services/garden/pkg/apis/garden/v1alpha1"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/common"
	"github.com/sap/infrabox/src/services/garden/pkg/stub/shootOperations/utils"
)

const ENVAwsCloudZones = "AWS_CLOUD_ZONES"
const shootDomainPostfix = ".datahub.shoot.canary.k8s-hana.ondemand.com"
const dummyNameForClusterName = "CLUSTERNAME"
const dummyNameForAwsRegion = "REGIONDUMMY"

func createAwsConfig(sdkops common.SdkOperations, dhInfra *v1alpha1.ShootCluster, cloudProfileIf v1beta1.CloudProfileInterface) (*gApiV1beta.Shoot, error) {
	shootcfg := DefaultAwsConfig()
	fillSpecWithStaticInfo(shootcfg, dhInfra)
	fillSpecFromEnv(shootcfg)
	if err := setNetworkSpec(dhInfra, shootcfg, make([]*net.IPNet, 0)); err != nil {
		return nil, err
	}

	if err := fillSpecWithSecretBindingRef(sdkops, dhInfra, shootcfg); err != nil {
		return nil, err
	}

	if err := fillSpecWithK8sVersion(shootcfg, dhInfra, cloudProfileIf); err != nil {
		return nil, err
	}

	return shootcfg, nil
}

func fillSpecWithSecretBindingRef(sdkops common.SdkOperations, dhInfra *v1alpha1.ShootCluster, shootcfg *gApiV1beta.Shoot) error {
	s := utils.NewSecret(dhInfra)
	if err := sdkops.Get(s); err != nil {
		return err
	}

	if refBinding, ok := s.Data[common.KeySecretBindingRefInSecret]; !ok {
		return fmt.Errorf("secret does not contain secretBindingRef (key: %s)", common.KeySecretBindingRefInSecret)
	} else {
		shootcfg.Spec.Cloud.SecretBindingRef.Name = string(bytes.Trim(refBinding, "\n"))
	}

	return nil
}

func fillSpecWithStaticInfo(shootcfg *gApiV1beta.Shoot, dhInfra *v1alpha1.ShootCluster) {
	shootcfg.GetObjectMeta().SetName(dhInfra.Spec.ShootName)
	shootcfg.ObjectMeta.SetNamespace(dhInfra.Spec.GardenerNamespace)

	vpc := gApiV1beta.CIDR(dhInfra.Spec.VpcCIDR)
	shootcfg.Spec.Cloud.AWS.Networks.VPC.CIDR = &vpc

	shootcfg.Spec.Cloud.AWS.Workers = []gApiV1beta.AWSWorker{{
		Worker: gApiV1beta.Worker{
			AutoScalerMin: int(dhInfra.Spec.MinNodes),
			AutoScalerMax: int(dhInfra.Spec.MaxNodes),
			Name:          "worker",                                     //dhInfra.Spec.WorkerName
			MachineType:   convertMachineType(dhInfra.Spec.MachineType), // TODO: fix as soon as gardener supports all machine types
		},
		VolumeType: "gp2", //dhInfra.Spec.WorkerVolumeType,
		VolumeSize: strconv.Itoa(int(dhInfra.Spec.DiskSize)) + "Gi",
	}}

	shootcfg.Spec.Cloud.Region = dhInfra.Spec.Zone[:len(dhInfra.Spec.Zone)-1] // aws zones are the name of the region plus one letter
	shootcfg.Spec.Cloud.AWS.Zones = []string{dhInfra.Spec.Zone}

	newPolicy := strings.Replace(shootcfg.Spec.Addons.Kube2IAM.Roles[0].Policy, dummyNameForAwsRegion, dhInfra.Spec.Zone, 1)
	newPolicy = strings.Replace(newPolicy, dummyNameForClusterName, dhInfra.Spec.ShootName, 1)
	shootcfg.Spec.Addons.Kube2IAM.Roles[0].Policy = newPolicy

	dns := dhInfra.Spec.ShootName + shootDomainPostfix
	shootcfg.Spec.DNS.Domain = &dns

	shootcfg.Spec.Kubernetes.Version = dhInfra.Spec.ClusterVersion
	shootcfg.Spec.Addons.ClusterAutoscaler.Enabled = dhInfra.Spec.EnableAutoscaling

}

// TODO: temporary fix suggested by Lars. Gardener does not support all types we need (m5.4xlarge, r4.4xlarge)
func convertMachineType(t string) string {
	supported := map[string]string{
		"m5.large":    "m4.large",
		"m5.xlarge":   "m4.xlarge",
		"m5.2xlarge":  "m4.2xlarge",
		"m5.4xlarge":  "m4.4xlarge",
		"m5.12xlarge": "m4.16xlarge",
		"m5.24xlarge": "m4.16xlarge",
		"r4.4xlarge":  "m4.10xlarge",
	}

	if val, ok := supported[t]; ok {
		return val
	} else {
		return t
	}
}

func fillSpecFromEnv(shootcfg *gApiV1beta.Shoot) {
	if s := os.Getenv("AWS_DNS_DOMAIN_SUFFIX"); len(s) != 0 {
		var dns string
		if s[0] == '.' {
			dns = shootcfg.GetName() + s
		} else {
			dns = shootcfg.GetName() + "." + s
		}
		shootcfg.Spec.DNS.Domain = &dns
	}
	if s := os.Getenv("AWS_CLOUD_REGION"); len(s) != 0 {
		shootcfg.Spec.Cloud.Region = s

		zone := strings.Split(s, ",")[0]
		nPol := strings.Replace(shootcfg.Spec.Addons.Kube2IAM.Roles[0].Policy, dummyNameForAwsRegion, zone, 1)
		shootcfg.Spec.Addons.Kube2IAM.Roles[0].Policy = nPol
	}

	if s := os.Getenv("AWS_CLOUD_PROFILE"); len(s) != 0 {
		shootcfg.Spec.Cloud.Profile = s
	}
	if s := os.Getenv("AWS_MAINTENANCE_AUTOUPDATE"); len(s) != 0 {
		if b, err := strconv.ParseBool(s); err != nil {
			logrus.Errorf("Invalid environment value (%s) given for 'AwsMaintenanceAutoUpdate'. Must be a bool. err: %s", s, err)
		} else {
			if shootcfg.Spec.Maintenance == nil {
				shootcfg.Spec.Maintenance = &gApiV1beta.Maintenance{}
			}
			if shootcfg.Spec.Maintenance.AutoUpdate == nil {
				shootcfg.Spec.Maintenance.AutoUpdate = &gApiV1beta.MaintenanceAutoUpdate{}
			}
			shootcfg.Spec.Maintenance.AutoUpdate.KubernetesVersion = b
		}
	}

	if begin, end := os.Getenv("AWS_MAINTENANCE_AUTOUPDATE_TWBEGIN"), os.Getenv("AWS_MAINTENANCE_AUTOUPDATE_TWEND"); (len(begin) != 0) && (len(end) != 0) {

		if shootcfg.Spec.Maintenance == nil {
			shootcfg.Spec.Maintenance = &gApiV1beta.Maintenance{}
		}
		if shootcfg.Spec.Maintenance.TimeWindow == nil {
			shootcfg.Spec.Maintenance.TimeWindow = &gApiV1beta.MaintenanceTimeWindow{}
		}

		shootcfg.Spec.Maintenance.TimeWindow.Begin = begin
		shootcfg.Spec.Maintenance.TimeWindow.End = end
	} else if (len(begin) + len(end)) != 0 {
		logrus.Error("Incomplete time window specified. please check the env variables 'AwsMaintenanceAutoUpdateTWBegin' and 'AwsMaintenanceAutoUpdateTWEnd'")
	}

	if s := os.Getenv("AWS_CLUSTER_AUTOSCALER"); len(s) != 0 {
		if b, err := strconv.ParseBool(s); err != nil {
			logrus.Errorf("Invalid environment value (%s) given for 'AWS_CLUSTER_AUTOSCALER'. Must be a bool. err: %s", s, err)
		} else {
			if shootcfg.Spec.Addons == nil {
				shootcfg.Spec.Addons = &gApiV1beta.Addons{}
			}

			if shootcfg.Spec.Addons.ClusterAutoscaler == nil {
				shootcfg.Spec.Addons.ClusterAutoscaler = &gApiV1beta.ClusterAutoscaler{Addon: gApiV1beta.Addon{Enabled: b}}
			} else {
				shootcfg.Spec.Addons.ClusterAutoscaler.Addon.Enabled = b
			}
		}
	}

	if s := os.Getenv(ENVAwsCloudZones); len(s) != 0 {
		trimmed := strings.Trim(s, ", ")
		czones := strings.Split(trimmed, ",")
		if len(czones) == 0 {
			logrus.Errorf("env variable for 'AWS_CLOUD_ZONES' must be a comma-separated list with nonempty values. Found: %s, which leads to an empty list!", s)
		}

		shootcfg.Spec.Cloud.AWS.Zones = czones
	}
}

func setNetworkSpec(dhInfra *v1alpha1.ShootCluster, shootcfg *gApiV1beta.Shoot, usedSubnets []*net.IPNet) error {
	if len(dhInfra.Spec.VpcCIDR) == 0 {
		return fmt.Errorf("no vpc CIDR specified for AWS cluster!")
	} else if _, _, err := net.ParseCIDR(dhInfra.Spec.VpcCIDR); err != nil {
		return fmt.Errorf("invalid AWS vpc CIDR specified (%s): error: %s", dhInfra.Spec.VpcCIDR, err)
	} else if usedSubnets == nil {
		return fmt.Errorf("no previous usedSubnets given")
	}

	cidr := new(gApiV1beta.CIDR)
	*cidr = gApiV1beta.CIDR(dhInfra.Spec.VpcCIDR)
	shootcfg.Spec.Cloud.AWS.Networks.VPC.CIDR = cidr

	snGen := NewSubnetGenerator(dhInfra.Spec.VpcCIDR)
	snGen.Init(usedSubnets)

	internal, err := snGen.GenerateNext24Subnet()
	if err != nil {
		return err
	}
	worker, err := snGen.GenerateNext25Subnet()
	if err != nil {
		return err
	}
	public, err := snGen.GenerateNext25Subnet()
	if err != nil {
		return err
	}

	shootcfg.Spec.Cloud.AWS.Networks.Internal = []gApiV1beta.CIDR{gApiV1beta.CIDR(internal)}
	shootcfg.Spec.Cloud.AWS.Networks.Public = []gApiV1beta.CIDR{gApiV1beta.CIDR(public)}
	shootcfg.Spec.Cloud.AWS.Networks.Workers = []gApiV1beta.CIDR{gApiV1beta.CIDR(worker)}

	return nil
}

func fillSpecWithK8sVersion(shootcfg *gApiV1beta.Shoot, shootCluster *v1alpha1.ShootCluster, cloudProfileIf v1beta1.CloudProfileInterface) error {
	requestedVersion, err := semver.NewVersion(shootCluster.Spec.ClusterVersion)
	if err != nil {
		logrus.Errorf("error while parsing requested kubernetes version (%s). err: %s", shootCluster.Spec.ClusterVersion, err)
		return err
	}

	profile, err := cloudProfileIf.Get("aws", metav1.GetOptions{})
	if err != nil {
		return err
	}

	versions := profile.Spec.AWS.Constraints.Kubernetes.Versions
	for _, v := range versions {
		sv, err := semver.NewVersion(v)
		if err != nil {
			logrus.Errorf("gardener returned kubernetes version with invalid semver: %s; semver parsing error: %s", v, err.Error())
			continue
		}

		if (requestedVersion.Major() == sv.Major()) &&
			(requestedVersion.Minor() == sv.Minor()) {
			shootcfg.Spec.Kubernetes.Version = v
			return nil
		}
	}

	return fmt.Errorf("couldn't find supported version compatible with requested one (%s). supported versions: %s", shootCluster.Spec.ClusterVersion, strings.Join(versions, ","))
}

func DefaultAwsConfig() *gApiV1beta.Shoot {
	domain := "scenarios" + shootDomainPostfix
	awsVpcCIDR := gApiV1beta.CIDR("10.0.0.0/16") // vpc-86f8b7ed

	return &gApiV1beta.Shoot{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "", // change it
			Namespace: "gApiV1beta-datahub",
		},
		Spec: gApiV1beta.ShootSpec{
			Cloud: gApiV1beta.Cloud{
				Profile: "aws",          // per env
				Region:  "eu-central-1", // per env
				SecretBindingRef: corev1.LocalObjectReference{
					Name: "aws-canary-service-account", // name of credentials, per-cluster configuration taken from secret // TODO
				},
				AWS: &gApiV1beta.AWSCloud{
					Networks: gApiV1beta.AWSNetworks{
						VPC: gApiV1beta.AWSVPC{
							CIDR: &awsVpcCIDR, //set this to let gardener create a new VPC		// per env
						},
						Internal: []gApiV1beta.CIDR{"10.250.205.0/27"},  // change it
						Public:   []gApiV1beta.CIDR{"10.250.205.32/28"}, // change it
						Workers:  []gApiV1beta.CIDR{"10.250.205.48/28"}, // change it
					},
					Workers: []gApiV1beta.AWSWorker{
						{Worker: gApiV1beta.Worker{ // from cr
							Name:          "cpu-worker",
							MachineType:   "m4.2xlarge",
							AutoScalerMin: 5,
							AutoScalerMax: 5},
							VolumeSize: "100Gi",
							VolumeType: "gp2",
						},
					},
					Zones: []string{"eu-central-1a"}, // per env
				},
			},
			Kubernetes: gApiV1beta.Kubernetes{
				Version: "1.10.8", // change as necessary
			},
			DNS: gApiV1beta.DNS{
				Provider: "aws-route53",
				Domain:   &domain, // change it			// per env
			},
			Maintenance: &gApiV1beta.Maintenance{
				TimeWindow: &gApiV1beta.MaintenanceTimeWindow{ // per env
					Begin: "220000+0100",
					End:   "230000+0100",
				},
				AutoUpdate: &gApiV1beta.MaintenanceAutoUpdate{ // per env
					KubernetesVersion: true,
				},
			},
			Backup: &gApiV1beta.Backup{
				Schedule: "*/5 * * * *",
				Maximum:  7,
			},
			Addons: &gApiV1beta.Addons{
				Kube2IAM: &gApiV1beta.Kube2IAM{
					Addon: gApiV1beta.Addon{Enabled: true},
					Roles: []gApiV1beta.Kube2IAMRole{ // TODO: discuss because of ECR sharing (security issue)
						{Name: "ecr",
							Description: "Allow access to ECR repositories beginning with 'vora/', and creation of new repositories",
							Policy: fmt.Sprintf(`{
            "Version": "2012-10-17",
            "Statement": [
              {
                "Action": "ecr:*",
                "Effect": "Allow",
                "Resource": "arn:aws:ecr:%s:${account_id}:repository/%s/vora/*"
              },
              {
                "Action": [
                  "ecr:GetAuthorizationToken",
                  "ecr:CreateRepository"
                ],
                "Effect": "Allow",
                "Resource": "*" 
              }
            ]
          }`, dummyNameForAwsRegion, dummyNameForClusterName)},
					},
				},
				Heapster: &gApiV1beta.Heapster{
					Addon: gApiV1beta.Addon{Enabled: true},
				},
				KubernetesDashboard: &gApiV1beta.KubernetesDashboard{
					Addon: gApiV1beta.Addon{Enabled: true},
				},
				ClusterAutoscaler: &gApiV1beta.ClusterAutoscaler{
					Addon: gApiV1beta.Addon{Enabled: false},
				},
				NginxIngress: &gApiV1beta.NginxIngress{
					Addon: gApiV1beta.Addon{Enabled: true},
				},
				KubeLego: &gApiV1beta.KubeLego{
					Addon: gApiV1beta.Addon{Enabled: false},
					Mail:  "john.doe@example.com",
				},
				Monocular: &gApiV1beta.Monocular{
					Addon: gApiV1beta.Addon{Enabled: false},
				},
			},
		},
	}
}
