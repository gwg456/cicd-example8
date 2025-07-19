"""
回滚脚本
用于在部署失败时快速回滚到上一个稳定版本
"""

import os
import sys
import logging
import subprocess
import requests
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RollbackManager:
    """回滚管理器"""
    
    def __init__(self, prefect_api_url: str, image_repo: str, work_pool_name: str):
        self.prefect_api_url = prefect_api_url.rstrip('/')
        self.image_repo = image_repo
        self.work_pool_name = work_pool_name
    
    def get_available_versions(self) -> List[str]:
        """获取可用的镜像版本"""
        try:
            # 使用 Docker CLI 获取镜像标签
            result = subprocess.run(
                ['docker', 'images', self.image_repo, '--format', '{{.Tag}}'],
                capture_output=True,
                text=True,
                check=True
            )
            
            versions = [tag.strip() for tag in result.stdout.split('\n') if tag.strip() and tag != 'latest']
            # 按时间排序，最新的在前面
            versions.sort(reverse=True)
            return versions
        except subprocess.CalledProcessError as e:
            logger.error(f"获取镜像版本失败: {str(e)}")
            return []
    
    def get_deployment_info(self, deployment_name: str) -> Optional[Dict[str, Any]]:
        """获取部署信息"""
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
            return None
        except Exception as e:
            logger.error(f"获取部署信息失败: {str(e)}")
            return None
    
    def check_version_health(self, version: str) -> bool:
        """检查版本的健康状态"""
        try:
            # 运行健康检查
            result = subprocess.run([
                'docker', 'run', '--rm',
                '-e', f'PREFECT_API_URL={self.prefect_api_url}',
                '-e', f'WORK_POOL_NAME={self.work_pool_name}',
                '-e', 'DEPLOYMENT_NAME=prod-deployment',
                '-e', 'HEALTH_CHECK_TIMEOUT=60',
                f'{self.image_repo}:{version}',
                'python', 'deployment/health_check.py'
            ], capture_output=True, text=True, timeout=120)
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"检查版本 {version} 健康状态失败: {str(e)}")
            return False
    
    def rollback_to_version(self, target_version: str, deployment_name: str) -> bool:
        """回滚到指定版本"""
        logger.info(f"开始回滚到版本: {target_version}")
        
        try:
            # 1. 验证目标版本是否存在
            available_versions = self.get_available_versions()
            if target_version not in available_versions:
                logger.error(f"目标版本 {target_version} 不存在")
                return False
            
            # 2. 检查目标版本的健康状态
            logger.info(f"检查版本 {target_version} 的健康状态...")
            if not self.check_version_health(target_version):
                logger.error(f"版本 {target_version} 健康检查失败")
                return False
            
            # 3. 执行回滚部署
            logger.info("执行回滚部署...")
            result = subprocess.run([
                'docker', 'run', '--rm',
                '-e', f'PREFECT_API_URL={self.prefect_api_url}',
                '-e', f'IMAGE_REPO={self.image_repo}',
                '-e', f'IMAGE_TAG={target_version}',
                '-e', f'WORK_POOL_NAME={self.work_pool_name}',
                '-e', 'DEPLOY_MODE=true',
                '-e', 'ENVIRONMENT=production',
                '-v', '/var/run/docker.sock:/var/run/docker.sock',
                f'{self.image_repo}:{target_version}'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"回滚部署失败: {result.stderr}")
                return False
            
            # 4. 验证回滚结果
            logger.info("验证回滚结果...")
            time.sleep(30)  # 等待部署完成
            
            deployment_info = self.get_deployment_info(deployment_name)
            if not deployment_info:
                logger.error("无法获取部署信息")
                return False
            
            logger.info(f"回滚成功，当前部署状态: {deployment_info.get('status', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"回滚过程中发生错误: {str(e)}")
            return False
    
    def auto_rollback(self, deployment_name: str, max_attempts: int = 3) -> bool:
        """自动回滚到最近的稳定版本"""
        logger.info("开始自动回滚...")
        
        available_versions = self.get_available_versions()
        if not available_versions:
            logger.error("没有可用的版本进行回滚")
            return False
        
        # 尝试最近的几个版本
        for i, version in enumerate(available_versions[:max_attempts]):
            logger.info(f"尝试回滚到版本 {version} (第 {i+1} 次尝试)")
            
            if self.rollback_to_version(version, deployment_name):
                logger.info(f"自动回滚成功，回滚到版本: {version}")
                return True
            else:
                logger.warning(f"回滚到版本 {version} 失败，尝试下一个版本")
        
        logger.error("自动回滚失败，所有尝试的版本都无法正常工作")
        return False
    
    def create_rollback_point(self, current_version: str) -> bool:
        """创建回滚点"""
        try:
            # 标记当前版本为稳定版本
            result = subprocess.run([
                'docker', 'tag',
                f'{self.image_repo}:{current_version}',
                f'{self.image_repo}:stable-{datetime.now().strftime("%Y%m%d%H%M")}'
            ], capture_output=True, text=True, check=True)
            
            logger.info(f"创建回滚点: stable-{datetime.now().strftime('%Y%m%d%H%M')}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"创建回滚点失败: {str(e)}")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='部署回滚工具')
    parser.add_argument('--action', choices=['rollback', 'auto-rollback', 'list-versions'], 
                       required=True, help='执行的操作')
    parser.add_argument('--version', help='回滚到的版本')
    parser.add_argument('--deployment-name', default='prod-deployment', 
                       help='部署名称')
    parser.add_argument('--max-attempts', type=int, default=3, 
                       help='自动回滚最大尝试次数')
    
    args = parser.parse_args()
    
    # 从环境变量获取配置
    prefect_api_url = os.environ.get('PREFECT_API_URL')
    image_repo = os.environ.get('IMAGE_REPO')
    work_pool_name = os.environ.get('WORK_POOL_NAME', 'production-docker-pool')
    
    if not all([prefect_api_url, image_repo]):
        logger.error("缺少必要的环境变量: PREFECT_API_URL, IMAGE_REPO")
        sys.exit(1)
    
    # 创建回滚管理器
    rollback_manager = RollbackManager(prefect_api_url, image_repo, work_pool_name)
    
    if args.action == 'list-versions':
        versions = rollback_manager.get_available_versions()
        print("可用的版本:")
        for version in versions:
            print(f"  - {version}")
    
    elif args.action == 'rollback':
        if not args.version:
            logger.error("回滚操作需要指定 --version 参数")
            sys.exit(1)
        
        success = rollback_manager.rollback_to_version(args.version, args.deployment_name)
        sys.exit(0 if success else 1)
    
    elif args.action == 'auto-rollback':
        success = rollback_manager.auto_rollback(args.deployment_name, args.max_attempts)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()