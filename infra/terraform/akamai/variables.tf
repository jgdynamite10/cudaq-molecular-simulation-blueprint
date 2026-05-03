variable "label" {
  type        = string
  description = "Label applied to the Linode instance and dependent resources."
  default     = "cudaq-blueprint-blackwell"
}

variable "region" {
  type        = string
  description = <<-EOT
    Akamai region slug. The RTX PRO 6000 Blackwell plan is feature-gated and
    capacity-limited; before applying, verify both with:

      curl -sH "Authorization: Bearer $LINODE_TOKEN" \
        "https://api.linode.com/v4/regions/<region>/availability?page_size=500" \
        | jq '.data[] | select(.plan == "g3-gpu-rtxpro6000-blackwell-1")'

    As of 2026-05-01, Blackwell is in stock in id-cgk (Jakarta) and br-gru
    (Sao Paulo) for this account. Jakarta carries a regional price uplift
    (~$3.00/hr/GPU vs $2.50 base); Sao Paulo carries a larger one ($3.50/hr/GPU).
  EOT
  default     = "id-cgk"
}

variable "instance_type" {
  type        = string
  description = "Linode plan slug. Defaults to the 1-card RTX PRO 6000 Blackwell plan."
  default     = "g3-gpu-rtxpro6000-blackwell-1"
}

variable "image" {
  type        = string
  description = "Linode image slug for the boot disk."
  default     = "linode/ubuntu22.04"
}

variable "ssh_authorized_keys" {
  type        = list(string)
  description = "SSH public keys authorized for the root user."
  validation {
    condition     = length(var.ssh_authorized_keys) > 0
    error_message = "At least one SSH public key must be provided."
  }
}

variable "tags" {
  type        = list(string)
  description = "Tags applied to the Linode instance."
  default     = ["cudaq-blueprint", "blackwell", "research"]
}

variable "create_firewall" {
  type        = bool
  description = "Whether to create a Linode firewall restricting inbound traffic."
  default     = true
}

variable "firewall_allowed_ssh_cidrs" {
  type        = list(string)
  description = "CIDR blocks allowed to SSH (port 22). Default is open; tighten for production."
  default     = ["0.0.0.0/0", "::/0"]
}

variable "firewall_allowed_app_cidrs" {
  type        = list(string)
  description = "CIDR blocks allowed to reach the FastAPI app on port 8000."
  default     = ["0.0.0.0/0", "::/0"]
}

variable "private_ip" {
  type        = bool
  description = "Allocate a private IP on the instance for VLAN integration."
  default     = false
}

variable "disk_encryption" {
  type        = string
  description = "Whether to enable disk encryption ('enabled' or 'disabled')."
  default     = "enabled"
}

variable "render_ansible_inventory" {
  type        = bool
  description = "If true, write a ready-to-use Ansible inventory file alongside terraform state."
  default     = true
}
