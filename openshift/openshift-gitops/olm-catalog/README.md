### Key Considerations for OpenShift 4.21:

* Sync Waves: We use sync-wave: "0" for the Operator and sync-wave: "1" for the NMState instance. This prevents ArgoCD from failing when it tries to apply the NMState object before the CRD is registered by the operator.
* SkipDryRunOnMissingResource: This option in the ArgoCD Application is crucial. Without it, ArgoCD might fail the initial sync because it doesn't recognize the NMState kind yet.
* Singleton Instance: The NMState resource is a cluster-wide singleton. You should only have one instance named nmstate.

## Troubleshooting

- Argo CD sync fails for NMState custom resources:
	- Confirm the operator application sync wave is lower than the NMState instance sync wave.
	- Ensure `SkipDryRunOnMissingResource=true` is set on the NMState application.
- NMState CRD not found:
	- Verify the NMState operator application is healthy and CSV is `Succeeded` before syncing the instance.
	- Re-sync operator app first, then sync NMState instance app.
- Duplicate NMState resources detected:
	- Remove extra NMState instances and keep only the singleton `nmstate` object.