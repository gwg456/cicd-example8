# AWS VPN网关配置
# 用于与阿里云建立跨云IPSec VPN连接

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

# 配置AWS Provider
provider "aws" {
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
  region     = var.aws_region
}

# 变量定义
variable "aws_access_key" {
  description = "AWS Access Key"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS Secret Key"
  type        = string
  sensitive   = true
}

variable "aws_region" {
  description = "AWS区域"
  type        = string
  default     = "us-west-1"
}

variable "aliyun_vpn_gateway_ip" {
  description = "阿里云VPN网关公网IP"
  type        = string
}

variable "vpc_id" {
  description = "AWS VPC ID"
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
  default     = "172.16.0.0/16"
}

variable "remote_subnet" {
  description = "远程子网CIDR"
  type        = string
  default     = "10.0.0.0/16"
}

variable "bgp_asn" {
  description = "BGP ASN"
  type        = number
  default     = 65000
}

# 获取VPC信息
data "aws_vpc" "selected" {
  id = var.vpc_id
}

# 获取路由表
data "aws_route_tables" "vpc_route_tables" {
  vpc_id = var.vpc_id
}

# 创建Virtual Private Gateway
resource "aws_vpn_gateway" "cross_cloud_vgw" {
  vpc_id          = var.vpc_id
  amazon_side_asn = var.bgp_asn

  tags = {
    Name        = "aliyun-cross-cloud-vgw"
    Environment = "production"
    Purpose     = "cross-cloud-connectivity"
    CreatedBy   = "terraform"
  }
}

# 创建Customer Gateway (阿里云侧)
resource "aws_customer_gateway" "aliyun_customer_gateway" {
  bgp_asn    = var.bgp_asn
  ip_address = var.aliyun_vpn_gateway_ip
  type       = "ipsec.1"

  tags = {
    Name      = "aliyun-customer-gateway"
    Purpose   = "cross-cloud-connectivity"
    CreatedBy = "terraform"
  }
}

# 创建VPN连接
resource "aws_vpn_connection" "cross_cloud_vpn" {
  vpn_gateway_id      = aws_vpn_gateway.cross_cloud_vgw.id
  customer_gateway_id = aws_customer_gateway.aliyun_customer_gateway.id
  type                = "ipsec.1"
  static_routes_only  = true

  tags = {
    Name        = "aliyun-cross-cloud-vpn"
    Environment = "production"
    Purpose     = "cross-cloud-connectivity"
    CreatedBy   = "terraform"
  }
}

# 创建VPN连接静态路由
resource "aws_vpn_connection_route" "aliyun_route" {
  vpn_connection_id      = aws_vpn_connection.cross_cloud_vpn.id
  destination_cidr_block = var.remote_subnet
}

# 启用路由传播
resource "aws_vpn_gateway_route_propagation" "main" {
  count          = length(data.aws_route_tables.vpc_route_tables.ids)
  vpn_gateway_id = aws_vpn_gateway.cross_cloud_vgw.id
  route_table_id = data.aws_route_tables.vpc_route_tables.ids[count.index]
}

# 创建安全组规则
resource "aws_security_group" "cross_cloud_sg" {
  name_prefix = "cross-cloud-"
  vpc_id      = var.vpc_id
  description = "Security group for cross-cloud connectivity"

  # 允许来自阿里云VPC的入站流量
  ingress {
    description = "Allow traffic from Aliyun VPC"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.remote_subnet]
  }

  ingress {
    description = "Allow ICMP from Aliyun VPC"
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = [var.remote_subnet]
  }

  # 允许所有出站流量
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "cross-cloud-security-group"
    Purpose   = "cross-cloud-connectivity"
    CreatedBy = "terraform"
  }
}

# 创建CloudWatch告警
resource "aws_cloudwatch_metric_alarm" "vpn_tunnel_state" {
  count               = 2
  alarm_name          = "vpn-tunnel-${count.index + 1}-down"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TunnelState"
  namespace           = "AWS/VPN"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "1"
  alarm_description   = "This metric monitors VPN tunnel state"
  alarm_actions       = [aws_sns_topic.vpn_alerts.arn]

  dimensions = {
    VpnId   = aws_vpn_connection.cross_cloud_vpn.id
    TunnelIpAddress = aws_vpn_connection.cross_cloud_vpn.tunnel1_address
  }

  tags = {
    Name      = "vpn-tunnel-${count.index + 1}-alarm"
    Purpose   = "cross-cloud-monitoring"
    CreatedBy = "terraform"
  }
}

