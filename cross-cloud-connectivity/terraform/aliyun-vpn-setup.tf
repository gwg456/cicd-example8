# 阿里云VPN网关配置
# 用于与AWS建立跨云IPSec VPN连接

terraform {
  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 1.200"
    }
  }
  required_version = ">= 1.0"
}

# 配置阿里云Provider
provider "alicloud" {
  access_key = var.aliyun_access_key
  secret_key = var.aliyun_secret_key
  region     = var.aliyun_region
}

# 变量定义
variable "aliyun_access_key" {
  description = "阿里云Access Key"
  type        = string
  sensitive   = true
}

variable "aliyun_secret_key" {
  description = "阿里云Secret Key"
  type        = string
  sensitive   = true
}

variable "aliyun_region" {
  description = "阿里云区域"
  type        = string
  default     = "cn-beijing"
}

variable "aws_vpn_gateway_ip" {
  description = "AWS VPN网关公网IP"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "preshared_key" {
  description = "IPSec预共享密钥"
  type        = string
  sensitive   = true
  default     = "MyStrongPreSharedKey123!"
}

variable "local_subnet" {
  description = "本地子网CIDR"
  type        = string
  default     = "10.0.0.0/16"
}

variable "remote_subnet" {
  description = "远程子网CIDR"
  type        = string
  default     = "172.16.0.0/16"
}

# 获取可用区信息
data "alicloud_zones" "default" {
  available_resource_creation = ["VSwitch"]
}

# 创建VPN网关
resource "alicloud_vpn_gateway" "cross_cloud_gateway" {
  name                 = "aws-cross-cloud-vpn"
  vpc_id              = var.vpc_id
  bandwidth           = "200"
  instance_charge_type = "PostPaid"
  description         = "跨云连接到AWS的VPN网关"
  enable_ssl          = false
  enable_ipsec        = true
  
  tags = {
    Name        = "AWS-Cross-Cloud-VPN"
    Environment = "production"
    Purpose     = "cross-cloud-connectivity"
    CreatedBy   = "terraform"
  }
}

# 创建客户网关 (AWS侧)
resource "alicloud_vpn_customer_gateway" "aws_customer_gateway" {
  name        = "aws-customer-gateway"
  ip_address  = var.aws_vpn_gateway_ip
  description = "AWS侧VPN网关"
  
  tags = {
    Name      = "AWS-Customer-Gateway"
    Purpose   = "cross-cloud-connectivity"
    CreatedBy = "terraform"
  }
}

# 创建IPSec连接
resource "alicloud_vpn_connection" "cross_cloud_connection" {
  name                = "aws-cross-cloud-ipsec"
  vpn_gateway_id     = alicloud_vpn_gateway.cross_cloud_gateway.id
  customer_gateway_id = alicloud_vpn_customer_gateway.aws_customer_gateway.id
  local_subnet       = [var.local_subnet]
  remote_subnet      = [var.remote_subnet]
  effect_immediately = true
  
  # IKE配置
  ike_config {
    ike_auth_alg  = "sha256"
    ike_enc_alg   = "aes256"
    ike_version   = "ikev2"
    ike_mode      = "main"
    ike_lifetime  = 86400
    psk           = var.preshared_key
    ike_pfs       = "group14"
    remote_id     = var.aws_vpn_gateway_ip
    local_id      = alicloud_vpn_gateway.cross_cloud_gateway.internet_ip
  }
  
  # IPSec配置
  ipsec_config {
    ipsec_pfs      = "group14"
    ipsec_enc_alg  = "aes256"
    ipsec_auth_alg = "sha256"
    ipsec_lifetime = 3600
  }
  
  tags = {
    Name        = "AWS-Cross-Cloud-IPSec"
    Environment = "production"
    Purpose     = "cross-cloud-connectivity"
    CreatedBy   = "terraform"
  }
}

# 创建路由表条目
resource "alicloud_route_entry" "cross_cloud_route" {
  route_table_id        = data.alicloud_vpcs.default.vpcs.0.route_table_id
  destination_cidrblock = var.remote_subnet
  nexthop_type         = "VpnGateway"
  nexthop_id           = alicloud_vpn_gateway.cross_cloud_gateway.id
  
  depends_on = [alicloud_vpn_connection.cross_cloud_connection]
}

# 获取VPC信息
data "alicloud_vpcs" "default" {
  ids = [var.vpc_id]
}

# 创建安全组规则
resource "alicloud_security_group_rule" "allow_aws_traffic" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "1/65535"
  priority          = 1
  security_group_id = data.alicloud_security_groups.default.groups.0.id
  cidr_ip           = var.remote_subnet
  description       = "允许来自AWS VPC的流量"
}

resource "alicloud_security_group_rule" "allow_aws_icmp" {
  type              = "ingress"
  ip_protocol       = "icmp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "-1/-1"
  priority          = 1
  security_group_id = data.alicloud_security_groups.default.groups.0.id
  cidr_ip           = var.remote_subnet
  description       = "允许来自AWS VPC的ICMP流量"
}

