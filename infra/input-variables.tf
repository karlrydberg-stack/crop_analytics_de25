# --- Azure's ---
variable "subscription_id" {
  type = string
}

variable "location" {
  description = "location to be used for resoucres"
  type        = string
  default     = "belgiumcentral"
}

# --- For postgress ---

variable "postgres_location" {
  type    = string
  default = "norwayeast"
}


variable "db_admin_user" {
  type    = string
  default = "cropadmin"
}

variable "db_admin_password" {
  type      = string
  sensitive = true # hidden in Terraform's output
}

# --- Image ---
variable "image_tag" {
  type    = string
  default = "v1"

}