resource "aws_cloudwatch_metric_alarm" "vpn_tunnel_packets" {
  alarm_name          = "vpn-tunnel-low-packets"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "TunnelPacketsReceived"
  namespace           = "AWS/VPN"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors VPN tunnel packet flow"
  treat_missing_data  = "breaching"

  dimensions = {
    VpnId = aws_vpn_connection.cross_cloud_vpn.id
  }

  tags = {
    Name      = "vpn-packets-alarm"
    Purpose   = "cross-cloud-monitoring"
    CreatedBy = "terraform"
  }
}

# 创建SNS主题用于告警
resource "aws_sns_topic" "vpn_alerts" {
  name = "vpn-cross-cloud-alerts"

  tags = {
    Name      = "vpn-alerts-topic"
    Purpose   = "cross-cloud-monitoring"
    CreatedBy = "terraform"
  }
}

# 创建SNS订阅 (邮件)
resource "aws_sns_topic_subscription" "vpn_email_alerts" {
  topic_arn = aws_sns_topic.vpn_alerts.arn
  protocol  = "email"
  endpoint  = "admin@example.com" # 替换为实际邮箱地址
}

# 创建Lambda函数用于自定义告警处理
resource "aws_lambda_function" "vpn_monitor" {
  filename         = "vpn_monitor.zip"
  function_name    = "cross-cloud-vpn-monitor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 60

  environment {
    variables = {
      VPN_CONNECTION_ID = aws_vpn_connection.cross_cloud_vpn.id
      ALIYUN_ENDPOINTS  = "172.16.1.10,172.16.1.11"
      WEBHOOK_URL       = "https://hooks.dingtalk.com/services/YOUR_WEBHOOK_URL"
    }
  }

  tags = {
    Name      = "vpn-monitor-lambda"
    Purpose   = "cross-cloud-monitoring"
    CreatedBy = "terraform"
  }
}

# 创建Lambda代码包
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "vpn_monitor.zip"
  source {
    content = templatefile("${path.module}/scripts/lambda_monitor.py.tpl", {
      vpn_connection_id = aws_vpn_connection.cross_cloud_vpn.id
    })
    filename = "index.py"
  }
}

# 创建Lambda IAM角色
resource "aws_iam_role" "lambda_role" {
  name = "cross-cloud-vpn-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name      = "lambda-vpn-monitor-role"
    Purpose   = "cross-cloud-monitoring"
    CreatedBy = "terraform"
  }
}

