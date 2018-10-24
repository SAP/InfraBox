package controller

import (
	"github.com/sap/infrabox/src/services/aks/pkg/controller/akscluster"
)

func init() {
	// AddToManagerFuncs is a list of functions to create controllers and add them to a manager.
	AddToManagerFuncs = append(AddToManagerFuncs, akscluster.Add)
}
