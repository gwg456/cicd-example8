"""
Production-grade Prefect deployment management module
"""
import asyncio
import datetime
import logging
import signal
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from prefect.client.orchestration import get_client
from prefect.deployments import Deployment
from prefect.exceptions import PrefectException

from src.config import get_settings
from src.core import (
    retry_with_backoff,
    async_retry_with_backoff,
    circuit_breaker,
    CircuitBreaker,
    DeploymentError,
    ConnectionError as AppConnectionError,
    TimeoutError as AppTimeoutError,
    ConfigurationError,
)
from src.flows import hello_flow, health_check_flow
from src.monitoring import metrics

logger = logging.getLogger(__name__)
settings = get_settings()


class DeploymentManager:
    """Production-grade deployment manager with error handling and monitoring"""
    
    def __init__(self):
        self.settings = settings
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            expected_exception=(PrefectException, AppConnectionError),
            name="prefect_api"
        )
        
        # Apply Prefect settings to environment
        self._apply_prefect_settings()
        
        # Print configuration if not in production
        if not self.settings.is_production:
            self.settings.print_config_summary()
    
    def _apply_prefect_settings(self):
        """Apply Prefect settings to environment"""
        import os
        for key, value in self.settings.get_prefect_settings().items():
            if value is not None:
                os.environ[key] = str(value)
    
    def _generate_image_tag(self) -> str:
        """Generate Docker image tag"""
        if self.settings.image_tag:
            return self.settings.full_image_name
        
        # Generate timestamp-based tag
        current_time = datetime.datetime.now()
        version_tag = f"v{current_time.strftime('%Y%m%d%H%M')}"
        return f"{self.settings.image_repo}:{version_tag}"
    
    @async_retry_with_backoff(max_attempts=3, max_delay=10)
    async def check_prefect_connection(self) -> bool:
        """
        Check Prefect API connection with retry logic
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with get_client() as client:
                await asyncio.wait_for(
                    client.api_healthcheck(),
                    timeout=self.settings.api_timeout
                )
                logger.info("✅ Prefect API connection successful")
                metrics.record_api_call("prefect_healthcheck", success=True)
                return True
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Prefect API connection timeout ({self.settings.api_timeout}s)")
            metrics.record_api_call("prefect_healthcheck", success=False)
            raise AppTimeoutError(
                "Prefect API connection timeout",
                timeout=self.settings.api_timeout,
                operation="healthcheck"
            )
        except Exception as e:
            logger.error(f"❌ Prefect API connection failed: {str(e)}")
            metrics.record_api_call("prefect_healthcheck", success=False)
            raise AppConnectionError(
                f"Failed to connect to Prefect API: {str(e)}",
                service="prefect_api"
            )
    
    @asynccontextmanager
    async def _timeout_context(self, timeout: int, operation: str):
        """Context manager for operation timeouts"""
        try:
            yield
        except asyncio.TimeoutError:
            raise AppTimeoutError(
                f"{operation} timed out",
                timeout=timeout,
                operation=operation
            )
    
    async def _validate_work_pool(self, client, work_pool_name: str) -> bool:
        """
        Validate that work pool exists
        
        Args:
            client: Prefect client
            work_pool_name: Name of work pool to validate
        
        Returns:
            True if work pool exists
        
        Raises:
            DeploymentError: If work pool doesn't exist
        """
        try:
            work_pools = await client.read_work_pools()
            pool_names = [pool.name for pool in work_pools]
            
            if work_pool_name not in pool_names:
                available_pools = ", ".join(pool_names) if pool_names else "None"
                raise DeploymentError(
                    f"Work pool '{work_pool_name}' not found",
                    available_pools=available_pools
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to validate work pool: {e}")
            raise
    
    @circuit_breaker(failure_threshold=3, recovery_timeout=60)
    @retry_with_backoff(max_attempts=3, max_delay=30)
    async def deploy_flow(
        self,
        flow,
        name: str,
        schedule: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Deploy a single flow with comprehensive error handling
        
        Args:
            flow: The Prefect flow to deploy
            name: Deployment name
            schedule: Schedule configuration
            tags: Deployment tags
            description: Deployment description
            **kwargs: Additional deployment parameters
        
        Returns:
            Deployment ID
        
        Raises:
            DeploymentError: If deployment fails
        """
        start_time = datetime.datetime.now()
        deployment_id = None
        
        try:
            # Validate configuration
            issues = self.settings.validate_deployment_requirements()
            if issues:
                raise ConfigurationError(
                    "Invalid deployment configuration",
                    missing_keys=issues
                )
            
            # Check Prefect connection
            if not await self.check_prefect_connection():
                raise AppConnectionError(
                    "Cannot establish connection to Prefect API",
                    service="prefect_api"
                )
            
            # Validate work pool
            async with get_client() as client:
                await self._validate_work_pool(client, self.settings.work_pool_name)
            
            # Generate image tag
            image_tag = self._generate_image_tag()
            
            # Get job variables
            job_variables = self.settings.get_docker_job_variables()
            
            logger.info(f"🚀 Deploying flow '{name}'")
            logger.info(f"📦 Image: {image_tag}")
            logger.info(f"🏊 Work pool: {self.settings.work_pool_name}")
            
            # Set up deployment parameters
            deploy_params = {
                "name": name,
                "work_pool_name": self.settings.work_pool_name,
                "image": image_tag,
                "job_variables": job_variables,
                "tags": tags or [],
                "description": description,
            }
            
            if schedule:
                deploy_params["schedule"] = schedule
            
            # Add any additional parameters
            deploy_params.update(kwargs)
            
            # Skip Docker operations in container environment
            if self.settings.is_container_env:
                logger.info("📦 Container environment detected, skipping Docker build")
                deploy_params["build"] = False
                deploy_params["push"] = False
            
            # Deploy with timeout
            async with self._timeout_context(
                self.settings.deployment_timeout,
                f"Deployment of {name}"
            ):
                deployment_id = await asyncio.to_thread(
                    flow.deploy,
                    **deploy_params
                )
            
            # Record metrics
            duration = (datetime.datetime.now() - start_time).total_seconds()
            metrics.record_deployment(name, success=True, duration=duration)
            
            logger.info(f"✅ Flow '{name}' deployed successfully")
            logger.info(f"🆔 Deployment ID: {deployment_id}")
            
            return deployment_id
            
        except Exception as e:
            # Record failure metrics
            duration = (datetime.datetime.now() - start_time).total_seconds()
            metrics.record_deployment(name, success=False, duration=duration)
            
            # Log detailed error information
            self._log_deployment_error(e, name)
            
            # Wrap in DeploymentError if not already
            if not isinstance(e, DeploymentError):
                raise DeploymentError(
                    f"Failed to deploy flow '{name}': {str(e)}",
                    deployment_id=deployment_id,
                    flow_name=name
                )
            raise
    
    def _log_deployment_error(self, error: Exception, flow_name: str):
        """Log detailed error information with troubleshooting tips"""
        error_msg = str(error).lower()
        
        logger.error(f"❌ Deployment failed for '{flow_name}': {error}")
        
        # Provide specific troubleshooting guidance
        if "timeout" in error_msg:
            logger.info("💡 Troubleshooting tips for timeout errors:")
            logger.info("  1. Check network connectivity to Prefect API")
            logger.info("  2. Increase API_TIMEOUT or DEPLOYMENT_TIMEOUT")
            logger.info("  3. Check if Prefect server is under heavy load")
        elif "work_pool" in error_msg or "pool" in error_msg:
            logger.info("💡 Troubleshooting tips for work pool errors:")
            logger.info("  1. Verify work pool exists: prefect work-pool ls")
            logger.info("  2. Create work pool: prefect work-pool create <name>")
            logger.info("  3. Check work pool configuration and status")
        elif "auth" in error_msg or "unauthorized" in error_msg:
            logger.info("💡 Troubleshooting tips for authentication errors:")
            logger.info("  1. Verify PREFECT_API_KEY is set correctly")
            logger.info("  2. Check API key permissions")
            logger.info("  3. Ensure user has deployment permissions")
        elif "docker" in error_msg:
            logger.info("💡 Troubleshooting tips for Docker errors:")
            logger.info("  1. Verify Docker daemon is running")
            logger.info("  2. Check Docker registry credentials")
            logger.info("  3. Ensure image exists and is accessible")
        elif "connection" in error_msg:
            logger.info("💡 Troubleshooting tips for connection errors:")
            logger.info("  1. Verify PREFECT_API_URL is correct")
            logger.info("  2. Check firewall and network settings")
            logger.info("  3. Ensure Prefect server is running")
    
    async def deploy_hello_flow(self) -> str:
        """Deploy the hello flow"""
        return await self.deploy_flow(
            flow=hello_flow,
            name="hello-production",
            schedule={"interval": self.settings.schedule_interval},
            tags=["production", "automated", "hello"],
            description="Production hello workflow with monitoring"
        )
    
    async def deploy_health_check_flow(self) -> str:
        """Deploy the health check flow"""
        return await self.deploy_flow(
            flow=health_check_flow,
            name="health-check-production",
            schedule={"interval": 300},  # Check every 5 minutes
            tags=["production", "health-check", "monitoring"],
            description="Production health check workflow"
        )
    
    async def deploy_all(self) -> Dict[str, Any]:
        """
        Deploy all flows with parallel execution where possible
        
        Returns:
            Dictionary with deployment results
        """
        results = {
            "success": False,
            "deployments": {},
            "errors": [],
            "metrics": {}
        }
        
        try:
            # Deploy flows in parallel for better performance
            tasks = [
                self.deploy_hello_flow(),
                self.deploy_health_check_flow(),
            ]
            
            # Use asyncio.gather with return_exceptions to handle partial failures
            deployment_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            flow_names = ["hello_flow", "health_check_flow"]
            for name, result in zip(flow_names, deployment_results):
                if isinstance(result, Exception):
                    results["errors"].append({
                        "flow": name,
                        "error": str(result)
                    })
                    logger.error(f"Failed to deploy {name}: {result}")
                else:
                    results["deployments"][name] = result
                    logger.info(f"Successfully deployed {name}: {result}")
            
            # Determine overall success
            results["success"] = len(results["errors"]) == 0
            
            # Add metrics
            results["metrics"] = {
                "total_flows": len(flow_names),
                "successful": len(results["deployments"]),
                "failed": len(results["errors"]),
                "circuit_breaker_state": self.circuit_breaker.state.value
            }
            
            if results["success"]:
                logger.info("✅ All flows deployed successfully")
            else:
                logger.warning(f"⚠️ Partial deployment: {len(results['errors'])} flows failed")
            
            return results
            
        except Exception as e:
            logger.error(f"Critical error during deployment: {e}")
            results["errors"].append({
                "flow": "deployment_manager",
                "error": str(e)
            })
            
            # In container environment, return error info instead of raising
            if self.settings.is_container_env:
                logger.warning("Container environment: returning error info instead of raising")
                return results
            
            raise


async def deploy_flows_async() -> Dict[str, Any]:
    """Async entry point for flow deployment"""
    manager = DeploymentManager()
    return await manager.deploy_all()


def deploy_flows() -> Dict[str, Any]:
    """Synchronous entry point for flow deployment (backward compatibility)"""
    try:
        # Run async deployment in new event loop
        return asyncio.run(deploy_flows_async())
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        
        # Return error info for CI/CD compatibility
        return {
            "success": False,
            "error": str(e),
            "deployments": {},
            "errors": [{"flow": "all", "error": str(e)}]
        }