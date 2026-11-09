# --- Azure Provider block source and version being used
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.5"
    }
  }
}

# --- Configure the Microsoft Azure Provider
provider "azurerm" {
  features {}
  subscription_id = var.subscription_id

  # --- Version 5 of terraform may not register Azure services by default ---
  resource_providers_to_register = [
    "Microsoft.ContainerRegistry",
    "Microsoft.App",
    "Microsoft.OperationalInsights",
    "Microsoft.DBforPostgreSQL",
  ]


}

# --- Create a resource group
resource "azurerm_resource_group" "rg" {
  name     = "jord-rg"
  location = var.location
}

