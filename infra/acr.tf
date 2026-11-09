# --- Terraform for the Azure Container Registry ---

resource "azurerm_container_registry" "acr" {
  name                = "jregistry"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true # Not sure if needed yet, gives a username/password the apps can use
}