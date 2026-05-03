# Akamai deployment

This document walks through provisioning a single Akamai NVIDIA RTX PRO 6000
Blackwell Server Edition VM, configuring it, and running the application.

> The `g3-gpu-rtxpro6000-blackwell-1` plan is currently in **limited
> availability**. You must have access enabled on your Linode/Akamai account
> before any of the steps below will succeed. Coordinate with the Akamai
> product team for access.

## Prerequisites

| tool                | tested with             |
|---------------------|--------------------------|
| Terraform           | >= 1.6                   |
| Ansible             | >= 8 (ansible-core 2.15+) |
| Docker (locally)    | >= 24                    |
| Linode API token    | scopes: linodes, firewalls, events (read+write) |
| SSH public key      | used to authorize root SSH on the VM   |

## Step 1: configure environment

```bash
export LINODE_TOKEN=...                           # Linode personal access token
export TF_VAR_ssh_authorized_keys='["ssh-ed25519 AAAA... you@host"]'
# Optional:
# export TF_VAR_region=us-lax
# export TF_VAR_label=cudaq-blueprint-blackwell
# export TF_VAR_firewall_allowed_ssh_cidrs='["198.51.100.7/32"]'
# export TF_VAR_firewall_allowed_app_cidrs='["198.51.100.7/32"]'
```

## Step 2: provision

```bash
cd infra/terraform/akamai
terraform init
terraform plan
terraform apply
```

`terraform apply` writes:

- the Linode instance (`linode_instance.blackwell`),
- an optional Linode firewall (`linode_firewall.blackwell`),
- an Ansible inventory at `infra/terraform/akamai/inventory.ini`.

Outputs of interest:

```bash
terraform output public_ip
terraform output ssh_command
```

## Step 3: configure host

```bash
cd ../../ansible
ansible-playbook -i ../terraform/akamai/inventory.ini playbook.yml
```

The playbook applies three roles in sequence:

1. **`nvidia_driver`** - installs the NVIDIA driver branch and CUDA 12.6
   runtime, reboots if needed, and verifies `nvidia-smi -L` reports a GPU.
2. **`docker`** - installs Docker CE and the NVIDIA Container Toolkit; runs
   `docker run --rm --gpus all nvidia/cuda:... nvidia-smi -L` as a smoke test.
3. **`app`** - pulls the application image from GHCR, renders a systemd unit,
   starts it, and waits for `/health` to return 200.

A single end-to-end script wraps both Terraform and Ansible:

```bash
./scripts/bootstrap_host.sh
```

## Step 4: verify

```bash
# Health check from anywhere
curl http://$(terraform output -raw public_ip):8000/health

# CUDA-Q + GPU smoke test in the running container
ssh root@$(terraform output -raw public_ip) bash -lc \
  'docker exec cudaq-blueprint python -c "import cudaq; cudaq.set_target(\"nvidia\", option=\"fp64\"); print(\"OK\")"'

# Or use the convenience script
scp scripts/verify_gpu.sh root@$(terraform output -raw public_ip):/tmp/
ssh root@$(terraform output -raw public_ip) bash /tmp/verify_gpu.sh
```

## Step 5: run experiments

Open the UI in your browser:

```bash
echo "http://$(terraform output -raw public_ip):8000/"
```

From the UI, pick a molecule and backend and click **Start run**. Convergence
streams live via SSE. Past runs are listed under `/results`. The CPU vs GPU
comparison is at `/compare`.

Or drive the CLI over SSH:

```bash
ssh root@$(terraform output -raw public_ip) bash -lc \
  "docker exec cudaq-blueprint cudaq-bp run h2 --backend gpu_fp64"
```

## Step 6: tear down

When the validation runs are complete, destroy the instance to stop billing:

```bash
cd infra/terraform/akamai
terraform destroy
```

Run artifacts you care about should be exported first:

```bash
ssh root@$(terraform output -raw public_ip) tar czf /tmp/results.tgz -C /var/lib/cudaq-blueprint .
scp root@$(terraform output -raw public_ip):/tmp/results.tgz ./results-akamai.tgz
```

## Cost note

The 1-GPU plan is approximately **$2.50 per hour** as of this writing. Two
days of intermittent runs is well under $50. Always destroy the instance
when not actively using it.

## Region availability

Limited regions as of latest Akamai announcement: Amsterdam, Chennai,
Chicago, Frankfurt, Jakarta, London, Los Angeles, Madrid, Miami, Mumbai,
Milan, Newark, Osaka, Paris, Seattle, Singapore, Stockholm, Tokyo, Toronto.
Verify before deploy:

```bash
linode-cli regions list --json | jq '.[] | select(.capabilities | index("GPU"))'
```
