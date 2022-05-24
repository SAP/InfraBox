package cleaner

import (
    "os"
    "os/exec"
    "github.com/sirupsen/logrus"
)


type clusterCleanerByKubectl struct {
    kubeConfigPath string
    log *logrus.Entry
}

func NewK8sCleanerByKubectl(kubeConfigPath string, log *logrus.Entry) *clusterCleanerByKubectl{
    ccbk := &clusterCleanerByKubectl{
        kubeConfigPath: kubeConfigPath,
		log:            log,
	}

	return ccbk
}

func (ccbk *clusterCleanerByKubectl) Cleanup() (bool, error) {
    ccbk.log.Debug("Attempt to clean up cluster")
    os.Setenv("KUBECONFIG", ccbk.kubeConfigPath)
    ingressClean, err:= ccbk.cleanAllIngresses()
    if err != nil {
        ccbk.log.Error("couldn't clean all ingresses: ", err.Error())
        return ingressClean, err
    }
    resourceClean, err := ccbk.cleanResources()
    if err != nil {
        ccbk.log.Error("couldn't clean all resources: ", err.Error())
        return resourceClean, err
    }
    pvcClean, err := ccbk.cleanAllPVC()
    if err != nil {
        ccbk.log.Error("couldn't clean all pvc: ", err.Error())
        return pvcClean, err
    }
    pvClean, err := ccbk.cleanAllPV()
    if err != nil {
        ccbk.log.Error("couldn't clean all PV: ", err.Error())
        return pvClean, err
    }
    return true, nil
}

func (ccbk *clusterCleanerByKubectl) cleanAllIngresses() (bool, error) {
    ccbk.log.Debug("Attempt to clean up ingress")
    cmd := exec.Command("bash", "-c", "kubectl delete ingress --all --all-namespaces")
	out, err := cmd.Output()
    ccbk.log.Debug("clean all ingress in all namespaces: ", out)
	if err != nil {
		return false, err
	}
	return true, nil
}
func (ccbk *clusterCleanerByKubectl) cleanResources() (bool, error) {
    ccbk.log.Debug("Attempt to clean up resources")
    cmd := exec.Command("bash", "-c", "kubectl delete all --all --all-namespaces")
	out, err := cmd.Output()
	ccbk.log.Debug("clean all resources in all namespaces: ", out)
	if err != nil {
		return false, err
	}
	return true, nil
}

func (ccbk *clusterCleanerByKubectl) cleanAllPVC() (bool, error) {
    ccbk.log.Debug("Attempt to clean up PVC")
    cmd := exec.Command("bash", "-c", "kubectl delete pvc --all --all-namespaces")
	out, err := cmd.Output()
	ccbk.log.Debug("clean all resources in all pvc: ", out)
	if err != nil {
		return false, err
	}
	return true, nil
}

func (ccbk *clusterCleanerByKubectl) cleanAllPV() (bool, error) {
    ccbk.log.Debug("Attempt to clean up PV")
    cmd := exec.Command("bash", "-c", "kubectl delete pv --all --all-namespaces")
	out, err := cmd.Output()
	ccbk.log.Debug("clean all resources in all pv: ", out)
	if err != nil {
		return false, err
	}
	return true, nil
}
