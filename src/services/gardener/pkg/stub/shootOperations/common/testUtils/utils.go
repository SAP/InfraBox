package testUtils

import (
	"testing"
	"github.com/golang/mock/gomock"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

type TestError struct {
	Reason metav1.StatusReason
}
func (err *TestError) Error() string {
	return string(err.Reason)
}
func (err *TestError) Status() metav1.Status {
	return metav1.Status{
		Reason: metav1.StatusReason(err.Reason),
	}
}

func CreateMock(t *testing.T) (*gomock.Controller, *MockSdkOperations) {
	mockCtrl := gomock.NewController(t)
	sdkMock := NewMockSdkOperations(mockCtrl)
	return mockCtrl, sdkMock
}
