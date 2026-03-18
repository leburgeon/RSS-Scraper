terraform {
  backend "s3" {
    bucket  = "c22-rss-scraper-terraform-state" # Your bucket name
    key     = "rss-scraper/terraform.tfstate"   # Path inside the bucket
    region  = "eu-west-1"
    encrypt = true
  }
}