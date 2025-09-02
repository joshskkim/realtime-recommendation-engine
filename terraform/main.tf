# File: terraform/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "recommendation-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-west-2"
  }
}

# File: terraform/eks.tf
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 10

      instance_types = ["t3.large"]
      
      labels = {
        Environment = "production"
        Application = "recommendation-system"
      }
    }
    
    ml = {
      desired_size = 2
      min_size     = 1
      max_size     = 5

      instance_types = ["c5.xlarge"]
      
      labels = {
        workload = "ml-service"
      }
      
      taints = {
        dedicated = {
          key    = "ml-workload"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }
}

# File: terraform/rds.tf
resource "aws_db_instance" "postgres" {
  identifier     = "recommendation-postgres"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.large"
  
  allocated_storage     = 100
  max_allocated_storage = 500
  storage_encrypted     = true
  
  db_name  = "userdb"
  username = "postgres"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  tags = {
    Name        = "recommendation-postgres"
    Environment = "production"
  }
}

# File: terraform/elasticache.tf
resource "aws_elasticache_replication_group" "redis" {
  description = "Redis replication group for recommendation system"
  replication_group_id       = "recommendation-redis"

  engine               = "redis"
  engine_version       = "7.0"
  node_type           = "cache.r6g.large"
  
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  snapshot_retention_limit = 7
  snapshot_window         = "03:00-05:00"
  
  tags = {
    Name        = "recommendation-redis"
    Environment = "production"
  }
}

# File: terraform/msk.tf
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "recommendation-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = module.vpc.private_subnets
    security_groups = [aws_security_group.kafka.id]
    
    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.kafka.name
      }
    }
  }

  tags = {
    Name        = "recommendation-kafka"
    Environment = "production"
  }
}