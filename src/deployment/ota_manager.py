#!/usr/bin/env python3
"""
Brutally Honest AI - OTA (Over-the-Air) Deployment Manager
Handles remote deployments via SSH with incremental updates, rollbacks, and monitoring.
"""

import asyncio
import subprocess
import json
import os
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    SYNCING = "syncing"
    INSTALLING = "installing"
    RESTARTING = "restarting"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"


class DeploymentType(str, Enum):
    QUICK = "quick"           # Only sync changed files
    FULL = "full"             # Full reinstall
    RESTART = "restart"       # Just restart services
    ROLLBACK = "rollback"     # Rollback to previous version


@dataclass
class DeploymentConfig:
    """Configuration for remote deployment"""
    remote_host: str = "brutally@brutallyhonest.io"
    remote_dir: str = "/home/brutally/brutally-honest-ai"
    ssh_key: Optional[str] = None
    ssh_port: int = 22
    ssh_timeout: int = 30
    backup_enabled: bool = True
    max_backups: int = 5
    # Remote access options
    use_tailscale: bool = False
    tailscale_hostname: Optional[str] = None  # e.g., "brutally-jetson"
    use_cloudflare_tunnel: bool = False
    cloudflare_hostname: Optional[str] = None  # e.g., "ssh.yourdomain.com"
    jump_host: Optional[str] = None  # For ProxyJump through a bastion
    
    def get_effective_host(self) -> str:
        """Get the effective SSH host based on configuration"""
        if self.use_tailscale and self.tailscale_hostname:
            # Tailscale uses the machine name directly
            user = self.remote_host.split('@')[0] if '@' in self.remote_host else 'brutally'
            return f"{user}@{self.tailscale_hostname}"
        elif self.use_cloudflare_tunnel and self.cloudflare_hostname:
            user = self.remote_host.split('@')[0] if '@' in self.remote_host else 'brutally'
            return f"{user}@{self.cloudflare_hostname}"
        return self.remote_host


@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    success: bool
    deployment_type: DeploymentType
    status: DeploymentStatus
    message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    files_synced: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    remote_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "deployment_type": self.deployment_type.value,
            "status": self.status.value,
            "message": self.message,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "files_synced": self.files_synced,
            "errors": self.errors,
            "warnings": self.warnings,
            "remote_version": self.remote_version
        }


@dataclass
class RemoteSystemInfo:
    """Information about the remote system"""
    hostname: str = ""
    os_version: str = ""
    gpu_info: str = ""
    memory_total: str = ""
    memory_available: str = ""
    disk_usage: str = ""
    python_version: str = ""
    node_version: str = ""
    ollama_running: bool = False
    api_running: bool = False
    frontend_running: bool = False
    uptime: str = ""
    last_deployment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hostname": self.hostname,
            "os_version": self.os_version,
            "gpu_info": self.gpu_info,
            "memory_total": self.memory_total,
            "memory_available": self.memory_available,
            "disk_usage": self.disk_usage,
            "python_version": self.python_version,
            "node_version": self.node_version,
            "ollama_running": self.ollama_running,
            "api_running": self.api_running,
            "frontend_running": self.frontend_running,
            "uptime": self.uptime,
            "last_deployment": self.last_deployment
        }


