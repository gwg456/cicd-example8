"""
监控和告警脚本
用于监控部署状态和应用性能
"""

import time
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlertConfig:
    """告警配置"""
    webhook_url: Optional[str] = None
    email_recipients: List[str] = None
    slack_channel: Optional[str] = None
    alert_threshold: int = 3  # 连续失败次数阈值

class DeploymentMonitor:
    """部署监控器"""
    
    def __init__(self, prefect_api_url: str, alert_config: AlertConfig):
        self.prefect_api_url = prefect_api_url.rstrip('/')
        self.alert_config = alert_config
        self.failure_count = 0
        self.last_alert_time = None
    
    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """获取部署状态"""
        try:
            response = requests.get(
                f"{self.prefect_api_url}/deployments",
                timeout=10
            )
            if response.status_code == 200:
                deployments = response.json()
                for deployment in deployments:
                    if deployment.get('name') == deployment_name:
                        return deployment
            return {}
        except Exception as e:
            logger.error(f"获取部署状态失败: {str(e)}")
            return {}
    
    def get_flow_runs(self, deployment_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近的流程运行记录"""
        try:
            since = datetime.now() - timedelta(hours=hours)
            response = requests.get(
                f"{self.prefect_api_url}/flow_runs",
                params={
                    'deployment_name': deployment_name,
                    'start_time': since.isoformat()
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"获取流程运行记录失败: {str(e)}")
            return []
    
    def check_deployment_health(self, deployment_name: str) -> bool:
        """检查部署健康状态"""
        deployment = self.get_deployment_status(deployment_name)
        if not deployment:
            logger.error(f"未找到部署: {deployment_name}")
            return False
        
        # 检查部署状态
        status = deployment.get('status', 'unknown')
        if status not in ['active', 'running']:
            logger.warning(f"部署状态异常: {status}")
            return False
        
        # 检查最近的流程运行
        flow_runs = self.get_flow_runs(deployment_name, hours=1)
        if not flow_runs:
            logger.warning("最近1小时内没有流程运行")
            return False
        
        # 检查失败率
        failed_runs = [run for run in flow_runs if run.get('state', {}).get('type') == 'FAILED']
        failure_rate = len(failed_runs) / len(flow_runs) if flow_runs else 0
        
        if failure_rate > 0.5:  # 失败率超过50%
            logger.error(f"流程失败率过高: {failure_rate:.2%}")
            return False
        
        logger.info(f"部署健康检查通过，失败率: {failure_rate:.2%}")
        return True
    
    def send_alert(self, message: str, level: str = "WARNING"):
        """发送告警"""
        timestamp = datetime.now().isoformat()
        alert_data = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "environment": "production"
        }
        
        # 发送到 Webhook
        if self.alert_config.webhook_url:
            try:
                response = requests.post(
                    self.alert_config.webhook_url,
                    json=alert_data,
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info("Webhook 告警发送成功")
                else:
                    logger.error(f"Webhook 告警发送失败: {response.status_code}")
            except Exception as e:
                logger.error(f"Webhook 告警发送异常: {str(e)}")
        
        # 发送到 Slack
        if self.alert_config.slack_channel:
            self._send_slack_alert(alert_data)
        
        # 发送邮件
        if self.alert_config.email_recipients:
            self._send_email_alert(alert_data)
        
        self.last_alert_time = datetime.now()
    
    def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """发送 Slack 告警"""
        # 这里需要配置 Slack Webhook URL
        slack_webhook = None  # 从环境变量获取
        
        if slack_webhook:
            try:
                slack_message = {
                    "channel": self.alert_config.slack_channel,
                    "text": f"[{alert_data['level']}] {alert_data['message']}",
                    "attachments": [{
                        "fields": [
                            {"title": "时间", "value": alert_data['timestamp'], "short": True},
                            {"title": "环境", "value": alert_data['environment'], "short": True}
                        ]
                    }]
                }
                
                response = requests.post(slack_webhook, json=slack_message, timeout=10)
                if response.status_code == 200:
                    logger.info("Slack 告警发送成功")
                else:
                    logger.error(f"Slack 告警发送失败: {response.status_code}")
            except Exception as e:
                logger.error(f"Slack 告警发送异常: {str(e)}")
    
    def _send_email_alert(self, alert_data: Dict[str, Any]):
        """发送邮件告警"""
        # 这里需要配置邮件服务
        # 可以使用 SMTP 或第三方服务如 SendGrid
        logger.info(f"邮件告警: {alert_data['message']}")
    
    def monitor_deployment(self, deployment_name: str, check_interval: int = 300):
        """持续监控部署"""
        logger.info(f"开始监控部署: {deployment_name}")
        
        while True:
            try:
                is_healthy = self.check_deployment_health(deployment_name)
                
                if is_healthy:
                    self.failure_count = 0
                    logger.info("部署健康检查通过")
                else:
                    self.failure_count += 1
                    logger.warning(f"部署健康检查失败，连续失败次数: {self.failure_count}")
                    
                    # 检查是否需要发送告警
                    if self.failure_count >= self.alert_config.alert_threshold:
                        # 避免重复告警
                        if (not self.last_alert_time or 
                            datetime.now() - self.last_alert_time > timedelta(minutes=30)):
                            self.send_alert(
                                f"部署 {deployment_name} 连续 {self.failure_count} 次健康检查失败",
                                "ERROR"
                            )
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("监控已停止")
                break
            except Exception as e:
                logger.error(f"监控过程中发生错误: {str(e)}")
                time.sleep(check_interval)

def main():
    """主函数"""
    import os
    
    # 从环境变量获取配置
    prefect_api_url = os.environ.get('PREFECT_API_URL')
    deployment_name = os.environ.get('DEPLOYMENT_NAME', 'prod-deployment')
    check_interval = int(os.environ.get('MONITOR_INTERVAL', '300'))
    
    if not prefect_api_url:
        logger.error("缺少 PREFECT_API_URL 环境变量")
        return
    
    # 配置告警
    alert_config = AlertConfig(
        webhook_url=os.environ.get('ALERT_WEBHOOK_URL'),
        slack_channel=os.environ.get('SLACK_CHANNEL'),
        email_recipients=os.environ.get('EMAIL_RECIPIENTS', '').split(','),
        alert_threshold=int(os.environ.get('ALERT_THRESHOLD', '3'))
    )
    
    # 创建监控器
    monitor = DeploymentMonitor(prefect_api_url, alert_config)
    
    # 开始监控
    monitor.monitor_deployment(deployment_name, check_interval)

if __name__ == "__main__":
    main()