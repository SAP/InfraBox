package shootOperations

import (
	"fmt"
	"time"

	"github.com/sirupsen/logrus"
	appV1 "k8s.io/api/apps/v1"
	batchV1 "k8s.io/api/batch/v1"
	apiCoreV1 "k8s.io/api/core/v1"
	apiExtV1Beta1 "k8s.io/api/extensions/v1beta1"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	typedAppV1 "k8s.io/client-go/kubernetes/typed/apps/v1"
	typedBatchV1 "k8s.io/client-go/kubernetes/typed/batch/v1"
	corev1 "k8s.io/client-go/kubernetes/typed/core/v1"
	"k8s.io/client-go/kubernetes/typed/extensions/v1beta1"
)

// Attempts to remove all objects in a kubernetes cluster connected to persistent resources.
type clusterCleaner struct {
	clientSet kubernetes.Interface
	log       *logrus.Entry

	nsIf corev1.NamespaceInterface
	pvIf corev1.PersistentVolumeInterface
}

func NewK8sCleaner(cs kubernetes.Interface, log *logrus.Entry) *clusterCleaner {
	cc := &clusterCleaner{
		log:       log,
		clientSet: cs,
	}

	if cs != nil {
		cc.nsIf = cs.CoreV1().Namespaces()
		cc.pvIf = cs.CoreV1().PersistentVolumes()
	}

	return cc
}

var errNotYetClean = fmt.Errorf("cluster isn't clean, yet")

func (cc *clusterCleaner) Cleanup() error {
	cc.log.Debug("Attempt to clean up cluster")

	err := cc.cleanAllNamespaces(cc.clientSet)
	if err != nil {
		if err == errNotYetClean {
			cc.log.Debug("not all namespaces are clean, yet. will skip and retry next round")
		} else {
			cc.log.Error("couldn't clean all namespaces. err: ", err.Error())
		}
		return err
	}

	err = cc.deletePersistentVolumes(cc.pvIf)
	if err != nil {
		if err == errNotYetClean {
			cc.log.Debug("not all persistent volumes are removed, yet. will skip and retry next round")
		} else {
			cc.log.Error("couldn't remove all persistent volumes. err: ", err.Error())
		}
		return err
	}

	return err
}

type helperResultStruct struct {
	isClean bool
	err     error
}

func (cc *clusterCleaner) cleanAllNamespaces(clientSet kubernetes.Interface) error {
	namespaces, err := cc.nsIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Error("couldn't enlist all namespaces. err: ", err)
		return err
	}

	outChan := make(chan *helperResultStruct, len(namespaces.Items))
	for _, ns := range namespaces.Items {
		if ns.GetName() == v1.NamespaceSystem {
			continue
		}

		go func(nsName string, pvcIf corev1.PersistentVolumeClaimInterface, ingIf v1beta1.IngressInterface, podIf corev1.PodInterface, deplIf typedAppV1.DeploymentInterface, jobIf typedBatchV1.JobInterface, statefulSetIf typedAppV1.StatefulSetInterface, out chan *helperResultStruct) {
			isClean, err := cc.cleanupNamespace(nsName, pvcIf, ingIf, podIf, deplIf, jobIf, statefulSetIf)
			out <- &helperResultStruct{isClean, err}
		}(ns.GetName(), clientSet.CoreV1().PersistentVolumeClaims(ns.GetName()), clientSet.ExtensionsV1beta1().Ingresses(ns.GetName()), clientSet.CoreV1().Pods(ns.GetName()), clientSet.AppsV1().Deployments(ns.GetName()), clientSet.BatchV1().Jobs(ns.GetName()), clientSet.AppsV1().StatefulSets(ns.GetName()), outChan)
	}

	numExpectedResults := len(namespaces.Items) - 1
	allClean, err := cc.collectResults(time.Minute, numExpectedResults, outChan)
	switch {
	case err != nil:
		return err
	case !allClean:
		return errNotYetClean
	default:
		return nil
	}
}

func (cc *clusterCleaner) collectResults(toDur time.Duration, numExpectedResults int, outChan chan *helperResultStruct) (bool, error) {
	timeout := time.After(toDur)
	allClean := true
	for i := 0; i < numExpectedResults; i++ { // -1 because the system namespace gets ignored
		select {
		case <-timeout:
			return false, fmt.Errorf("timeout during clearing %d namespaces", numExpectedResults)

		case r := <-outChan:
			if r.err != nil && r.err != errNotYetClean {
				return false, r.err // This doesn't cause a goroutine leak because be set the size of the channel s.t. every routine can put its result into it
			}
			allClean = allClean && r.isClean
		}
	}

	return allClean, nil
}

