"""
指标收集模块

提供应用程序指标收集和监控功能。
"""
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """指标数据点"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
        }


class Counter:
    """计数器指标"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0.0
        self._labels_values: Dict[str, float] = defaultdict(float)
    
    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数"""
        if labels:
            label_key = self._labels_to_key(labels)
            self._labels_values[label_key] += amount
        else:
            self._value += amount
    
    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """获取当前值"""
        if labels:
            label_key = self._labels_to_key(labels)
            return self._labels_values.get(label_key, 0.0)
        return self._value
    
    def get_all_values(self) -> List[MetricPoint]:
        """获取所有标签的值"""
        points = []
        now = datetime.now(timezone.utc)
        
        # 无标签的值
        if self._value > 0:
            points.append(MetricPoint(self.name, self._value, now))
        
        # 有标签的值
        for label_key, value in self._labels_values.items():
            if value > 0:
                labels = self._key_to_labels(label_key)
                points.append(MetricPoint(self.name, value, now, labels))
        
        return points
    
    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """将标签转换为键"""
        return "|".join(f"{k}={v}" for k, v in sorted(labels.items()))
    
    def _key_to_labels(self, key: str) -> Dict[str, str]:
        """将键转换为标签"""
        if not key:
            return {}
        return dict(item.split("=", 1) for item in key.split("|"))


class Gauge:
    """仪表盘指标"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0.0
        self._labels_values: Dict[str, float] = defaultdict(float)
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置值"""
        if labels:
            label_key = self._labels_to_key(labels)
            self._labels_values[label_key] = value
        else:
            self._value = value
    
    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """增加值"""
        if labels:
            label_key = self._labels_to_key(labels)
            self._labels_values[label_key] += amount
        else:
            self._value += amount
    
    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """减少值"""
        self.inc(-amount, labels)
    
    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """获取当前值"""
        if labels:
            label_key = self._labels_to_key(labels)
            return self._labels_values.get(label_key, 0.0)
        return self._value
    
    def get_all_values(self) -> List[MetricPoint]:
        """获取所有标签的值"""
        points = []
        now = datetime.now(timezone.utc)
        
        # 无标签的值
        points.append(MetricPoint(self.name, self._value, now))
        
        # 有标签的值
        for label_key, value in self._labels_values.items():
            labels = self._key_to_labels(label_key)
            points.append(MetricPoint(self.name, value, now, labels))
        
        return points
    
    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """将标签转换为键"""
        return "|".join(f"{k}={v}" for k, v in sorted(labels.items()))
    
    def _key_to_labels(self, key: str) -> Dict[str, str]:
        """将键转换为标签"""
        if not key:
            return {}
        return dict(item.split("=", 1) for item in key.split("|"))


class Histogram:
    """直方图指标"""
    
    def __init__(self, name: str, description: str = "", buckets: Optional[List[float]] = None):
        self.name = name
        self.description = description
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self._observations: List[float] = []
        self._bucket_counts: Dict[float, int] = {bucket: 0 for bucket in self.buckets}
        self._sum = 0.0
        self._count = 0
    
    def observe(self, value: float) -> None:
        """记录观察值"""
        self._observations.append(value)
        self._sum += value
        self._count += 1
        
        # 更新桶计数
        for bucket in self.buckets:
            if value <= bucket:
                self._bucket_counts[bucket] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        if not self._observations:
            return {
                "count": 0,
                "sum": 0.0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "buckets": self._bucket_counts,
            }
        
        sorted_obs = sorted(self._observations)
        return {
            "count": self._count,
            "sum": self._sum,
            "avg": self._sum / self._count,
            "min": min(self._observations),
            "max": max(self._observations),
            "p50": self._percentile(sorted_obs, 0.5),
            "p90": self._percentile(sorted_obs, 0.9),
            "p95": self._percentile(sorted_obs, 0.95),
            "p99": self._percentile(sorted_obs, 0.99),
            "buckets": self._bucket_counts,
        }
    
    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not sorted_values:
            return 0.0
        
        index = int(len(sorted_values) * percentile)
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
        
        return sorted_values[index]


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self._start_time = time.time()
    
    def counter(self, name: str, description: str = "") -> Counter:
        """获取或创建计数器"""
        if name not in self.counters:
            self.counters[name] = Counter(name, description)
        return self.counters[name]
    
    def gauge(self, name: str, description: str = "") -> Gauge:
        """获取或创建仪表盘"""
        if name not in self.gauges:
            self.gauges[name] = Gauge(name, description)
        return self.gauges[name]
    
    def histogram(self, name: str, description: str = "", buckets: Optional[List[float]] = None) -> Histogram:
        """获取或创建直方图"""
        if name not in self.histograms:
            self.histograms[name] = Histogram(name, description, buckets)
        return self.histograms[name]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": time.time() - self._start_time,
            "counters": {},
            "gauges": {},
            "histograms": {},
        }
        
        # 收集计数器指标
        for name, counter in self.counters.items():
            points = counter.get_all_values()
            metrics["counters"][name] = [point.to_dict() for point in points]
        
        # 收集仪表盘指标
        for name, gauge in self.gauges.items():
            points = gauge.get_all_values()
            metrics["gauges"][name] = [point.to_dict() for point in points]
        
        # 收集直方图指标
        for name, histogram in self.histograms.items():
            metrics["histograms"][name] = histogram.get_summary()
        
        return metrics
    
    def record_flow_execution(self, flow_name: str, duration: float, status: str) -> None:
        """记录流程执行指标"""
        # 计数器：流程执行次数
        self.counter("flow_executions_total", "Total number of flow executions").inc(
            labels={"flow_name": flow_name, "status": status}
        )
        
        # 直方图：流程执行时间
        self.histogram("flow_execution_duration_seconds", "Flow execution duration").observe(duration)
        
        # 仪表盘：最后执行时间
        self.gauge("flow_last_execution_timestamp", "Last flow execution timestamp").set(
            time.time(), labels={"flow_name": flow_name}
        )
    
    def record_deployment(self, flow_name: str, status: str) -> None:
        """记录部署指标"""
        self.counter("deployments_total", "Total number of deployments").inc(
            labels={"flow_name": flow_name, "status": status}
        )
        
        self.gauge("deployment_last_timestamp", "Last deployment timestamp").set(
            time.time(), labels={"flow_name": flow_name}
        )
    
    def record_api_request(self, endpoint: str, method: str, status_code: int, duration: float) -> None:
        """记录API请求指标"""
        self.counter("api_requests_total", "Total API requests").inc(
            labels={"endpoint": endpoint, "method": method, "status": str(status_code)}
        )
        
        self.histogram("api_request_duration_seconds", "API request duration").observe(duration)


# 全局指标收集器
metrics = MetricsCollector()


def record_execution_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """装饰器：记录函数执行时间"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import functools
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 记录成功执行
                metrics.histogram(f"{metric_name}_duration_seconds").observe(duration)
                metrics.counter(f"{metric_name}_total").inc(
                    labels={**(labels or {}), "status": "success"}
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # 记录失败执行
                metrics.histogram(f"{metric_name}_duration_seconds").observe(duration)
                metrics.counter(f"{metric_name}_total").inc(
                    labels={**(labels or {}), "status": "error"}
                )
                
                raise
        
        return functools.wraps(func)(wrapper)
    return decorator