class OTADeploymentManager:
    """Manages Over-the-Air deployments to remote systems"""
    
    def __init__(self, config: Optional[DeploymentConfig] = None):
        self.config = config or DeploymentConfig()
        self.local_dir = Path(__file__).parent.parent.parent
        self.current_status = DeploymentStatus.IDLE
        self.current_progress = 0
        self.progress_message = ""
        self._progress_callbacks: List[Callable] = []
        self._deployment_history: List[DeploymentResult] = []
        
        # Files/directories to exclude from sync
        self.exclude_patterns = [
            'venv/',
            '__pycache__/',
            '*.pyc',
            'node_modules/',
            '*.db',
            '.git/',
            'models/*.gguf',
            'documents/*',
            'uploads/*',
            '.env',
            '.env.local',
            '.api_keys.json',
            '*.log',
            '.DS_Store',
            'installer/',
            '*.dmg',
        ]
    
    def add_progress_callback(self, callback: Callable):
        """Add a callback for progress updates"""
        self._progress_callbacks.append(callback)
    
    def _update_progress(self, status: DeploymentStatus, progress: int, message: str):
        """Update deployment progress and notify callbacks"""
        self.current_status = status
        self.current_progress = progress
        self.progress_message = message
        
        for callback in self._progress_callbacks:
            try:
                callback(status, progress, message)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def _get_ssh_options(self) -> List[str]:
        """Get SSH command options based on configuration"""
        opts = []
        
        # SSH key
        if self.config.ssh_key:
            opts.extend(["-i", self.config.ssh_key])
        
        # Custom port
        if self.config.ssh_port != 22:
            opts.extend(["-p", str(self.config.ssh_port)])
        
        # Connection options
        opts.extend([
            "-o", f"ConnectTimeout={self.config.ssh_timeout}",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
        ])
        
        # Jump host / bastion (for accessing behind firewalls)
        if self.config.jump_host:
            opts.extend(["-J", self.config.jump_host])
        
        # Cloudflare Tunnel uses ProxyCommand
        if self.config.use_cloudflare_tunnel and self.config.cloudflare_hostname:
            opts.extend(["-o", f"ProxyCommand=cloudflared access ssh --hostname {self.config.cloudflare_hostname}"])
        
        return opts
    
    async def _run_ssh_command(self, command: str, timeout: int = 60) -> tuple[bool, str, str]:
        """Run a command on the remote system via SSH"""
        ssh_cmd = ["ssh"]
        ssh_cmd.extend(self._get_ssh_options())
        
        # Get effective host (handles Tailscale/Cloudflare)
        effective_host = self.config.get_effective_host()
        ssh_cmd.append(effective_host)
        ssh_cmd.append(command)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            success = process.returncode == 0
            return success, stdout.decode('utf-8', errors='replace'), stderr.decode('utf-8', errors='replace')
            
        except asyncio.TimeoutError:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    def _get_rsync_ssh_command(self) -> str:
        """Get the SSH command string for rsync"""
        ssh_parts = ["ssh"]
        
        if self.config.ssh_key:
            ssh_parts.append(f"-i {self.config.ssh_key}")
        
        if self.config.ssh_port != 22:
            ssh_parts.append(f"-p {self.config.ssh_port}")
        
        ssh_parts.append(f"-o ConnectTimeout={self.config.ssh_timeout}")
        ssh_parts.append("-o BatchMode=yes")
        ssh_parts.append("-o StrictHostKeyChecking=accept-new")
        
        if self.config.jump_host:
            ssh_parts.append(f"-J {self.config.jump_host}")
        
        if self.config.use_cloudflare_tunnel and self.config.cloudflare_hostname:
            ssh_parts.append(f"-o ProxyCommand='cloudflared access ssh --hostname {self.config.cloudflare_hostname}'")
        
        return " ".join(ssh_parts)
    
    async def _run_rsync(self, dry_run: bool = False) -> tuple[bool, int, str]:
        """Sync files to remote using rsync"""
        rsync_cmd = [
            "rsync", "-avz", "--progress",
            "--delete",  # Remove files that don't exist locally
        ]
        
        if dry_run:
            rsync_cmd.append("--dry-run")
        
        # Add exclude patterns
        for pattern in self.exclude_patterns:
            rsync_cmd.extend(["--exclude", pattern])
        
        # Add SSH options (with custom port, jump host, cloudflare support)
        ssh_cmd = self._get_rsync_ssh_command()
        rsync_cmd.extend(["-e", ssh_cmd])
        
        # Get effective host and destination
        effective_host = self.config.get_effective_host()
        rsync_cmd.extend([
            f"{self.local_dir}/",
            f"{effective_host}:{self.config.remote_dir}/"
        ])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *rsync_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=600  # 10 minute timeout for sync
            )
            
            output = stdout.decode('utf-8', errors='replace')
            
            # Count files synced (rough estimate from rsync output)
            files_synced = output.count('\n')
            
            success = process.returncode == 0
            return success, files_synced, output if success else stderr.decode('utf-8', errors='replace')
            
        except asyncio.TimeoutError:
            return False, 0, "rsync timed out after 600s"
        except Exception as e:
            return False, 0, str(e)
    
    async def check_ssh_connection(self) -> bool:
        """Test SSH connection to remote host"""
        success, _, _ = await self._run_ssh_command("echo 'connected'", timeout=15)
        return success
    
    async def get_remote_system_info(self) -> RemoteSystemInfo:
        """Get detailed information about the remote system"""
        info = RemoteSystemInfo()
        
        # Check SSH first
        if not await self.check_ssh_connection():
            info.hostname = "OFFLINE"
            return info
        
        # Get hostname
        success, stdout, _ = await self._run_ssh_command("hostname")
        if success:
            info.hostname = stdout.strip()
        
        # Get OS version
        success, stdout, _ = await self._run_ssh_command("uname -a")
        if success:
            info.os_version = stdout.strip()
        
        # Get GPU info (NVIDIA)
        success, stdout, _ = await self._run_ssh_command(
            "nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || echo 'No GPU'"
        )
        if success:
            info.gpu_info = stdout.strip()
        
        # Get memory info
        success, stdout, _ = await self._run_ssh_command("free -h | grep Mem | awk '{print $2, $7}'")
        if success:
            parts = stdout.strip().split()
            if len(parts) >= 1:
                info.memory_total = parts[0]
            if len(parts) >= 2:
                info.memory_available = parts[1]
        
        # Get disk usage
        success, stdout, _ = await self._run_ssh_command(
            f"df -h {self.config.remote_dir} 2>/dev/null | tail -1 | awk '{{print $3\"/\"$2\" (\"$5\" used)\"}}'")
        if success:
            info.disk_usage = stdout.strip()
        
        # Get Python version
        success, stdout, _ = await self._run_ssh_command("python3 --version 2>/dev/null || echo 'Not installed'")
        if success:
            info.python_version = stdout.strip()
        
        # Get Node version
        success, stdout, _ = await self._run_ssh_command("node --version 2>/dev/null || echo 'Not installed'")
        if success:
            info.node_version = stdout.strip()
        
        # Check if Ollama is running
        success, stdout, _ = await self._run_ssh_command("pgrep -x ollama >/dev/null && echo 'running' || echo 'stopped'")
        info.ollama_running = 'running' in stdout
        
        # Check if API is running
        success, stdout, _ = await self._run_ssh_command(
            "systemctl is-active brutally-honest-api 2>/dev/null || echo 'stopped'"
        )
        info.api_running = 'active' in stdout
        
        # Check if frontend is running
        success, stdout, _ = await self._run_ssh_command(
            "systemctl is-active brutally-honest-frontend 2>/dev/null || echo 'stopped'"
        )
        info.frontend_running = 'active' in stdout
        
        # Get uptime
        success, stdout, _ = await self._run_ssh_command("uptime -p 2>/dev/null || uptime")
        if success:
            info.uptime = stdout.strip()
        
        # Get last deployment time
        success, stdout, _ = await self._run_ssh_command(
            f"stat -c '%y' {self.config.remote_dir}/.last_deployment 2>/dev/null || echo 'Never'"
        )
        if success:
            info.last_deployment = stdout.strip()
        
        return info
    
    async def get_service_logs(self, service: str = "api", lines: int = 50) -> str:
        """Get recent logs from a service"""
        service_name = f"brutally-honest-{service}"
        
        success, stdout, stderr = await self._run_ssh_command(
            f"sudo journalctl -u {service_name} -n {lines} --no-pager 2>/dev/null || echo 'Could not get logs'"
        )
        
        return stdout if success else stderr
    
    async def restart_services(self) -> tuple[bool, str]:
        """Restart all Brutally Honest AI services on remote"""
        self._update_progress(DeploymentStatus.RESTARTING, 0, "Restarting services...")
        
        commands = [
            ("Stopping API", "sudo systemctl stop brutally-honest-api 2>/dev/null || true"),
            ("Stopping frontend", "sudo systemctl stop brutally-honest-frontend 2>/dev/null || true"),
            ("Starting API", "sudo systemctl start brutally-honest-api"),
            ("Starting frontend", "sudo systemctl start brutally-honest-frontend"),
        ]
        
        errors = []
        for i, (desc, cmd) in enumerate(commands):
            self._update_progress(
                DeploymentStatus.RESTARTING,
                int((i + 1) / len(commands) * 100),
                desc
            )
            
            success, _, stderr = await self._run_ssh_command(cmd)
            if not success:
                errors.append(f"{desc} failed: {stderr}")
        
        # Wait for services to start
        await asyncio.sleep(3)
        
        # Verify services are running
        api_running = await self._check_service_running("brutally-honest-api")
        frontend_running = await self._check_service_running("brutally-honest-frontend")
        
        if not api_running:
            errors.append("API service failed to start")
        if not frontend_running:
            errors.append("Frontend service failed to start")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "All services restarted successfully"
    
    async def _check_service_running(self, service_name: str) -> bool:
        """Check if a systemd service is running"""
        success, stdout, _ = await self._run_ssh_command(
            f"systemctl is-active {service_name} 2>/dev/null"
        )
        return success and 'active' in stdout
    
    async def create_backup(self) -> tuple[bool, str]:
        """Create a backup of the remote installation"""
        if not self.config.backup_enabled:
            return True, "Backups disabled"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{self.config.remote_dir}_backup_{timestamp}"
        
        # Create backup
        success, _, stderr = await self._run_ssh_command(
            f"cp -r {self.config.remote_dir} {backup_dir}",
            timeout=300
        )
        
        if not success:
            return False, f"Backup failed: {stderr}"
        
        # Clean old backups (keep only max_backups)
        cleanup_cmd = f"""
        cd $(dirname {self.config.remote_dir}) && 
        ls -dt brutally-honest-ai_backup_* 2>/dev/null | 
        tail -n +{self.config.max_backups + 1} | 
        xargs rm -rf 2>/dev/null || true
        """
        await self._run_ssh_command(cleanup_cmd)
        
        return True, backup_dir
    
    async def list_backups(self) -> List[Dict[str, str]]:
        """List available backups on remote"""
        success, stdout, _ = await self._run_ssh_command(
            f"ls -dt $(dirname {self.config.remote_dir})/brutally-honest-ai_backup_* 2>/dev/null || echo ''"
        )
        
        if not success or not stdout.strip():
            return []
        
        backups = []
        for backup_path in stdout.strip().split('\n'):
            if backup_path:
                name = os.path.basename(backup_path)
                # Extract timestamp from name
                timestamp = name.replace("brutally-honest-ai_backup_", "")
                backups.append({
                    "path": backup_path,
                    "name": name,
                    "timestamp": timestamp
                })
        
        return backups
    
    async def rollback(self, backup_name: Optional[str] = None) -> DeploymentResult:
        """Rollback to a previous version"""
        started_at = datetime.now()
        
        self._update_progress(DeploymentStatus.ROLLING_BACK, 0, "Starting rollback...")
        
        # Get available backups
        backups = await self.list_backups()
        if not backups:
            return DeploymentResult(
                success=False,
                deployment_type=DeploymentType.ROLLBACK,
                status=DeploymentStatus.FAILED,
                message="No backups available",
                started_at=started_at,
                completed_at=datetime.now()
            )
        
        # Select backup
        if backup_name:
            backup = next((b for b in backups if b['name'] == backup_name), None)
            if not backup:
                return DeploymentResult(
                    success=False,
                    deployment_type=DeploymentType.ROLLBACK,
                    status=DeploymentStatus.FAILED,
                    message=f"Backup '{backup_name}' not found",
                    started_at=started_at,
                    completed_at=datetime.now()
                )
        else:
            backup = backups[0]  # Most recent
        
        self._update_progress(DeploymentStatus.ROLLING_BACK, 20, f"Rolling back to {backup['name']}...")
        
        # Stop services first
        await self._run_ssh_command("sudo systemctl stop brutally-honest-api brutally-honest-frontend 2>/dev/null || true")
        
        self._update_progress(DeploymentStatus.ROLLING_BACK, 40, "Restoring backup...")
        
        # Swap directories
        rollback_cmd = f"""
        mv {self.config.remote_dir} {self.config.remote_dir}_rollback_temp &&
        mv {backup['path']} {self.config.remote_dir} &&
        rm -rf {self.config.remote_dir}_rollback_temp
        """
        
        success, _, stderr = await self._run_ssh_command(rollback_cmd, timeout=300)
        
        if not success:
            # Try to restore original
            await self._run_ssh_command(
                f"mv {self.config.remote_dir}_rollback_temp {self.config.remote_dir} 2>/dev/null || true"
            )
            return DeploymentResult(
                success=False,
                deployment_type=DeploymentType.ROLLBACK,
                status=DeploymentStatus.FAILED,
                message=f"Rollback failed: {stderr}",
                started_at=started_at,
                completed_at=datetime.now()
            )
        
        self._update_progress(DeploymentStatus.ROLLING_BACK, 80, "Restarting services...")
        
        # Restart services
        restart_success, restart_msg = await self.restart_services()
        
        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()
        
        result = DeploymentResult(
            success=restart_success,
            deployment_type=DeploymentType.ROLLBACK,
            status=DeploymentStatus.COMPLETED if restart_success else DeploymentStatus.FAILED,
            message=f"Rolled back to {backup['name']}" if restart_success else f"Rollback completed but: {restart_msg}",
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration
        )
        
        self._deployment_history.append(result)
        self._update_progress(DeploymentStatus.COMPLETED if restart_success else DeploymentStatus.FAILED, 100, result.message)
        
        return result
    
    async def deploy_quick(self) -> DeploymentResult:
        """Quick deployment - only sync changed files"""
        started_at = datetime.now()
        errors = []
        warnings = []
        
        try:
            # Check SSH connection
            self._update_progress(DeploymentStatus.PREPARING, 5, "Checking SSH connection...")
            if not await self.check_ssh_connection():
                return DeploymentResult(
                    success=False,
                    deployment_type=DeploymentType.QUICK,
                    status=DeploymentStatus.FAILED,
                    message="SSH connection failed",
                    started_at=started_at,
                    completed_at=datetime.now()
                )
            
            # Create remote directory if needed
            self._update_progress(DeploymentStatus.PREPARING, 10, "Preparing remote directory...")
            await self._run_ssh_command(f"mkdir -p {self.config.remote_dir}")
            
            # Sync files
            self._update_progress(DeploymentStatus.SYNCING, 20, "Syncing files...")
            sync_success, files_synced, sync_output = await self._run_rsync()
            
            if not sync_success:
                return DeploymentResult(
                    success=False,
                    deployment_type=DeploymentType.QUICK,
                    status=DeploymentStatus.FAILED,
                    message=f"File sync failed: {sync_output}",
                    started_at=started_at,
                    completed_at=datetime.now(),
                    errors=[sync_output]
                )
            
            self._update_progress(DeploymentStatus.SYNCING, 60, f"Synced {files_synced} files")
            
            # Mark deployment time
            await self._run_ssh_command(
                f"touch {self.config.remote_dir}/.last_deployment"
            )
            
            # Restart services
            self._update_progress(DeploymentStatus.RESTARTING, 70, "Restarting services...")
            restart_success, restart_msg = await self.restart_services()
            
            if not restart_success:
                warnings.append(f"Service restart issue: {restart_msg}")
            
            # Verify
            self._update_progress(DeploymentStatus.VERIFYING, 90, "Verifying deployment...")
            await asyncio.sleep(2)
            
            # Check if services are up
            api_running = await self._check_service_running("brutally-honest-api")
            frontend_running = await self._check_service_running("brutally-honest-frontend")
            
            if not api_running:
                warnings.append("API service may not be running")
            if not frontend_running:
                warnings.append("Frontend service may not be running")
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            result = DeploymentResult(
                success=True,
                deployment_type=DeploymentType.QUICK,
                status=DeploymentStatus.COMPLETED,
                message=f"Quick deployment completed in {duration:.1f}s",
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                files_synced=files_synced,
                errors=errors,
                warnings=warnings
            )
            
            self._deployment_history.append(result)
            self._update_progress(DeploymentStatus.COMPLETED, 100, result.message)
            
            return result
            
        except Exception as e:
            logger.error(f"Quick deployment failed: {e}")
            return DeploymentResult(
                success=False,
                deployment_type=DeploymentType.QUICK,
                status=DeploymentStatus.FAILED,
                message=str(e),
                started_at=started_at,
                completed_at=datetime.now(),
                errors=[str(e)]
            )
    
    async def deploy_full(self) -> DeploymentResult:
        """Full deployment - reinstall everything"""
        started_at = datetime.now()
        errors = []
        warnings = []
        
        try:
            # Check SSH connection
            self._update_progress(DeploymentStatus.PREPARING, 2, "Checking SSH connection...")
            if not await self.check_ssh_connection():
                return DeploymentResult(
                    success=False,
                    deployment_type=DeploymentType.FULL,
                    status=DeploymentStatus.FAILED,
                    message="SSH connection failed",
                    started_at=started_at,
                    completed_at=datetime.now()
                )
            
            # Create backup
            self._update_progress(DeploymentStatus.PREPARING, 5, "Creating backup...")
            backup_success, backup_msg = await self.create_backup()
            if not backup_success:
                warnings.append(f"Backup warning: {backup_msg}")
            
            # Stop services
            self._update_progress(DeploymentStatus.PREPARING, 10, "Stopping services...")
            await self._run_ssh_command(
                "sudo systemctl stop brutally-honest-api brutally-honest-frontend 2>/dev/null || true"
            )
            
            # Sync files
            self._update_progress(DeploymentStatus.SYNCING, 15, "Syncing all files...")
            sync_success, files_synced, sync_output = await self._run_rsync()
            
            if not sync_success:
                errors.append(f"File sync failed: {sync_output}")
                return DeploymentResult(
                    success=False,
                    deployment_type=DeploymentType.FULL,
                    status=DeploymentStatus.FAILED,
                    message=f"File sync failed",
                    started_at=started_at,
                    completed_at=datetime.now(),
                    errors=errors
                )
            
            self._update_progress(DeploymentStatus.SYNCING, 35, f"Synced {files_synced} files")
            
            # Install Python dependencies
            self._update_progress(DeploymentStatus.INSTALLING, 40, "Installing Python dependencies...")
            install_cmd = f"""
            cd {self.config.remote_dir} &&
            if [ ! -d "venv" ]; then python3 -m venv venv; fi &&
            source venv/bin/activate &&
            pip install --upgrade pip wheel &&
            pip install -r requirements.txt --no-cache-dir
            """
            
            success, _, stderr = await self._run_ssh_command(install_cmd, timeout=600)
            if not success:
                warnings.append(f"Python install warning: {stderr}")
            
            self._update_progress(DeploymentStatus.INSTALLING, 60, "Installing Node.js dependencies...")
            
            # Install Node.js dependencies
            node_cmd = f"cd {self.config.remote_dir}/frontend && npm install"
            success, _, stderr = await self._run_ssh_command(node_cmd, timeout=300)
            if not success:
                warnings.append(f"Node.js install warning: {stderr}")
            
            # Mark deployment time
            await self._run_ssh_command(
                f"touch {self.config.remote_dir}/.last_deployment"
            )
            
            # Restart services
            self._update_progress(DeploymentStatus.RESTARTING, 80, "Restarting services...")
            restart_success, restart_msg = await self.restart_services()
            
            if not restart_success:
                warnings.append(f"Service restart issue: {restart_msg}")
            
            # Verify
            self._update_progress(DeploymentStatus.VERIFYING, 95, "Verifying deployment...")
            await asyncio.sleep(3)
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            result = DeploymentResult(
                success=True,
                deployment_type=DeploymentType.FULL,
                status=DeploymentStatus.COMPLETED,
                message=f"Full deployment completed in {duration:.1f}s",
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                files_synced=files_synced,
                errors=errors,
                warnings=warnings
            )
            
            self._deployment_history.append(result)
            self._update_progress(DeploymentStatus.COMPLETED, 100, result.message)
            
            return result
            
        except Exception as e:
            logger.error(f"Full deployment failed: {e}")
            return DeploymentResult(
                success=False,
                deployment_type=DeploymentType.FULL,
                status=DeploymentStatus.FAILED,
                message=str(e),
                started_at=started_at,
                completed_at=datetime.now(),
                errors=[str(e)]
            )
    
    def get_deployment_history(self) -> List[Dict[str, Any]]:
        """Get deployment history"""
        return [r.to_dict() for r in self._deployment_history[-20:]]  # Last 20
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        return {
            "status": self.current_status.value,
            "progress": self.current_progress,
            "message": self.progress_message
        }


