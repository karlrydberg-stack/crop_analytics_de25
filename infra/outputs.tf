# --- Tips! This will print the output of the (public) Azure portal URLs ---
# source: https://build5nines.com/output-link-to-azure-resources-from-terraform-project/

output "backend_url" {
  value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "frontend_url" {
  value = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}
