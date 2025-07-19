#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Jenkins API 文件上传和构建触发示例
支持通过REST API上传文件并触发参数化构建
作者: DevOps Team
版本: 1.0.0
"""

import os
import sys
import json
import time
import argparse
import requests
from urllib.parse import urljoin
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class JenkinsAPIClient:
    """Jenkins API客户端"""
    
    def __init__(self, jenkins_url, username, token):
        """
        初始化Jenkins客户端
        
        Args:
            jenkins_url: Jenkins服务器URL
            username: Jenkins用户名
            token: Jenkins API Token
        """
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = (username, token)
        self.session = requests.Session()
        self.session.auth = self.auth
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Jenkins-API-Client/1.0',
            'Accept': 'application/json'
        })
        
        logger.info(f"初始化Jenkins客户端: {self.jenkins_url}")
    
    def test_connection(self):
        """测试连接到Jenkins"""
        try:
            url = urljoin(self.jenkins_url, '/api/json')
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            server_info = response.json()
            logger.info(f"连接成功 - Jenkins版本: {server_info.get('version', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    def get_job_info(self, job_name):
        """获取任务信息"""
        try:
            url = urljoin(self.jenkins_url, f'/job/{job_name}/api/json')
            response = self.session.get(url)
            response.raise_for_status()
            
            job_info = response.json()
            logger.info(f"获取任务信息成功: {job_name}")
            return job_info
            
        except Exception as e:
            logger.error(f"获取任务信息失败: {e}")
            return None
    
    def get_job_parameters(self, job_name):
        """获取任务参数定义"""
        job_info = self.get_job_info(job_name)
        if not job_info:
            return None
        
        parameters = []
        for action in job_info.get('actions', []):
            if action.get('_class') == 'hudson.model.ParametersDefinitionProperty':
                for param_def in action.get('parameterDefinitions', []):
                    parameters.append({
                        'name': param_def.get('name'),
                        'type': param_def.get('type'),
                        'description': param_def.get('description'),
                        'defaultValue': param_def.get('defaultParameterValue', {}).get('value')
                    })
        
        logger.info(f"任务 {job_name} 有 {len(parameters)} 个参数")
        return parameters
    
    def trigger_build_with_files(self, job_name, parameters=None, files=None):
        """
        触发带文件参数的构建
        
        Args:
            job_name: 任务名称
            parameters: 构建参数字典
            files: 文件参数字典 {param_name: file_path}
        
        Returns:
            build_number: 构建编号
        """
        try:
            url = urljoin(self.jenkins_url, f'/job/{job_name}/buildWithParameters')
            
            # 准备表单数据
            data = parameters or {}
            files_data = {}
            
            # 处理文件参数
            if files:
                for param_name, file_path in files.items():
                    if os.path.exists(file_path):
                        files_data[param_name] = open(file_path, 'rb')
                        logger.info(f"添加文件参数: {param_name} = {file_path}")
                    else:
                        logger.warning(f"文件不存在: {file_path}")
            
            # 发送构建请求
            logger.info(f"触发构建: {job_name}")
            response = self.session.post(url, data=data, files=files_data)
            
            # 关闭文件句柄
            for f in files_data.values():
                f.close()
            
            if response.status_code == 201:
                # 从Location头获取构建URL
                location = response.headers.get('Location')
                if location:
                    # 等待一下让构建开始
                    time.sleep(2)
                    queue_item_id = location.split('/')[-2]
                    build_number = self.get_build_number_from_queue(queue_item_id)
                    logger.info(f"构建已触发，构建编号: {build_number}")
                    return build_number
                else:
                    logger.info("构建已触发，但无法获取构建编号")
                    return None
            else:
                logger.error(f"触发构建失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"触发构建异常: {e}")
            return None
    
    def get_build_number_from_queue(self, queue_item_id):
        """从队列项目获取构建编号"""
        try:
            url = urljoin(self.jenkins_url, f'/queue/item/{queue_item_id}/api/json')
            
            # 轮询等待构建开始
            for _ in range(30):  # 最多等待30秒
                response = self.session.get(url)
                if response.status_code == 200:
                    queue_item = response.json()
                    executable = queue_item.get('executable')
                    if executable:
                        return executable.get('number')
                time.sleep(1)
            
            logger.warning("无法从队列获取构建编号")
            return None
            
        except Exception as e:
            logger.error(f"获取构建编号失败: {e}")
            return None
    
    def get_build_status(self, job_name, build_number):
        """获取构建状态"""
        try:
            url = urljoin(self.jenkins_url, f'/job/{job_name}/{build_number}/api/json')
            response = self.session.get(url)
            response.raise_for_status()
            
            build_info = response.json()
            return {
                'building': build_info.get('building'),
                'result': build_info.get('result'),
                'duration': build_info.get('duration'),
                'timestamp': build_info.get('timestamp'),
                'url': build_info.get('url')
            }
            
        except Exception as e:
            logger.error(f"获取构建状态失败: {e}")
            return None
    
    def wait_for_build_completion(self, job_name, build_number, timeout=1800):
        """等待构建完成"""
        logger.info(f"等待构建完成: {job_name} #{build_number}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_build_status(job_name, build_number)
            if status:
                if not status['building']:
                    logger.info(f"构建完成: {status['result']}")
                    return status
                else:
                    logger.info("构建进行中...")
            
            time.sleep(10)  # 每10秒检查一次
        
        logger.warning("等待构建超时")
        return None
    
    def get_build_console_output(self, job_name, build_number):
        """获取构建控制台输出"""
        try:
            url = urljoin(self.jenkins_url, f'/job/{job_name}/{build_number}/consoleText')
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            logger.error(f"获取控制台输出失败: {e}")
            return None

def create_sample_files():
    """创建示例文件用于测试"""
    sample_dir = Path('./sample-files')
    sample_dir.mkdir(exist_ok=True)
    
    # 创建示例配置文件
    config_content = """
