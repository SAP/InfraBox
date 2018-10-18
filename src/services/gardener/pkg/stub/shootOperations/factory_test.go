package shootOperations

import (
	"github.com/sirupsen/logrus"
	"testing"
)

func TestNewShootOperatorFactory(t *testing.T) {
	fac := NewShootOperatorFactory(nil, nil, nil)
	if fac == nil {
		t.Fatal("expected nonnil")
	}

	if sop := fac.Get(logrus.WithField("foo", "bar")); sop == nil {
		t.Fatal("expected nonnil")
	}
}