func (cc *clusterCleaner) cleanupNamespace(ns string, pvcIf corev1.PersistentVolumeClaimInterface, ingIf v1beta1.IngressInterface, podIf corev1.PodInterface, deplIf typedAppV1.DeploymentInterface, jobIf typedBatchV1.JobInterface, statefulSetIf typedAppV1.StatefulSetInterface) (isClean bool, err error) {
	results := make(chan *helperResultStruct, 2)

	go func() {
		pvcClean, pvcErr := cc.cleanAllPvcInNamespace(ns, pvcIf)
		results <- &helperResultStruct{pvcClean, pvcErr}
	}()

	go func() {
		ingressClean, ingErr := cc.cleanAllIngressInNamespace(ns, ingIf)
		results <- &helperResultStruct{ingressClean, ingErr}
	}()

	go func() {
		deploymentClean, podErr := cc.cleanAllStatefulSetInNamespace(ns, statefulSetIf)
		results <- &helperResultStruct{deploymentClean, podErr}
	}()

	go func() {
		deploymentClean, podErr := cc.cleanAllDeploymentsInNamespace(ns, deplIf)
		results <- &helperResultStruct{deploymentClean, podErr}
	}()

	go func() {
		jobClean, podErr := cc.cleanAllJobsInNamespace(ns, jobIf)
		results <- &helperResultStruct{jobClean, podErr}
	}()

	go func() {
		podClean, podErr := cc.cleanAllPodsInNamespace(ns, podIf)
		results <- &helperResultStruct{podClean, podErr}
	}()

	isClean = true
	for i := 0; i < 5; i++ {
		r := <-results
		isClean = isClean && r.isClean
		if r.err != nil && err == nil {
			err = r.err
		}
	}

	return
}

const deletionPeriodTolerance = time.Minute

