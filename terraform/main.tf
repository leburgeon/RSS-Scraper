terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket  = "c22-rss-scraper-tf-state"
    key     = "rss-scraper/terraform.tfstate"
    region  = "eu-west-2"
    encrypt = true
  }
}

provider "aws" {
  region = "eu-west-2"
}

# Data for the vpc
data "aws_vpc" "c22_vpc" {
  filter {
    name   = "tag:Name"
    values = ["c22-VPC"]
  }
}

# Verify that the VPC exists
resource "aws_vpc" "c22_vpc" {
  id = data.aws_vpc.c22_vpc.id
}

# Data for public subnets in the VPC
data "aws_subnets" "public_subnets" {
  filter {
    name   = "tag:Name"
    values = ["c22-public-subnet-*"]
  }
}

# Verify that the public subnets exist
resource "aws_subnets" "public_subnets" {
  ids = data.aws_subnets.public_subnets.ids
}

# DynamoDB table for storing the rss feed data
resource "aws_dynamodb_table" "c22_rss_scraper_table" {
  name           = "c22_rss_scraper_table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }
}
