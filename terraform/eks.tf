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