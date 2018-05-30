package stub

import (
	"context"
	//goerr "errors"
	"github.com/sap/infrabox/src/controller/pkg/apis/core/v1alpha1"

	"github.com/onrik/logrus/filename"
	"github.com/operator-framework/operator-sdk/pkg/sdk"
	"github.com/sirupsen/logrus"

	"k8s.io/apimachinery/pkg/api/errors"
	//metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	corev1 "k8s.io/api/core/v1"
	//"k8s.io/apimachinery/pkg/runtime/schema"
	//"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

func NewHandler() sdk.Handler {
	return &Controller{}
}

func init() {
	logrus.AddHook(filename.NewHook())
	// logrus.SetLevel(logrus.WarnLevel)
}

type Controller struct{}

func (h *Controller) Handle(ctx context.Context, event sdk.Event) error {
	switch o := event.Object.(type) {
	case *v1alpha1.IBPipelineInvocation:
		ns := o
		if event.Deleted {
			return nil
		}

		log := logrus.WithFields(logrus.Fields{
			"namespace": ns.Namespace,
			"name":      ns.Name,
		})

		delTimestamp := ns.GetDeletionTimestamp()
		if delTimestamp != nil {
			return h.deletePipelineInvocation(ns, log)
		} else {
			if ns.Status.Status == "error" {
				log.Info("pi terminated, ignoring")
				return nil
			}

			err := h.syncPipelineInvocation(ns, log)

			if err == nil {
				return nil
			}

			if errors.IsConflict(err) {
				// we just wait for the next update
				return nil
			}

			ns.Status.Status = "error"
			ns.Status.Message = err.Error()
			err = sdk.Update(ns)

			if err != nil && errors.IsConflict(err) {
				return err
			}
		}
	case *v1alpha1.IBFunctionInvocation:
		ns := o
		if event.Deleted {
			return nil
		}

		log := logrus.WithFields(logrus.Fields{
			"namespace": ns.Namespace,
			"name":      ns.Name,
		})

		delTimestamp := ns.GetDeletionTimestamp()
		if delTimestamp != nil {
			return h.deleteFunctionInvocation(ns, log)
		} else {
			err := h.syncFunctionInvocation(ns, log)

			if ns.Status.State.Terminated != nil {
				log.Info("function terminated, ignoring")
				return nil
			}

			if err == nil {
				return nil
			}

			if errors.IsConflict(err) {
				// we just wait for the next update
				return nil
			}

			// Update status in case of error
			ns.Status.State.Terminated = &corev1.ContainerStateTerminated{
				ExitCode: 1,
				Message:  err.Error(),
			}

			err = sdk.Update(ns)

			if err != nil && errors.IsConflict(err) {
				return err
			}
		}
	}

	return nil
}