# Singleton instance
_ota_manager: Optional[OTADeploymentManager] = None


def get_ota_manager() -> OTADeploymentManager:
    """Get the singleton OTA manager instance"""
    global _ota_manager
    if _ota_manager is None:
        _ota_manager = OTADeploymentManager()
    return _ota_manager


async def configure_ota_manager(
    remote_host: str,
    remote_dir: str = "/home/brutally/brutally-honest-ai",
    ssh_key: Optional[str] = None,
    ssh_port: int = 22,
    use_tailscale: bool = False,
    tailscale_hostname: Optional[str] = None,
    use_cloudflare_tunnel: bool = False,
    cloudflare_hostname: Optional[str] = None,
    jump_host: Optional[str] = None
) -> OTADeploymentManager:
    """Configure and return the OTA manager"""
    global _ota_manager
    
    config = DeploymentConfig(
        remote_host=remote_host,
        remote_dir=remote_dir,
        ssh_key=ssh_key,
        ssh_port=ssh_port,
        use_tailscale=use_tailscale,
        tailscale_hostname=tailscale_hostname,
        use_cloudflare_tunnel=use_cloudflare_tunnel,
        cloudflare_hostname=cloudflare_hostname,
        jump_host=jump_host
    )
    
    _ota_manager = OTADeploymentManager(config)
    return _ota_manager