# 获取默认安全组
data "alicloud_security_groups" "default" {
  vpc_id = var.vpc_id
  name_regex = "default"
}

# 创建VPN网关监控告警
resource "alicloud_cms_alarm" "vpn_connection_status" {
  name         = "vpn-connection-status-alarm"
  project      = "acs_vpn"
  metric       = "connection_status"
  dimensions = {
    instanceId = alicloud_vpn_connection.cross_cloud_connection.id
  }
  
  escalations_critical {
    statistics          = "Average"
    comparison_operator = "LessThanThreshold"
    threshold           = "1"
    times               = "3"
  }
  
  contact_groups = ["default"]
  effective_interval = "00:00-23:59"
  
  webhook = "https://hooks.dingtalk.com/services/YOUR_WEBHOOK_URL"
}

resource "alicloud_cms_alarm" "vpn_bandwidth_utilization" {
  name         = "vpn-bandwidth-utilization-alarm"
  project      = "acs_vpn"
  metric       = "bandwidth_utilization"
  dimensions = {
    instanceId = alicloud_vpn_gateway.cross_cloud_gateway.id
  }
  
  escalations_warn {
    statistics          = "Average"
    comparison_operator = "GreaterThanThreshold"
    threshold           = "80"
    times               = "3"
  }
  
  escalations_critical {
    statistics          = "Average"
    comparison_operator = "GreaterThanThreshold"
    threshold           = "95"
    times               = "2"
  }
  
  contact_groups = ["default"]
  effective_interval = "00:00-23:59"
}

# 输出重要信息
output "vpn_gateway_id" {
  description = "VPN网关ID"
  value       = alicloud_vpn_gateway.cross_cloud_gateway.id
}

output "vpn_gateway_public_ip" {
  description = "VPN网关公网IP"
  value       = alicloud_vpn_gateway.cross_cloud_gateway.internet_ip
}

output "vpn_connection_id" {
  description = "VPN连接ID"
  value       = alicloud_vpn_connection.cross_cloud_connection.id
}

output "customer_gateway_id" {
  description = "客户网关ID"
  value       = alicloud_vpn_customer_gateway.aws_customer_gateway.id
}

output "connection_status" {
  description = "连接状态"
  value       = alicloud_vpn_connection.cross_cloud_connection.status
}

output "tunnel_config" {
  description = "隧道配置信息"
  value = {
    local_subnet    = var.local_subnet
    remote_subnet   = var.remote_subnet
    ike_version     = "ikev2"
    encryption      = "aes256"
    authentication  = "sha256"
    pfs_group      = "group14"
  }
  sensitive = false
}

# 创建健康检查脚本
resource "local_file" "health_check_script" {
  content = templatefile("${path.module}/scripts/vpn_health_check.py.tpl", {
    vpn_connection_id = alicloud_vpn_connection.cross_cloud_connection.id
    aws_endpoints     = ["172.16.1.10", "172.16.1.11"]
    aliyun_region     = var.aliyun_region
    webhook_url       = "https://hooks.dingtalk.com/services/YOUR_WEBHOOK_URL"
  })
  filename = "${path.module}/scripts/vpn_health_check.py"
}

# 创建系统服务文件
resource "local_file" "systemd_service" {
  content = templatefile("${path.module}/scripts/vpn-monitor.service.tpl", {
    script_path = abspath("${path.module}/scripts/vpn_health_check.py")
  })
  filename = "${path.module}/scripts/vpn-monitor.service"
}

# 创建配置文件
resource "local_file" "vpn_config" {
  content = yamlencode({
    vpn_gateway = {
      id        = alicloud_vpn_gateway.cross_cloud_gateway.id
      public_ip = alicloud_vpn_gateway.cross_cloud_gateway.internet_ip
      bandwidth = "200Mbps"
    }
    vpn_connection = {
      id            = alicloud_vpn_connection.cross_cloud_connection.id
      status        = alicloud_vpn_connection.cross_cloud_connection.status
      local_subnet  = var.local_subnet
      remote_subnet = var.remote_subnet
    }
    monitoring = {
      enabled = true
      interval = "60s"
      alerts = {
        connection_down = true
        high_latency    = true
        bandwidth_util  = true
      }
    }
  })
  filename = "${path.module}/config/vpn-config.yaml"
}

# 创建部署文档
resource "local_file" "deployment_guide" {
  content = templatefile("${path.module}/docs/deployment-guide.md.tpl", {
    vpn_gateway_ip     = alicloud_vpn_gateway.cross_cloud_gateway.internet_ip
    preshared_key      = var.preshared_key
    local_subnet       = var.local_subnet
    remote_subnet      = var.remote_subnet
    vpn_connection_id  = alicloud_vpn_connection.cross_cloud_connection.id
  })
  filename = "${path.module}/docs/aliyun-deployment-guide.md"
}