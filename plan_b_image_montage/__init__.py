"""方案B模块"""
try:
    from .main import PlanBWorkflow
    __all__ = ["PlanBWorkflow"]
except ImportError:
    # main.py未创建时的占位
    __all__ = []
