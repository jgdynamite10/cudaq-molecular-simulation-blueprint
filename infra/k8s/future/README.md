# Future: LKE deployment

This directory is intentionally empty.

LKE (Linode Kubernetes Engine) deployment is **explicitly out of scope for v1**
of cudaq-molecular-simulation-blueprint. See
[../../docs/scope-and-non-goals.md](../../docs/scope-and-non-goals.md).

The v1 deployment target is a single Akamai GPU VM provisioned via Terraform
and configured via Ansible (see `../terraform/akamai/` and `../ansible/`).

If/when this project moves to LKE, this directory is where the Helm charts,
Kustomize overlays, and node-pool definitions will live.
