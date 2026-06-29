variable "resource_group_name" {
  description = "Azure resource group name"
  type        = string
  default     = "rg-finops"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "France Central"
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default = {
    Environment = "production"
    Project     = "08-finops"
    ManagedBy   = "terraform"
  }
}
