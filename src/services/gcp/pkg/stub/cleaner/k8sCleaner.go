package cleaner

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
    _ "k8s.io/client-go/plugin/pkg/client/auth/gcp"
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

func (cc *clusterCleaner) Cleanup() (bool, error) {
	cc.log.Debug("Attempt to clean up cluster")

	isNamespacesClean, err := cc.cleanAllNamespaces(cc.clientSet)
	if err != nil {
		cc.log.Error("couldn't clean all namespaces: ", err.Error())
	}

	isPodsClean, err := cc.cleanPodsInAllNamespaces(cc.clientSet)
	if err != nil {
		cc.log.Error("couldn't remove all pods: ", err.Error())
	}

	isPvcsClean, err := cc.cleanPvcsInAllNamespaces(cc.clientSet)
	if err != nil {
		cc.log.Error("couldn't remove all persistent volume claims: ", err.Error())
	}

	isPvsClean, err := cc.deletePersistentVolumes(cc.pvIf)
	if err != nil {
		cc.log.Error("couldn't remove all persistent volumes: ", err.Error())
	}

	return isNamespacesClean && isPodsClean && isPvcsClean && isPvsClean , err
}

func (cc *clusterCleaner) cleanPvcsInAllNamespaces(clientSet kubernetes.Interface) (bool, error) {
	namespaces, err := cc.nsIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Error("couldn't enlist all namespaces. err: ", err)
		return false, err
	}

	outChan := make(chan *helperResultStruct, len(namespaces.Items))
	for _, ns := range namespaces.Items {
		if ns.GetName() == v1.NamespaceSystem {
			continue
		}
		go func(nsName string, pvcIf corev1.PersistentVolumeClaimInterface, out chan *helperResultStruct) {
			isClean, err := cc.cleanAllPvcInNamespace(nsName, pvcIf)
			out <- &helperResultStruct{isClean, err}
		}(ns.GetName(), clientSet.CoreV1().PersistentVolumeClaims(ns.GetName()), outChan)
	}

	numExpectedResults := len(namespaces.Items) - 1
	allClean, err := cc.collectResults(time.Minute, numExpectedResults, outChan)

	if err != nil {
		return false, err
	}

	return allClean, nil

}

func (cc *clusterCleaner) cleanPodsInAllNamespaces(clientSet kubernetes.Interface) (bool, error) {
	namespaces, err := cc.nsIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Error("couldn't enlist all namespaces. err: ", err)
		return false, err
	}

	outChan := make(chan *helperResultStruct, len(namespaces.Items))
	for _, ns := range namespaces.Items {
		if ns.GetName() == v1.NamespaceSystem {
			continue
		}
		go func(nsName string, podIf corev1.PodInterface, out chan *helperResultStruct) {
			isClean, err := cc.cleanAllPodsInNamespace(nsName, podIf)
			out <- &helperResultStruct{isClean, err}
		}(ns.GetName(), clientSet.CoreV1().Pods(ns.GetName()), outChan)
	}

	numExpectedResults := len(namespaces.Items) - 1
	allClean, err := cc.collectResults(time.Minute, numExpectedResults, outChan)

	if err != nil {
		return false, err
	}

	return allClean, nil

}

type helperResultStruct struct {
	isClean bool
	err     error
}

func (cc *clusterCleaner) cleanAllNamespaces(clientSet kubernetes.Interface) (bool, error) {
	namespaces, err := cc.nsIf.List(v1.ListOptions{})
	if err != nil {
		cc.log.Error("couldn't enlist all namespaces. err: ", err)
		return false, err
	}

	outChan := make(chan *helperResultStruct, len(namespaces.Items))
	for _, ns := range namespaces.Items {
		if ns.GetName() == v1.NamespaceSystem {
			continue
		}

		go func(nsName string,
			pvcIf corev1.PersistentVolumeClaimInterface,
			ingIf v1beta1.IngressInterface,
			deplIf typedAppV1.DeploymentInterface,
			jobIf typedBatchV1.JobInterface,
			statefulSetIf typedAppV1.StatefulSetInterface,
			dsIf typedAppV1.DaemonSetInterface,
			out chan *helperResultStruct) {

			isClean, err := cc.cleanupNamespace(nsName, ingIf, deplIf, jobIf, statefulSetIf, dsIf)
			out <- &helperResultStruct{isClean, err}

		}(ns.GetName(),
			clientSet.CoreV1().PersistentVolumeClaims(ns.GetName()),
			clientSet.ExtensionsV1beta1().Ingresses(ns.GetName()),
			clientSet.AppsV1().Deployments(ns.GetName()),
			clientSet.BatchV1().Jobs(ns.GetName()),
			clientSet.AppsV1().StatefulSets(ns.GetName()),
			clientSet.AppsV1().DaemonSets(ns.GetName()), outChan)
	}

	numExpectedResults := len(namespaces.Items) - 1 // -1 because the system namespace gets ignored
	allClean, err := cc.collectResults(time.Minute, numExpectedResults, outChan)

	if err != nil {
		return false, err
	}

	return allClean, nil
}

