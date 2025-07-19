"""
健康检查脚本
用于验证部署后的应用状态
"""

import requests
import time
import sys
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthChecker:
    """健康检查器"""
    
    def __init__(self, prefect_api_url: str, timeout: int = 300):
        self.prefect_api_url = prefect_api_url.rstrip('/')
        self.timeout = timeout
        self.start_time = time.time()
    
    def check_prefect_api(self) -> bool:
        """检查 Prefect API 是否可用"""
        try:
            response = requests.get(f"{self.prefect_api_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("Prefect API 健康检查通过")
                return True
            else:
                logger.error(f"Prefect API 返回状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Prefect API 健康检查失败: {str(e)}")
            return False
    
    def check_work_pool(self, work_pool_name: str) -> bool:
        """检查工作池状态"""
        try:
            response = requests.get(
                f"{self.prefect_api_url}/work_pools/{work_pool_name}",
                timeout=10
            )
            if response.status_code == 200:
                pool_info = response.json()
                logger.info(f"工作池 {work_pool_name} 状态: {pool_info.get('status', 'unknown')}")
                return True
            else:
                logger.error(f"工作池 {work_pool_name} 检查失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"工作池检查失败: {str(e)}")
            return False
    
    def check_deployment(self, deployment_name: str) -> bool:
        """检查部署状态"""
        try:
            response = requests.get(
                f"{self.prefect_api_url}/deployments",
                timeout=10
            )
            if response.status_code == 200:
                deployments = response.json()
                for deployment in deployments:
                    if deployment.get('name') == deployment_name:
                        logger.info(f"部署 {deployment_name} 状态: {deployment.get('status', 'unknown')}")
                        return True
                logger.error(f"未找到部署: {deployment_name}")
                return False
            else:
                logger.error(f"部署检查失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"部署检查失败: {str(e)}")
            return False
    
    def run_health_checks(self, work_pool_name: str, deployment_name: str) -> bool:
        """运行完整的健康检查"""
        logger.info("开始健康检查...")
        
        checks = [
            ("Prefect API", lambda: self.check_prefect_api()),
            ("工作池", lambda: self.check_work_pool(work_pool_name)),
            ("部署", lambda: self.check_deployment(deployment_name))
        ]
        
        for check_name, check_func in checks:
            logger.info(f"检查 {check_name}...")
            if not check_func():
                logger.error(f"{check_name} 检查失败")
                return False
            
            # 检查超时
            if time.time() - self.start_time > self.timeout:
                logger.error("健康检查超时")
                return False
        
        logger.info("所有健康检查通过")
        return True

def main():
    """主函数"""
    import os
    
    # 从环境变量获取配置
    prefect_api_url = os.environ.get('PREFECT_API_URL')
    work_pool_name = os.environ.get('WORK_POOL_NAME', 'my-docker-pool2')
    deployment_name = os.environ.get('DEPLOYMENT_NAME', 'prod-deployment')
    timeout = int(os.environ.get('HEALTH_CHECK_TIMEOUT', '300'))
    
    if not prefect_api_url:
        logger.error("缺少 PREFECT_API_URL 环境变量")
        sys.exit(1)
    
    # 创建健康检查器
    checker = HealthChecker(prefect_api_url, timeout)
    
    # 运行健康检查
    if checker.run_health_checks(work_pool_name, deployment_name):
        logger.info("健康检查成功")
        sys.exit(0)
    else:
        logger.error("健康检查失败")
        sys.exit(1)

if __name__ == "__main__":
    main()