# 创建Lambda IAM策略
resource "aws_iam_role_policy" "lambda_policy" {
  name = "cross-cloud-vpn-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeVpnConnections",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# 创建EventBridge规则定期执行Lambda
resource "aws_cloudwatch_event_rule" "vpn_monitor_schedule" {
  name                = "vpn-monitor-schedule"
  description         = "Trigger VPN monitor Lambda function"
  schedule_expression = "rate(5 minutes)"

  tags = {
    Name      = "vpn-monitor-schedule"
    Purpose   = "cross-cloud-monitoring"
    CreatedBy = "terraform"
  }
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.vpn_monitor_schedule.name
  target_id = "TriggerLambdaFunction"
  arn       = aws_lambda_function.vpn_monitor.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.vpn_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.vpn_monitor_schedule.arn
}

# 输出重要信息
output "vpn_gateway_id" {
  description = "VPN网关ID"
  value       = aws_vpn_gateway.cross_cloud_vgw.id
}

output "vpn_connection_id" {
  description = "VPN连接ID"
  value       = aws_vpn_connection.cross_cloud_vpn.id
}

output "customer_gateway_id" {
  description = "客户网关ID"
  value       = aws_customer_gateway.aliyun_customer_gateway.id
}

output "tunnel1_address" {
  description = "隧道1地址"
  value       = aws_vpn_connection.cross_cloud_vpn.tunnel1_address
}

output "tunnel2_address" {
  description = "隧道2地址"
  value       = aws_vpn_connection.cross_cloud_vpn.tunnel2_address
}

output "tunnel1_preshared_key" {
  description = "隧道1预共享密钥"
  value       = aws_vpn_connection.cross_cloud_vpn.tunnel1_preshared_key
  sensitive   = true
}

output "tunnel2_preshared_key" {
  description = "隧道2预共享密钥"
  value       = aws_vpn_connection.cross_cloud_vpn.tunnel2_preshared_key
  sensitive   = true
}

output "vpn_connection_status" {
  description = "VPN连接状态"
  value       = aws_vpn_connection.cross_cloud_vpn.state
}

output "security_group_id" {
  description = "安全组ID"
  value       = aws_security_group.cross_cloud_sg.id
}

output "tunnel_config" {
  description = "隧道配置信息"
  value = {
    tunnel1 = {
      address    = aws_vpn_connection.cross_cloud_vpn.tunnel1_address
      bgp_asn    = aws_vpn_connection.cross_cloud_vpn.tunnel1_bgp_asn
      inside_cidr = aws_vpn_connection.cross_cloud_vpn.tunnel1_inside_cidr
    }
    tunnel2 = {
      address    = aws_vpn_connection.cross_cloud_vpn.tunnel2_address
      bgp_asn    = aws_vpn_connection.cross_cloud_vpn.tunnel2_bgp_asn
      inside_cidr = aws_vpn_connection.cross_cloud_vpn.tunnel2_inside_cidr
    }
    encryption      = "aes256"
    authentication  = "sha256"
    pfs_group      = "group14"
    ike_version    = "ikev2"
  }
  sensitive = false
}

# 创建配置文件
resource "local_file" "aws_vpn_config" {
  content = yamlencode({
    vpn_gateway = {
      id     = aws_vpn_gateway.cross_cloud_vgw.id
      asn    = var.bgp_asn
      vpc_id = var.vpc_id
    }
    vpn_connection = {
      id            = aws_vpn_connection.cross_cloud_vpn.id
      status        = aws_vpn_connection.cross_cloud_vpn.state
      tunnel1 = {
        address         = aws_vpn_connection.cross_cloud_vpn.tunnel1_address
        preshared_key   = aws_vpn_connection.cross_cloud_vpn.tunnel1_preshared_key
        inside_cidr     = aws_vpn_connection.cross_cloud_vpn.tunnel1_inside_cidr
        bgp_asn         = aws_vpn_connection.cross_cloud_vpn.tunnel1_bgp_asn
      }
      tunnel2 = {
        address         = aws_vpn_connection.cross_cloud_vpn.tunnel2_address
        preshared_key   = aws_vpn_connection.cross_cloud_vpn.tunnel2_preshared_key
        inside_cidr     = aws_vpn_connection.cross_cloud_vpn.tunnel2_inside_cidr
        bgp_asn         = aws_vpn_connection.cross_cloud_vpn.tunnel2_bgp_asn
      }
    }
    customer_gateway = {
      id         = aws_customer_gateway.aliyun_customer_gateway.id
      ip_address = var.aliyun_vpn_gateway_ip
      bgp_asn    = var.bgp_asn
    }
    security_group = {
      id   = aws_security_group.cross_cloud_sg.id
      name = aws_security_group.cross_cloud_sg.name
    }
    monitoring = {
      sns_topic_arn = aws_sns_topic.vpn_alerts.arn
      lambda_function = aws_lambda_function.vpn_monitor.function_name
      cloudwatch_alarms = [
        aws_cloudwatch_metric_alarm.vpn_tunnel_state[0].alarm_name,
        aws_cloudwatch_metric_alarm.vpn_tunnel_state[1].alarm_name,
        aws_cloudwatch_metric_alarm.vpn_tunnel_packets.alarm_name
      ]
    }
  })
  filename = "${path.module}/config/aws-vpn-config.yaml"
}

# 创建部署文档
resource "local_file" "aws_deployment_guide" {
  content = templatefile("${path.module}/docs/aws-deployment-guide.md.tpl", {
    vpn_connection_id     = aws_vpn_connection.cross_cloud_vpn.id
    tunnel1_address       = aws_vpn_connection.cross_cloud_vpn.tunnel1_address
    tunnel2_address       = aws_vpn_connection.cross_cloud_vpn.tunnel2_address
    tunnel1_preshared_key = aws_vpn_connection.cross_cloud_vpn.tunnel1_preshared_key
    tunnel2_preshared_key = aws_vpn_connection.cross_cloud_vpn.tunnel2_preshared_key
    local_subnet          = var.local_subnet
    remote_subnet         = var.remote_subnet
    security_group_id     = aws_security_group.cross_cloud_sg.id
  })
  filename = "${path.module}/docs/aws-deployment-guide.md"
}

# 创建测试脚本
resource "local_file" "connectivity_test" {
  content = templatefile("${path.module}/scripts/connectivity_test.sh.tpl", {
    aws_test_endpoints    = ["172.16.1.10", "172.16.1.11"]
    aliyun_test_endpoints = ["10.0.1.10", "10.0.1.11"]
    vpn_connection_id     = aws_vpn_connection.cross_cloud_vpn.id
  })
  filename = "${path.module}/scripts/connectivity_test.sh"
}

# 创建CloudFormation模板
resource "local_file" "cloudformation_template" {
  content = templatefile("${path.module}/templates/vpn-stack.yaml.tpl", {
    vpc_id                = var.vpc_id
    aliyun_gateway_ip     = var.aliyun_vpn_gateway_ip
    bgp_asn              = var.bgp_asn
    remote_subnet        = var.remote_subnet
  })
  filename = "${path.module}/templates/aws-vpn-stack.yaml"
}