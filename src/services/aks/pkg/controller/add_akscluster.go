package controller

import (
	"github.wdf.sap.corp/i349934/ib-svc-aks/pkg/controller/akscluster"
)

func init() {
	// AddToManagerFuncs is a list of functions to create controllers and add them to a manager.
	AddToManagerFuncs = append(AddToManagerFuncs, akscluster.Add)
}
