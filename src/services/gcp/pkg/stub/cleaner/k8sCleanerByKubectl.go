package cleaner

import (
    "fmt"
    "os"
    "os/exec"
)


type clusterCleanerByKubectl struct {
    kubeConfigPath string
    log *logrus.Entry
}

func NewK8sCleanerByKubectl(kubeConfigPath string, log *log.Entry) *clusterCleanerByKubectl{
    ccbk := &clusterCleanerByKubectl{
        kubeConfigPath: string,
		log:            log,
	}

	return ccbk
}

func (ccbk *clusterCleanerByKubectl) Cleanup() (bool, error) {
    ccbk.log.Debug("Attempt to clean up cluster")
    os.Setenv("KUBECONFIG", ccbk.kubeConfigPath)
    ingressClean, err:= ccbk.cleanAllIngresses()
    if err != nil {
        cc.log.Error("couldn't clean all ingresses: ", err.Error())
        return false, err
    }
    podClean, err := ccbk.cleanAllPods()
    if err != nil {
        cc.log.Error("couldn't clean all ingresses: ", err.Error())
        return false, err
    }
    pvcClean, err := ccbk.cleanAllPVC()
    if err != nil {
        cc.log.Error("couldn't clean all pvc: ", err.Error())
        return false, err
    }
    pvClean, err := ccbk.cleanAllPV()
    if err != nil {
        cc.log.Error("couldn't clean all PV: ", err.Error())
        return false, err
    }
    return true, nil
}

func (ccbk *clusterCleanerByKubectl) cleanAllIngresses() (bool, error) {
    cmd := exec.Command("bash", "-c", "kubectl delete ingress --all --all-namespaces")
	out, err := cmd.Output()
	fmt.Println(string(out))
	if err != nil {
		return false, err
	}
	return true, nil
}
func (ccbk *clusterCleanerByKubectl) cleanAllPods() (bool, error) {
    cmd := exec.Command("bash", "-c", "kubectl delete pod --all --all-namespaces")
	out, err := cmd.Output()
    fmt.Println(string(out))
	if err != nil {
		return false, err
	}
	return true, nil
}

func (ccbk *clusterCleanerByKubectl) cleanAllPVC() (bool, error) {
    cmd := exec.Command("bash", "-c", "kubectl delete pvc --all --all-namespaces")
	out, err := cmd.Output()
	fmt.Println(string(out))
	if err != nil {
		return false, err
	}
	return true, nil
}

func (ccbk *clusterCleanerByKubectl) cleanAllPV() (bool, error) {
    cmd := exec.Command("bash", "-c", "kubectl delete pv --all --all-namespaces")
	out, err := cmd.Output()
	fmt.Println(string(out))
	if err != nil {
		return false, err
	}
	return true, nil
}
