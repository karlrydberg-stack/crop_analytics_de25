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

# --- Images ---
variable "backend_image_tag" {
  type    = string
  default = "v1"
}

variable "frontend_image_tag" {
  type    = string
  default = "v1"
}

# --- Read-only database users ---
variable "streamlit_reader_password" {
  type      = string
  sensitive = true
}

# --- If we have the time ---
variable "chatbot_reader_password" {
  type      = string
  sensitive = true
}

variable "gemini_api_key" {
  type      = string
  sensitive = true
}