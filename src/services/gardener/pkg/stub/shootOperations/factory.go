package shootOperations

import (
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/common"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/k8sClientCache"
	"github.com/sap/infrabox/src/services/gardener/pkg/stub/shootOperations/utils"
	"github.com/sirupsen/logrus"

)

type ShootOperatorFactory interface {
	Get(log *logrus.Entry) *ShootOperator
}

type shootOperatorFactory struct {
	opSdk       common.SdkOperations
	clientCache k8sClientCache.ClientCacher
	csCreator   utils.K8sClientSetCreator
}

func NewShootOperatorFactory(opSdk common.SdkOperations, cache k8sClientCache.ClientCacher, csCreator utils.K8sClientSetCreator) ShootOperatorFactory {
	return &shootOperatorFactory{opSdk: opSdk, clientCache: cache, csCreator: csCreator}
}

func (fac *shootOperatorFactory) Get(log *logrus.Entry) *ShootOperator {
	return NewShootOperator(fac.opSdk, fac.clientCache, fac.csCreator, log)
}
