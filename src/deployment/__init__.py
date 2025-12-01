"""
Brutally Honest AI - Deployment Module
OTA updates and remote deployment management
"""

from .ota_manager import (
    OTADeploymentManager,
    DeploymentConfig,
    DeploymentResult,
    DeploymentStatus,
    DeploymentType,
    RemoteSystemInfo,
    get_ota_manager,
    configure_ota_manager
)

__all__ = [
    'OTADeploymentManager',
    'DeploymentConfig',
    'DeploymentResult',
    'DeploymentStatus',
    'DeploymentType',
    'RemoteSystemInfo',
    'get_ota_manager',
    'configure_ota_manager'
]

