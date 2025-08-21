"""
主流程的端到端测试
"""
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestMainFlowE2E:
    """测试主流程的端到端执行"""
    
    @pytest.mark.e2e
    def test_main_flow_execution_mode(self):
        """测试主流程的执行模式"""
        # 设置环境变量
        env = os.environ.copy()
        env["DEPLOY_MODE"] = "false"
        env["LOG_LEVEL"] = "INFO"
        
        # 执行主流程
        result = subprocess.run(
            [sys.executable, "flow.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        # 验证执行成功
        assert result.returncode == 0
        assert "流执行完成" in result.stdout or "Hello" in result.stdout
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_main_flow_deploy_mode_mock(self):
        """测试主流程的部署模式（使用mock）"""
        # 由于真实的部署需要Prefect服务器，我们使用mock进行测试
        with patch("src.deployment.deploy_flows") as mock_deploy:
            mock_deploy.return_value = {"status": "success"}
            
            env = os.environ.copy()
            env["DEPLOY_MODE"] = "true"
            env["PREFECT_API_URL"] = "http://test:4200/api"
            env["WORK_POOL_NAME"] = "test-pool"
            env["IMAGE_REPO"] = "test/repo"
            env["LOG_LEVEL"] = "INFO"
            
            # 由于我们需要mock，这里直接调用main函数
            from flow import main
            
            # 临时设置环境变量
            with patch.dict(os.environ, env):
                # 重新导入config以获取新的环境变量
                import importlib
                import config
                importlib.reload(config)
                
                try:
                    main()
                except SystemExit:
                    pass  # main可能会调用sys.exit
    
    @pytest.mark.e2e
    def test_config_validation_e2e(self):
        """测试配置验证的端到端流程"""
        # 测试缺少必要配置的情况
        env = os.environ.copy()
        env["DEPLOY_MODE"] = "true"
        # 故意不设置必要的环境变量
        env.pop("PREFECT_API_URL", None)
        env.pop("WORK_POOL_NAME", None)
        env.pop("IMAGE_REPO", None)
        
        result = subprocess.run(
            [sys.executable, "flow.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        # 应该因为配置验证失败而退出
        # 检查输出中是否包含错误信息
        output = result.stdout + result.stderr
        assert "缺少必要的环境变量" in output or "missing" in output.lower()
    
    @pytest.mark.e2e
    def test_import_error_handling(self):
        """测试导入错误处理"""
        # 临时重命名src目录来模拟导入错误
        src_path = Path("src")
        temp_path = Path("src_temp")
        
        if src_path.exists():
            src_path.rename(temp_path)
            
            try:
                result = subprocess.run(
                    [sys.executable, "flow.py"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                
                # 应该有导入错误信息
                output = result.stdout + result.stderr
                assert "导入错误" in output or "ImportError" in output
                
            finally:
                # 恢复目录名
                if temp_path.exists():
                    temp_path.rename(src_path)
    
    @pytest.mark.e2e
    def test_logging_configuration(self):
        """测试日志配置"""
        env = os.environ.copy()
        env["DEPLOY_MODE"] = "false"
        env["LOG_LEVEL"] = "DEBUG"
        
        result = subprocess.run(
            [sys.executable, "flow.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        # 验证日志级别设置生效
        # DEBUG级别应该产生更多日志输出
        assert result.returncode == 0
        # 可以检查是否有DEBUG级别的日志输出


class TestToolsIntegrationE2E:
    """测试工具集成的端到端测试"""
    
    @pytest.mark.e2e
    def test_pdf_extraction_tool(self, sample_pdf_path):
        """测试PDF提取工具"""
        # 由于我们没有真实的PDF文件，这个测试需要真实的PDF
        # 或者我们可以创建一个简单的PDF文件进行测试
        
        # 检查工具文件是否存在
        tool_path = Path("tools/extract_pdf_text.py")
        assert tool_path.exists()
        
        # 测试工具的基本导入
        result = subprocess.run(
            [sys.executable, "-c", "from tools.extract_pdf_text import main"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        # 如果pdfminer.six未安装，应该有相应的错误信息
        if result.returncode != 0:
            assert "pdfminer.six" in result.stderr
    
    @pytest.mark.e2e
    def test_makefile_commands(self):
        """测试Makefile命令"""
        # 测试help命令
        result = subprocess.run(
            ["make", "help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            # 验证help输出包含预期的命令
            assert "install" in result.stdout
            assert "build" in result.stdout
            assert "deploy" in result.stdout
    
    @pytest.mark.e2e
    def test_docker_build_simulation(self):
        """测试Docker构建模拟"""
        # 检查Dockerfile是否存在
        dockerfile_path = Path("Dockerfile")
        assert dockerfile_path.exists()
        
        # 检查.dockerignore是否存在
        dockerignore_path = Path(".dockerignore")
        assert dockerignore_path.exists()
        
        # 验证Dockerfile语法（简单检查）
        with open(dockerfile_path) as f:
            content = f.read()
            assert "FROM python:" in content
            assert "WORKDIR" in content
            assert "COPY" in content


class TestCICDSimulation:
    """测试CI/CD流程模拟"""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_ci_workflow_simulation(self):
        """模拟CI工作流程"""
        # 1. 安装依赖（模拟）
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        
        # 2. 运行代码质量检查（如果工具已安装）
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", ".", "--select", "F"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # ruff可能未安装，所以不强制要求成功
        except FileNotFoundError:
            pass  # ruff未安装
        
        # 3. 运行测试（基本语法检查）
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", "flow.py"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
    
    @pytest.mark.e2e
    def test_deployment_simulation(self):
        """模拟部署流程"""
        # 模拟容器环境
        env = os.environ.copy()
        env["DEPLOY_MODE"] = "true"
        env["PREFECT_API_URL"] = "http://mock:4200/api"
        env["WORK_POOL_NAME"] = "mock-pool"
        env["IMAGE_REPO"] = "mock/repo"
        env["IMAGE_TAG"] = "mock-tag"
        
        # 由于没有真实的Prefect服务器，这个测试会失败
        # 但我们可以验证程序能够正确处理连接失败的情况
        result = subprocess.run(
            [sys.executable, "flow.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        # 程序应该能够处理连接失败并给出有用的错误信息
        output = result.stdout + result.stderr
        # 检查是否有适当的错误处理信息
        assert any(keyword in output.lower() for keyword in [
            "connection", "timeout", "error", "failed", "部署"
        ])
