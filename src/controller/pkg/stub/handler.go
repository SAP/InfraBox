package stub

import (
	"context"
	"github.com/sap/infrabox/src/controller/pkg/apis/core/v1alpha1"

	"github.com/onrik/logrus/filename"
	"github.com/operator-framework/operator-sdk/pkg/sdk"
	"github.com/sirupsen/logrus"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
)

func NewHandler() sdk.Handler {
	return &Controller{}
}

func init() {
	logrus.AddHook(filename.NewHook())
	// logrus.SetLevel(logrus.WarnLevel)
}

type Controller struct{}

func handleError(pi *v1alpha1.IBPipelineInvocation, err error) error {
	if errors.IsConflict(err) {
		// we just wait for the next update
		return nil
	}

	pi.Status.State = "error"
	pi.Status.Message = err.Error()
	err = sdk.Update(pi)

	if err != nil && errors.IsConflict(err) {
		return err
	}

	return err
}

func (h *Controller) Handle(ctx context.Context, event sdk.Event) error {
	switch o := event.Object.(type) {
	case *v1alpha1.IBPipelineInvocation:
		pi := o
		if event.Deleted {
			return nil
		}

		log := logrus.WithFields(logrus.Fields{
			"namespace": pi.Namespace,
			"name":      pi.Name,
		})

		delTimestamp := pi.GetDeletionTimestamp()
		if delTimestamp != nil {
			return h.deletePipelineInvocation(pi, log)
		}

		if pi.Status.State == "error" || pi.Status.State == "terminated" {
			log.Info("pi terminated, ignoring")
			return nil
		}

		if pi.Status.State == "" || pi.Status.State == "preparing" {
			err := h.preparePipelineInvocation(pi, log)
			if err != nil {
				return handleError(pi, err)
			}
		}

		if pi.Status.State == "running" || pi.Status.State == "scheduling" {
			err := h.runPipelineInvocation(pi, log)
			if err != nil {
				return handleError(pi, err)
			}
		}

		if pi.Status.State == "finalizing" {
			err := h.finalizePipelineInvocation(pi, log)
			if err != nil {
				return handleError(pi, err)
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