func (cc *clusterCleaner) collectResults(toDur time.Duration, numExpectedResults int, outChan chan *helperResultStruct) (bool, error) {
	timeout := time.After(toDur)
	allClean := true
	for i := 0; i < numExpectedResults; i++ {
		select {
		case <-timeout:
			return false, fmt.Errorf("timeout during clearing %d namespaces", numExpectedResults)

		case r := <-outChan:
			if r.err != nil {
				return false, r.err // This doesn't cause a goroutine leak because be set the size of the channel s.t. every routine can put its result into it
			}
			allClean = allClean && r.isClean
		}
	}

	return allClean, nil
}

func (cc *clusterCleaner) cleanupNamespace(ns string,
	ingIf v1beta1.IngressInterface,
	deplIf typedAppV1.DeploymentInterface,
	jobIf typedBatchV1.JobInterface,
	statefulSetIf typedAppV1.StatefulSetInterface,
	dsIf typedAppV1.DaemonSetInterface) (isClean bool, err error) {

	results := make(chan *helperResultStruct, 8)

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
		daemonsetClean, podErr := cc.cleanAllDaemonsetsInNamespace(ns, dsIf)
		results <- &helperResultStruct{daemonsetClean, podErr}
	}()

	go func() {
		jobClean, podErr := cc.cleanAllJobsInNamespace(ns, jobIf)
		results <- &helperResultStruct{jobClean, podErr}
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
	cc.log.Debug("clean all pvc in ns ", ns)

	list, err := pvcIf.List(v1.ListOptions{IncludeUninitialized: true})
	if err != nil {
		cc.log.Errorf("couldn't list all persistent volume claims in the namespace %s. err: %s", ns, err.Error())
		return false, err
	}
	if len(list.Items) == 0 {
		cc.log.Debug("no pvcs are left in ns ", ns)
		return true, nil
	}

	cc.log.Debugf("remove %d pvcs in ns ", len(list.Items), ns)

	now := time.Now()
	for i := range list.Items {
		if err := cc.enablePvcForceDelete(&list.Items[i], now, ns, pvcIf); err != nil {
			return false, err
		}
	}

	delPol := v1.DeletePropagationForeground
	if err := pvcIf.DeleteCollection(&v1.DeleteOptions{PropagationPolicy: &delPol}, v1.ListOptions{IncludeUninitialized: true}); err != nil {
		cc.log.Error("couldn't delete all persistent volume claims. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) enablePvcForceDelete(claim *apiCoreV1.PersistentVolumeClaim, now time.Time, ns string, pvcIf corev1.PersistentVolumeClaimInterface) error {
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
		if _, err := pvcIf.Update(claim); err != nil {
			cc.log.Debugf("couldn't remove finalizers from stateful set '%s' in namespace %s. err: %s", claim.GetName(), ns, err.Error())
			return err
		}
	}

	return nil
}

type CollectionDeleter interface {
	DeleteCollection(options *v1.DeleteOptions, listOptions v1.ListOptions) error
}

func (cc *clusterCleaner) cleanAllStatefulSetInNamespace(ns string, statefulSetIf typedAppV1.StatefulSetInterface) (bool, error) {
	list, err := statefulSetIf.List(v1.ListOptions{IncludeUninitialized: true})
	if err != nil {
		cc.log.Errorf("couldn't list all v1 stateful sets in the namespace %s. err: %s", ns, err.Error())
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

	delPol := v1.DeletePropagationForeground
	if err := statefulSetIf.DeleteCollection(&v1.DeleteOptions{PropagationPolicy: &delPol}, v1.ListOptions{IncludeUninitialized: true}); err != nil {
		cc.log.Error("couldn't delete all v1 stateful sets. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) enableStatefulSetForceDeleteIfNecessary(statefulSet *appV1.StatefulSet, now time.Time, ns string, statefulSetIf typedAppV1.StatefulSetInterface) error {
	if statefulSet.GetDeletionTimestamp() == nil {
		return nil
	}

	durSinceDeletion := now.Sub(statefulSet.GetDeletionTimestamp().Time)
	if durSinceDeletion > deletionPeriodTolerance {
		var dgp int64 = 0
		statefulSet.SetDeletionGracePeriodSeconds(&dgp)
		statefulSet.SetFinalizers([]string{})

		cc.log.Debugf("v1 stateful set '%s' in namespace %s is marked for deletion but wasn't deleted since %s ago. Will try to delete them", statefulSet.GetName(), ns, durSinceDeletion.String())
		statefulSet.SetFinalizers([]string{})
		if _, err := statefulSetIf.Update(statefulSet); err != nil {
			cc.log.Debugf("couldn't remove finalizers from stateful set '%s' in namespace %s. err: %s", statefulSet.GetName(), ns, err.Error())
			return err
		}
	}

	return nil
}

func (cc *clusterCleaner) cleanAllIngressInNamespace(ns string, ingIf v1beta1.IngressInterface) (bool, error) {
	list, err := ingIf.List(v1.ListOptions{IncludeUninitialized: true})
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

	delPol := v1.DeletePropagationForeground
	if err := ingIf.DeleteCollection(&v1.DeleteOptions{PropagationPolicy: &delPol}, v1.ListOptions{IncludeUninitialized: true}); err != nil {
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
	list, err := deplIf.List(v1.ListOptions{IncludeUninitialized: true})
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

	delPol := v1.DeletePropagationForeground
	if err := deplIf.DeleteCollection(&v1.DeleteOptions{PropagationPolicy: &delPol}, v1.ListOptions{IncludeUninitialized: true}); err != nil {
		cc.log.Error("couldn't delete all deployments. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) cleanAllDaemonsetsInNamespace(ns string, deplIf typedAppV1.DaemonSetInterface) (bool, error) {
	list, err := deplIf.List(v1.ListOptions{IncludeUninitialized: true})
	if err != nil {
		cc.log.Errorf("couldn't list all daemonsets in the namespace %s. err: %s", ns, err.Error())
		return false, err
	}
	if len(list.Items) == 0 {
		return true, nil
	}

	now := time.Now()
	for i := range list.Items {
		if err := cc.enableDaemonsetsForceDeleteIfNecessary(&list.Items[i], now, ns, deplIf); err != nil {
			return false, err
		}
	}

	delPol := v1.DeletePropagationForeground
	if err := deplIf.DeleteCollection(&v1.DeleteOptions{PropagationPolicy: &delPol}, v1.ListOptions{IncludeUninitialized: true}); err != nil {
		cc.log.Error("couldn't delete all daemonset. err: ", err)
		return false, err
	}

	return false, nil
}

func (cc *clusterCleaner) enableDaemonsetsForceDeleteIfNecessary(daemonset *appV1.DaemonSet, now time.Time, ns string, deplIf typedAppV1.DaemonSetInterface) error {
	if daemonset.GetDeletionTimestamp() == nil {
		return nil
	}

	durSinceDeletion := now.Sub(daemonset.GetDeletionTimestamp().Time)
	if durSinceDeletion > deletionPeriodTolerance {
		var dgp int64 = 0
		daemonset.SetDeletionGracePeriodSeconds(&dgp)
		daemonset.SetFinalizers([]string{})

		cc.log.Debugf("daemonset '%s' in namespace %s is marked for deletion but wasn't deleted since %s ago. Will try to delete them", daemonset.GetName(), ns, durSinceDeletion.String())
		daemonset.SetFinalizers([]string{})
		if _, err := deplIf.Update(daemonset); err != nil {
			cc.log.Debugf("couldn't remove finalizers from daemonset '%s' in namespace %s. err: %s", daemonset.GetName(), ns, err.Error())
			return err
		}
	}

	return nil
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
	list, err := jobIf.List(v1.ListOptions{IncludeUninitialized: true})
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

	delPol := v1.DeletePropagationForeground
	if err := jobIf.DeleteCollection(&v1.DeleteOptions{PropagationPolicy: &delPol}, v1.ListOptions{IncludeUninitialized: true}); err != nil {
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
	cc.log.Debug("clean all pods in ns ", ns)
	list, err := podIf.List(v1.ListOptions{IncludeUninitialized: true})
	if err != nil {
		cc.log.Errorf("couldn't list all pods in the namespace %s. err: %s", ns, err.Error())
		return false, err
	}
	if len(list.Items) == 0 {
		cc.log.Debug("no pods are left in ns ", ns)
		return true, nil
	}

	cc.log.Debugf("remove %d pods in ns ", len(list.Items), ns)

	now := time.Now()
	for i := range list.Items {
		if err := cc.enablePodForceDeleteIfNecessary(&list.Items[i], now, ns, podIf); err != nil {
			return false, err
		}
	}

	delPol := v1.DeletePropagationForeground
	if err := podIf.DeleteCollection(&v1.DeleteOptions{PropagationPolicy: &delPol}, v1.ListOptions{IncludeUninitialized: true}); err != nil {
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

func (cc *clusterCleaner) deletePersistentVolumes(pvIf corev1.PersistentVolumeInterface) (bool, error) {
	cc.log.Debug("clean up all pv")

	list, err := pvIf.List(v1.ListOptions{IncludeUninitialized: true})
	if err != nil {
		cc.log.Error("couldn't list all persistent volume claims. err: ", err)
		return false, err
	}

	if len(list.Items) == 0 {
		cc.log.Debugf("no pvs are left")
		return true, nil
	}

	cc.log.Debugf("remove %d pvs", len(list.Items))

	// we try a force-delete -> remove finalizers if existent
	now := time.Now()
	for i := range list.Items {
		if err := cc.enablePVForceDeleteIfNecessary(&list.Items[i], now, pvIf); err != nil {
			return false, err
		}
	}

	delPol := v1.DeletePropagationForeground
	if err := pvIf.DeleteCollection(&v1.DeleteOptions{PropagationPolicy: &delPol}, v1.ListOptions{IncludeUninitialized: true}); err != nil {
		cc.log.Error("couldn't delete all persistent volumes. err: ", err)
		return false, err
	}

	return false, nil
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
