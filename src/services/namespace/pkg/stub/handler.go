package stub

import (
	"github.com/sap/infrabox/src/services/namespace/pkg/apis/namespace/v1alpha1"

	"github.com/operator-framework/operator-sdk/pkg/sdk/action"
	"github.com/operator-framework/operator-sdk/pkg/sdk/handler"
	"github.com/operator-framework/operator-sdk/pkg/sdk/types"
    "github.com/operator-framework/operator-sdk/pkg/sdk/query"
	"github.com/sirupsen/logrus"
	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	rbacv1 "k8s.io/api/rbac/v1"
)

func NewHandler() handler.Handler {
	return &Handler{}
}

type Handler struct {}

func syncNamespace(cr *v1alpha1.ClusterNamespace) error {
    if cr.Status.Status == "ready" || cr.Status.Status == "error"  {
        return nil
    }

    cr.SetFinalizers([]string{"namespace.service.infrabox.net"})
    cr.Status.Status = "pending"
    err := action.Update(cr)
    if err != nil {
        logrus.Errorf("Failed to set finalizers: %v", err)
        return err
    }

    err = action.Create(newNamespace(cr))
    if err != nil && !errors.IsAlreadyExists(err) {
        logrus.Errorf("Failed to create namespace: %v", err)
        return err
    }

    err = action.Create(newResourceQuota(cr))
    if err != nil && !errors.IsAlreadyExists(err) {
        logrus.Errorf("Failed to create resource quota: %v", err)
        return err
    }

    err = action.Create(newRole(cr))
    if err != nil && !errors.IsAlreadyExists(err) {
        logrus.Errorf("Failed to create role: %v", err)
        return err
    }

    err = action.Create(newRoleBinding(cr))
    if err != nil && !errors.IsAlreadyExists(err) {
        logrus.Errorf("Failed to create role binding: %v", err)
        return err
    }

    err = action.Create(newSecret(cr))
    if err != nil && !errors.IsAlreadyExists(err) {
        logrus.Errorf("Failed to delete secret: %v", err)
        return err
    }

    return nil
}

func deleteNamespace(cr *v1alpha1.ClusterNamespace) error {
    cr.Status.Status = "pending"
    err := action.Update(cr)
    if err != nil {
        logrus.Errorf("Failed to set finalizers: %v", err)
        return err
    }

    err = action.Delete(newResourceQuota(cr))
    if err != nil && !errors.IsNotFound(err) {
        logrus.Errorf("Failed to delete resource quota: %v", err)
        return err
    }

    err = action.Delete(newRoleBinding(cr))
    if err != nil && !errors.IsNotFound(err) {
        logrus.Errorf("Failed to delete role binding: %v", err)
        return err
    }

    err = action.Delete(newRole(cr))
    if err != nil && !errors.IsNotFound(err) {
        logrus.Errorf("Failed to delete role: %v", err)
        return err
    }

    secretName :=  cr.ObjectMeta.Labels["service.infrabox.net/secret-name"]
    secret := &v1.Secret{
        TypeMeta: metav1.TypeMeta{
            Kind:       "Secret",
            APIVersion: "v1",
        },
        ObjectMeta: metav1.ObjectMeta{
            Name:      secretName,
            Namespace: cr.Namespace,
        },
    }

    err = action.Delete(secret)
    if err != nil && !errors.IsNotFound(err) {
        logrus.Errorf("Failed to delete secret: %v", err)
        return err
    }

    err = action.Delete(newNamespace(cr))
    if err != nil && !errors.IsNotFound(err) {
        logrus.Errorf("Failed to delete namespace: %v", err)
        return err
    }

    cr.SetFinalizers([]string{})
    err = action.Update(cr)
    if err != nil {
        logrus.Errorf("Failed to remove finalizers: %v", err)
        return err
    }

    err = action.Delete(cr)
    if err != nil && !errors.IsNotFound(err) {
        logrus.Errorf("Failed to delete cr: %v", err)
        return err
    }

    return nil
}

