# Akamai Terraform stack

Provisions a single NVIDIA RTX PRO 6000 Blackwell Server Edition Linode for
cudaq-molecular-simulation-blueprint.

## What it creates

- One `linode_instance` of type `g3-gpu-rtxpro6000-blackwell-1` (overridable).
- One optional `linode_firewall` allowing SSH (22) and the FastAPI app (8000).
- One local `inventory.ini` for the Ansible follow-up.

## Prerequisites

- Akamai limited-availability access for the RTX PRO 6000 Blackwell plan.
- A Linode personal access token in `LINODE_TOKEN` with `linodes`, `firewalls`,
  and `events` scopes (read+write).
- A copy of `terraform.tfvars.example` -> `terraform.tfvars` with at least
  one SSH public key.

## Usage

```bash
export LINODE_TOKEN=...

cd infra/terraform/akamai
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars

terraform init
terraform plan
terraform apply

# After apply, run Ansible against the rendered inventory:
ansible-playbook -i inventory.ini ../../ansible/playbook.yml
```

## Tearing down

```bash
terraform destroy
```

## Region availability

The RTX PRO 6000 Blackwell plan is offered in limited regions. As of the
latest Akamai announcement: Amsterdam, Chennai, Chicago, Frankfurt, Jakarta,
London, Los Angeles, Madrid, Miami, Mumbai, Milan, Newark, Osaka, Paris,
Seattle, Singapore, Stockholm, Tokyo, Toronto. Verify before deploy:

```bash
linode-cli regions list --json | jq '.[] | select(.capabilities[] | contains("GPU"))'
```

## Cost note

The 1-GPU plan is approximately $2.50/hour. Destroy when not in use.
