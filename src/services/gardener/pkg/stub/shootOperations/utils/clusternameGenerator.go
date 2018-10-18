package utils

import (
	"math/rand"
	"os"
	"strings"

	"github.com/sap/infrabox/src/services/gardener/pkg/apis/gardener/v1alpha1"
)

const clusterNamePrefix = "ib-"
const projectName = "datahub"

func CreateUniqueClusterName(list *v1alpha1.ShootClusterList) string {
	givenNames := make(map[string]struct{}, len(list.Items))
	for i := range list.Items {
		givenNames[list.Items[i].GetName()] = struct{}{}
	}

	const allowedChars = "0123456789abcdefghijklmnopqrstuvwxyz"

	pname := projectName
	if val, exists := os.LookupEnv("GARDENER_PROJECTNAME"); exists && len(val) > 0 {
		pname = val
	}

	createName := func() string {
		parts := make([]string, 1)
		parts[0] = clusterNamePrefix
		for i := len(clusterNamePrefix); i < 21-len(pname); i++ {
			parts = append(parts, string(allowedChars[rand.Int31n(int32(len(allowedChars)))]))
		}

		return strings.Join(parts, "")
	}

	var name string
	for {
		name = createName()
		if _, alreadyExists := givenNames[name]; !alreadyExists {
			break
		}
	}

	return name
}
