### Key Considerations for OpenShift 4.21:

* Sync Waves: We use sync-wave: "0" for the Operator and sync-wave: "1" for the NMState instance. This prevents ArgoCD from failing when it tries to apply the NMState object before the CRD is registered by the operator.
* SkipDryRunOnMissingResource: This option in the ArgoCD Application is crucial. Without it, ArgoCD might fail the initial sync because it doesn't recognize the NMState kind yet.
* Singleton Instance: The NMState resource is a cluster-wide singleton. You should only have one instance named nmstate.