# 示例配置文件
app:
  name: sample-app
  version: 1.0.0
  environment: dev

database:
  host: localhost
  port: 3306
  name: sample_db

logging:
  level: DEBUG
"""
    
    config_file = sample_dir / 'config.yml'
    config_file.write_text(config_content.strip())
    
    # 创建示例SQL脚本
    sql_content = """
-- 示例数据库脚本
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, email) VALUES 
('admin', 'admin@example.com'),
('user1', 'user1@example.com');
"""
    
    sql_file = sample_dir / 'init.sql'
    sql_file.write_text(sql_content.strip())
    
    # 创建示例应用包 (空的JAR文件)
    jar_file = sample_dir / 'sample-app.jar'
    jar_file.write_bytes(b'PK\x03\x04')  # 简单的ZIP文件头
    
    logger.info(f"示例文件已创建在: {sample_dir}")
    return {
        'config': str(config_file),
        'sql': str(sql_file),
        'jar': str(jar_file)
    }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Jenkins API 文件上传构建工具')
    parser.add_argument('--jenkins-url', required=True, help='Jenkins服务器URL')
    parser.add_argument('--username', required=True, help='Jenkins用户名')
    parser.add_argument('--token', required=True, help='Jenkins API Token')
    parser.add_argument('--job-name', required=True, help='Jenkins任务名称')
    parser.add_argument('--project-name', default='sample-app', help='项目名称')
    parser.add_argument('--app-version', default='1.0.0', help='应用版本')
    parser.add_argument('--environment', default='dev', help='部署环境')
    parser.add_argument('--config-file', help='配置文件路径')
    parser.add_argument('--package-file', help='应用包文件路径')
    parser.add_argument('--sql-file', help='SQL脚本文件路径')
    parser.add_argument('--create-samples', action='store_true', help='创建示例文件')
    parser.add_argument('--wait', action='store_true', help='等待构建完成')
    parser.add_argument('--show-log', action='store_true', help='显示构建日志')
    
    args = parser.parse_args()
    
    # 创建示例文件
    if args.create_samples:
        sample_files = create_sample_files()
        logger.info("示例文件已创建，可以使用以下参数:")
        logger.info(f"  --config-file {sample_files['config']}")
        logger.info(f"  --package-file {sample_files['jar']}")
        logger.info(f"  --sql-file {sample_files['sql']}")
        return
    
    # 初始化Jenkins客户端
    client = JenkinsAPIClient(args.jenkins_url, args.username, args.token)
    
    # 测试连接
    if not client.test_connection():
        logger.error("无法连接到Jenkins服务器")
        return 1
    
    # 获取任务参数信息
    parameters = client.get_job_parameters(args.job_name)
    if parameters:
        logger.info("任务参数:")
        for param in parameters:
            logger.info(f"  - {param['name']} ({param['type']}): {param['description']}")
    
    # 准备构建参数
    build_params = {
        'PROJECT_NAME': args.project_name,
        'APP_VERSION': args.app_version,
        'ENVIRONMENT': args.environment,
        'DEPLOYMENT_NOTES': f'API构建 - {time.strftime("%Y-%m-%d %H:%M:%S")}'
    }
    
    # 准备文件参数
    files = {}
    if args.config_file and os.path.exists(args.config_file):
        files['CONFIG_FILE'] = args.config_file
    if args.package_file and os.path.exists(args.package_file):
        files['APPLICATION_PACKAGE'] = args.package_file
    if args.sql_file and os.path.exists(args.sql_file):
        files['DATABASE_SCRIPTS'] = args.sql_file
    
    if not files:
        logger.warning("没有指定任何文件，将触发无文件构建")
    
    # 触发构建
    build_number = client.trigger_build_with_files(
        job_name=args.job_name,
        parameters=build_params,
        files=files
    )
    
    if not build_number:
        logger.error("构建触发失败")
        return 1
    
    logger.info(f"构建已触发: {args.job_name} #{build_number}")
    logger.info(f"构建URL: {args.jenkins_url}/job/{args.job_name}/{build_number}/")
    
    # 等待构建完成
    if args.wait:
        final_status = client.wait_for_build_completion(args.job_name, build_number)
        if final_status:
            logger.info(f"构建最终状态: {final_status['result']}")
            logger.info(f"构建耗时: {final_status['duration']/1000:.1f}秒")
            
            # 显示构建日志
            if args.show_log:
                console_output = client.get_build_console_output(args.job_name, build_number)
                if console_output:
                    print("\n" + "="*50)
                    print("构建控制台输出:")
                    print("="*50)
                    print(console_output)
            
            return 0 if final_status['result'] == 'SUCCESS' else 1
        else:
            logger.error("无法获取构建最终状态")
            return 1
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1)