func (h *Handler) Handle(ctx types.Context, event types.Event) error {
	switch o := event.Object.(type) {
	case *v1alpha1.ClusterNamespace:
        ns := o
        if event.Deleted {
            return nil
        }

        delTimestamp := ns.GetDeletionTimestamp()
        if delTimestamp != nil {
            return deleteNamespace(ns)
        } else {
            err := syncNamespace(ns)

            if err != nil {
                ns.Status.Status = "error"
                ns.Status.Message = err.Error()
                err = action.Update(ns)
                return err
            } else {
                if ns.Status.Status == "" || ns.Status.Status == "pending"  {
                    ns.Status.Status = "ready"
                    err = action.Update(ns)
                    return err
                }
            }
        }
	}
	return nil
}

func getLabels(cr *v1alpha1.ClusterNamespace) map[string]string {
    return map[string]string {}
}

func newSecret(cr *v1alpha1.ClusterNamespace) *v1.Secret {
    secrets := &v1.SecretList {
		TypeMeta: metav1.TypeMeta{
			Kind:       "Secret",
			APIVersion: "v1",
		},
    }

    query.List(cr.Name, secrets)

    s := secrets.Items[0].DeepCopy()

    s.Data["endpoint"] = []byte("https://kubernetes.default.svc")

    secretName := cr.ObjectMeta.Labels["service.infrabox.net/secret-name"]

	return &v1.Secret{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Secret",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      secretName,
            Labels:    getLabels(cr),
            Namespace: cr.Namespace,
        },
        Data: s.Data,
    }
}

func newNamespace(cr *v1alpha1.ClusterNamespace) *v1.Namespace {
	return &v1.Namespace{
		TypeMeta: metav1.TypeMeta{
			Kind:       "Namespace",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      cr.Name,
            Labels:    getLabels(cr),
        },
    }
}

func newResourceQuota(cr *v1alpha1.ClusterNamespace) *v1.ResourceQuota {
	return &v1.ResourceQuota{
		TypeMeta: metav1.TypeMeta{
			Kind:       "ResourceQuota",
			APIVersion: "v1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      cr.Name,
			Namespace: cr.Name,
			OwnerReferences: newOwnerReference(cr),
            Labels: getLabels(cr),
		},
		Spec: cr.Spec.ResourceQuota,
    }
}

func newRoleBinding(cr *v1alpha1.ClusterNamespace) *rbacv1.RoleBinding {
    return &rbacv1.RoleBinding {
		TypeMeta: metav1.TypeMeta{
			Kind:       "RoleBinding",
			APIVersion: "rbac.authorization.k8s.io/v1beta1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      cr.Name,
			Namespace: cr.Name,
			OwnerReferences: newOwnerReference(cr),
            Labels: getLabels(cr),
		},
        Subjects: []rbacv1.Subject{{
            Kind: "ServiceAccount",
            Name: "default",
            Namespace: cr.Name,
        }},
        RoleRef: rbacv1.RoleRef{
            Kind: "Role",
            Name: "infrabox",
            APIGroup: "rbac.authorization.k8s.io",
        },
    }
}


func newRole(cr *v1alpha1.ClusterNamespace) *rbacv1.Role {
    return &rbacv1.Role {
		TypeMeta: metav1.TypeMeta{
			Kind:       "Role",
			APIVersion: "rbac.authorization.k8s.io/v1beta1",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:      "infrabox",
			Namespace: cr.Name,
			OwnerReferences: newOwnerReference(cr),
            Labels: getLabels(cr),
		},
        Rules: []rbacv1.PolicyRule{{
            APIGroups: []string{"", "extensions", "apps", "batch"},
            Resources: []string{"*"},
            Verbs: []string{"*"},
        }, {
            APIGroups: []string{"rbac.authorization.k8s.io"},
            Resources: []string{"roles", "rolebindings"},
            Verbs: []string{"*"},
        }, {
            APIGroups: []string{"policy"},
            Resources: []string{"poddisruptionbudgets"},
            Verbs: []string{"*"},
        }},
    }
}

func newOwnerReference(cr *v1alpha1.ClusterNamespace) []metav1.OwnerReference {
    return []metav1.OwnerReference{
        *metav1.NewControllerRef(cr, schema.GroupVersionKind{
            Group:   v1alpha1.SchemeGroupVersion.Group,
            Version: v1alpha1.SchemeGroupVersion.Version,
            Kind:    "ClusterNamespace",
        }),
    }
}