func (cc *clusterCleaner) cleanAllPvcInNamespace(ns string, pvcIf corev1.PersistentVolumeClaimInterface) (bool, error) {
	list, err := pvcIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Errorf("couldn't list all persistent volume claims in the namespace %s. err: %s", ns, err.Error())
		return false, err
	}
	if len(list.Items) == 0 {
		return true, nil
	}

	now := time.Now()
	for i := range list.Items {
		if err := cc.enablePvcForceDeleteIfNecessary(&list.Items[i], now, ns, pvcIf); err != nil {
			return false, err
		}
	}

	if err := pvcIf.DeleteCollection(nil, v1.ListOptions{}); err != nil {
		cc.log.Error("couldn't delete all persistent volume claims. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) enablePvcForceDeleteIfNecessary(claim *apiCoreV1.PersistentVolumeClaim, now time.Time, ns string, pvcIf corev1.PersistentVolumeClaimInterface) error {
	if claim.GetDeletionTimestamp() == nil {
		return nil
	}

	durSinceDeletion := now.Sub(claim.GetDeletionTimestamp().Time)
	if durSinceDeletion > deletionPeriodTolerance {
		var dgp int64 = 0
		claim.SetDeletionGracePeriodSeconds(&dgp)
		claim.SetFinalizers([]string{})

		cc.log.Debugf("pvc '%s' in namespace %s is marked for deletion but wasn't deleted since %s ago. Will try to delete them", claim.GetName(), ns, durSinceDeletion.String())
		claim.SetFinalizers([]string{})
		if _, err := pvcIf.Update(claim); err != nil {
			cc.log.Debugf("couldn't remove finalizers from pvc '%s' in namespace %s. err: %s", claim.GetName(), ns, err.Error())
			return err
		}
	}

	return nil
}

type CollectionDeleter interface {
	DeleteCollection(options *v1.DeleteOptions, listOptions v1.ListOptions) error
}

func (cc *clusterCleaner) cleanAllStatefulSetInNamespace(ns string, statefulSetIf typedAppV1.StatefulSetInterface) (bool, error) {
	list, err := statefulSetIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Errorf("couldn't list all persistent volume claims in the namespace %s. err: %s", ns, err.Error())
		return false, err
	}
	if len(list.Items) == 0 {
		return true, nil
	}

	now := time.Now()
	for i := range list.Items {
		if err := cc.enableStatefulSetForceDeleteIfNecessary(&list.Items[i], now, ns, statefulSetIf); err != nil {
			return false, err
		}
	}

	if err := statefulSetIf.DeleteCollection(nil, v1.ListOptions{}); err != nil {
		cc.log.Error("couldn't delete all persistent volume claims. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) enableStatefulSetForceDeleteIfNecessary(claim *appV1.StatefulSet, now time.Time, ns string, statefulSetIf typedAppV1.StatefulSetInterface) error {
	if claim.GetDeletionTimestamp() == nil {
		return nil
	}

	durSinceDeletion := now.Sub(claim.GetDeletionTimestamp().Time)
	if durSinceDeletion > deletionPeriodTolerance {
		var dgp int64 = 0
		claim.SetDeletionGracePeriodSeconds(&dgp)
		claim.SetFinalizers([]string{})

		cc.log.Debugf("stateful set '%s' in namespace %s is marked for deletion but wasn't deleted since %s ago. Will try to delete them", claim.GetName(), ns, durSinceDeletion.String())
		claim.SetFinalizers([]string{})
		if _, err := statefulSetIf.Update(claim); err != nil {
			cc.log.Debugf("couldn't remove finalizers from stateful set '%s' in namespace %s. err: %s", claim.GetName(), ns, err.Error())
			return err
		}
	}

	return nil
}

func (cc *clusterCleaner) cleanAllIngressInNamespace(ns string, ingIf v1beta1.IngressInterface) (bool, error) {
	list, err := ingIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Errorf("couldn't list all ingresses in the namespace %s. err: %s", ns, err.Error())
		return false, err
	}
	if len(list.Items) == 0 {
		return true, nil
	}

	now := time.Now()
	for i := range list.Items {
		if err := cc.enableIngressForceDeleteIfNecessary(&list.Items[i], now, ns, ingIf); err != nil {
			return false, err
		}
	}

	if err := ingIf.DeleteCollection(nil, v1.ListOptions{}); err != nil {
		cc.log.Error("couldn't delete all ingresses. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) enableIngressForceDeleteIfNecessary(ingress *apiExtV1Beta1.Ingress, now time.Time, ns string, ingIf v1beta1.IngressInterface) error {
	if ingress.GetDeletionTimestamp() == nil {
		return nil
	}

	durSinceDeletion := now.Sub(ingress.GetDeletionTimestamp().Time)
	if durSinceDeletion > deletionPeriodTolerance {
		var dgp int64 = 0
		ingress.SetDeletionGracePeriodSeconds(&dgp)
		ingress.SetFinalizers([]string{})

		cc.log.Debugf("ingress '%s' in namespace %s is marked for deletion but wasn't deleted since %s ago. Will try to delete them", ingress.GetName(), ns, durSinceDeletion.String())
		ingress.SetFinalizers([]string{})
		if _, err := ingIf.Update(ingress); err != nil {
			cc.log.Debugf("couldn't remove finalizers from ingress '%s' in namespace %s. err: %s", ingress.GetName(), ns, err.Error())
			return err
		}
	}

	return nil
}

func (cc *clusterCleaner) cleanAllDeploymentsInNamespace(ns string, deplIf typedAppV1.DeploymentInterface) (bool, error) {
	list, err := deplIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Errorf("couldn't list all deployments in the namespace %s. err: %s", ns, err.Error())
		return false, err
	}
	if len(list.Items) == 0 {
		return true, nil
	}

	now := time.Now()
	for i := range list.Items {
		if err := cc.enableDeploymentsForceDeleteIfNecessary(&list.Items[i], now, ns, deplIf); err != nil {
			return false, err
		}
	}

	if err := deplIf.DeleteCollection(nil, v1.ListOptions{}); err != nil {
		cc.log.Error("couldn't delete all deployments. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) enableDeploymentsForceDeleteIfNecessary(deployment *appV1.Deployment, now time.Time, ns string, deplIf typedAppV1.DeploymentInterface) error {
	if deployment.GetDeletionTimestamp() == nil {
		return nil
	}

	durSinceDeletion := now.Sub(deployment.GetDeletionTimestamp().Time)
	if durSinceDeletion > deletionPeriodTolerance {
		var dgp int64 = 0
		deployment.SetDeletionGracePeriodSeconds(&dgp)
		deployment.SetFinalizers([]string{})

		cc.log.Debugf("deployment '%s' in namespace %s is marked for deletion but wasn't deleted since %s ago. Will try to delete them", deployment.GetName(), ns, durSinceDeletion.String())
		deployment.SetFinalizers([]string{})
		if _, err := deplIf.Update(deployment); err != nil {
			cc.log.Debugf("couldn't remove finalizers from deployment '%s' in namespace %s. err: %s", deployment.GetName(), ns, err.Error())
			return err
		}
	}

	return nil
}

func (cc *clusterCleaner) cleanAllJobsInNamespace(ns string, jobIf typedBatchV1.JobInterface) (bool, error) {
	list, err := jobIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Errorf("couldn't list all deployments in the namespace %s. err: %s", ns, err.Error())
		return false, err
	}
	if len(list.Items) == 0 {
		return true, nil
	}

	now := time.Now()
	for i := range list.Items {
		if err := cc.enableJobForceDeleteIfNecessary(&list.Items[i], now, ns, jobIf); err != nil {
			return false, err
		}
	}

	if err := jobIf.DeleteCollection(nil, v1.ListOptions{}); err != nil {
		cc.log.Error("couldn't delete all jobs. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) enableJobForceDeleteIfNecessary(job *batchV1.Job, now time.Time, ns string, jobIf typedBatchV1.JobInterface) error {
	if job.GetDeletionTimestamp() == nil {
		return nil
	}

	durSinceDeletion := now.Sub(job.GetDeletionTimestamp().Time)
	if durSinceDeletion > deletionPeriodTolerance {
		var dgp int64 = 0
		job.SetDeletionGracePeriodSeconds(&dgp)
		job.SetFinalizers([]string{})

		cc.log.Debugf("job '%s' in namespace %s is marked for deletion but wasn't deleted since %s ago. Will try to delete them", job.GetName(), ns, durSinceDeletion.String())
		job.SetFinalizers([]string{})
		if _, err := jobIf.Update(job); err != nil {
			cc.log.Debugf("couldn't remove finalizers from job '%s' in namespace %s. err: %s", job.GetName(), ns, err.Error())
			return err
		}
	}

	return nil
}

func (cc *clusterCleaner) cleanAllPodsInNamespace(ns string, podIf corev1.PodInterface) (bool, error) {
	list, err := podIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Errorf("couldn't list all pods in the namespace %s. err: %s", ns, err.Error())
		return false, err
	}
	if len(list.Items) == 0 {
		return true, nil
	}

	now := time.Now()
	for i := range list.Items {
		if err := cc.enablePodForceDeleteIfNecessary(&list.Items[i], now, ns, podIf); err != nil {
			return false, err
		}
	}

	if err := podIf.DeleteCollection(nil, v1.ListOptions{}); err != nil {
		cc.log.Error("couldn't delete all pods. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) enablePodForceDeleteIfNecessary(pod *apiCoreV1.Pod, now time.Time, ns string, podIf corev1.PodInterface) error {
	if pod.GetDeletionTimestamp() == nil {
		return nil
	}

	durSinceDeletion := now.Sub(pod.GetDeletionTimestamp().Time)
	if durSinceDeletion > deletionPeriodTolerance {
		cc.log.Debugf("pod '%s' in namespace %s is marked for deletion but wasn't deleted since %s ago. Will try to delete them", pod.GetName(), ns, durSinceDeletion.String())
		pod.SetFinalizers([]string{})
		if _, err := podIf.Update(pod); err != nil {
			cc.log.Debugf("couldn't remove finalizers from pod '%s' in namespace %s. err: %s", pod.GetName(), ns, err.Error())
			return err
		}
	}

	return nil
}

func (cc *clusterCleaner) deletePersistentVolumes(pvIf corev1.PersistentVolumeInterface) error {
	list, err := pvIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Error("couldn't list all persistent volume claims. err: ", err)
		return err
	}

	if len(list.Items) == 0 {
		return nil
	}

	// we try a force-delete -> remove finalizers if existent
	now := time.Now()
	for i := range list.Items {
		if err := cc.enablePVForceDeleteIfNecessary(&list.Items[i], now, pvIf); err != nil {
			return err
		}
	}

	if err := pvIf.DeleteCollection(nil, v1.ListOptions{}); err != nil {
		cc.log.Error("couldn't delete all persistent volumes. err: ", err)
		return err
	}

	return errNotYetClean
}

func (cc *clusterCleaner) enablePVForceDeleteIfNecessary(pv *apiCoreV1.PersistentVolume, now time.Time, pvIf corev1.PersistentVolumeInterface) error {
	if pv.GetDeletionTimestamp() == nil {
		return nil
	}

	durSinceDeletion := now.Sub(pv.GetDeletionTimestamp().Time)
	if durSinceDeletion > deletionPeriodTolerance {
		var dgp int64 = 0
		pv.SetDeletionGracePeriodSeconds(&dgp)
		pv.SetFinalizers([]string{})

		cc.log.Debugf("pv '%s' is marked for deletion but wasn't deleted since %s ago. Will try to delete them", pv.GetName(), durSinceDeletion.String())
		pv.SetFinalizers([]string{})
		if _, err := pvIf.Update(pv); err != nil {
			cc.log.Debugf("couldn't remove finalizers from pv '%s' . err: %s", pv.GetName(), err.Error())
			return err
		}
	}

	return nil
}
