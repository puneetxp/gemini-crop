resource "google_compute_network" "vpc" {
  name                    = "cropsense-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "cropsense-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}

# NOTE: Private VPC peering for Cloud SQL removed — Cloud Run connects
# to Cloud SQL via the Cloud SQL Auth Proxy over public IP instead.
# Add private networking back once servicenetworking peering is confirmed working.
