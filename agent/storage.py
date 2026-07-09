"""
Storage module for the AI Research Agent.

Handles saving and loading research results with support for
resume functionality and atomic writes.

Responsibilities:
- Save research results to JSON
- Load existing results
- Support resume after interruption
- Atomic writes to prevent corruption
- Track processed applications
"""

import json
import os
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from .logger import get_logger
from .models import AppResearch, ResearchBatch

logger = get_logger(__name__)


class ResearchStorage:
    """
    Storage manager for research results.
    
    Provides atomic writes, resume support, and progress tracking.
    """

    def __init__(self, output_dir: Path):
        """
        Initialize storage.
        
        Args:
            output_dir: Base output directory
        """
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw"
        self.verified_dir = self.output_dir / "verified"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.verified_dir.mkdir(parents=True, exist_ok=True)
        
        # Track processed apps
        self.processed_file = self.raw_dir / "processed.json"
        self.processed_apps = self._load_processed()
        
        logger.info(f"Storage initialized at {self.output_dir}")

    def _load_processed(self) -> Dict[str, Any]:
        """
        Load list of processed applications.
        
        Returns:
            Dictionary of processed app names and metadata
        """
        if not self.processed_file.exists():
            return {}
        
        try:
            with open(self.processed_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load processed apps: {e}")
            return {}

    def _save_processed(self) -> None:
        """Save list of processed applications."""
        try:
            with open(self.processed_file, "w", encoding="utf-8") as f:
                json.dump(self.processed_apps, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save processed apps: {e}")

    def is_processed(self, app_name: str) -> bool:
        """
        Check if application has been processed.
        
        Args:
            app_name: Application name
            
        Returns:
            True if processed, False otherwise
        """
        return app_name in self.processed_apps

    def mark_processed(
        self,
        app_name: str,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """
        Mark application as processed.
        
        Args:
            app_name: Application name
            success: Whether processing succeeded
            error: Error message if failed
        """
        self.processed_apps[app_name] = {
            "processed_at": datetime.utcnow().isoformat(),
            "success": success,
            "error": error,
        }
        self._save_processed()
        logger.debug(f"Marked {app_name} as processed")

    def save_result(
        self,
        app_research: AppResearch,
        batch_id: Optional[str] = None,
    ) -> Path:
        """
        Save research result atomically.
        
        Uses atomic write (write to temp file, then rename) to prevent
        corruption if the process is interrupted.
        
        Args:
            app_research: AppResearch object to save
            batch_id: Optional batch identifier
            
        Returns:
            Path to saved file
        """
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = self._sanitize_filename(app_research.name)
        filename = f"{safe_name}_{timestamp}.json"
        file_path = self.raw_dir / filename
        
        # Atomic write
        try:
            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".json",
                dir=self.raw_dir,
                delete=False,
            ) as temp_file:
                json.dump(
                    app_research.dict(),
                    temp_file,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
                temp_path = temp_file.name
            
            # Rename to final path (atomic operation)
            os.replace(temp_path, file_path)
            
            # Mark as processed
            self.mark_processed(app_research.name, success=True)
            
            logger.success(f"Saved result for {app_research.name} to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save result for {app_research.name}: {e}")
            # Clean up temp file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def save_batch(
        self,
        apps: List[AppResearch],
        batch_id: Optional[str] = None,
    ) -> Path:
        """
        Save batch of research results.
        
        Args:
            apps: List of AppResearch objects
            batch_id: Optional batch identifier
            
        Returns:
            Path to saved batch file
        """
        if not apps:
            logger.warning("No apps to save")
            return Path("")
        
        # Generate batch filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        batch_id = batch_id or f"batch_{timestamp}"
        filename = f"{batch_id}.json"
        file_path = self.raw_dir / filename
        
        # Create batch object
        batch = ResearchBatch(
            batch_id=batch_id,
            apps=apps,
            metadata={
                "total_apps": len(apps),
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        
        # Atomic write
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".json",
                dir=self.raw_dir,
                delete=False,
            ) as temp_file:
                json.dump(
                    batch.dict(),
                    temp_file,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
                temp_path = temp_file.name
            
            os.replace(temp_path, file_path)
            
            # Mark all apps as processed
            for app in apps:
                self.mark_processed(app.name, success=True)
            
            logger.success(f"Saved batch of {len(apps)} apps to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save batch: {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def load_result(self, app_name: str) -> Optional[AppResearch]:
        """
        Load research result for an application.
        
        Args:
            app_name: Application name
            
        Returns:
            AppResearch object if found, None otherwise
        """
        # Find file for this app
        safe_name = self._sanitize_filename(app_name)
        pattern = f"{safe_name}_*.json"
        
        matching_files = list(self.raw_dir.glob(pattern))
        if not matching_files:
            logger.debug(f"No saved result found for {app_name}")
            return None
        
        # Load most recent file
        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppResearch(**data)
        except Exception as e:
            logger.error(f"Failed to load result for {app_name}: {e}")
            return None

    def load_all_results(self) -> List[AppResearch]:
        """
        Load all saved research results.
        
        Returns:
            List of AppResearch objects
        """
        apps = []
        
        for json_file in self.raw_dir.glob("*.json"):
            if json_file.name == "processed.json":
                continue
            
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Handle both single app and batch formats
                    if "apps" in data:
                        # Batch format
                        for app_data in data["apps"]:
                            apps.append(AppResearch(**app_data))
                    else:
                        # Single app format
                        apps.append(AppResearch(**data))
                        
            except Exception as e:
                logger.warning(f"Failed to load {json_file}: {e}")
        
        logger.info(f"Loaded {len(apps)} research results")
        return apps

    def get_progress(self) -> Dict[str, Any]:
        """
        Get research progress statistics.
        
        Returns:
            Dictionary with progress information
        """
        total_processed = len(self.processed_apps)
        successful = sum(1 for p in self.processed_apps.values() if p.get("success", False))
        failed = total_processed - successful
        
        return {
            "total_processed": total_processed,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_processed * 100) if total_processed > 0 else 0,
        }

    def clear_processed(self) -> None:
        """Clear list of processed applications."""
        self.processed_apps = {}
        self._save_processed()
        logger.info("Cleared processed apps list")

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe filesystem storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, "_")
        
        # Limit length
        return filename[:100]

    def export_to_csv(self, output_path: Optional[Path] = None) -> Path:
        """
        Export all results to CSV.
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to exported CSV file
        """
        import csv
        
        apps = self.load_all_results()
        if not apps:
            logger.warning("No results to export")
            return Path("")
        
        output_path = output_path or self.output_dir / "research_results.csv"
        
        # Flatten data for CSV
        rows = []
        for app in apps:
            row = {
                "name": app.name,
                "category": app.category,
                "description": app.description,
                "auth_methods": ", ".join(app.auth_methods) if app.auth_methods else "",
                "self_serve": app.self_serve,
                "api_surface": app.api_surface,
                "mcp_support": app.mcp_support,
                "buildability": app.buildability,
                "main_blocker": app.main_blocker,
                "evidence_url": str(app.evidence_url) if app.evidence_url else "",
                "confidence_score": app.confidence_score,
                "verification_status": app.verification_status,
                "researched_at": app.researched_at.isoformat() if app.researched_at else "",
            }
            rows.append(row)
        
        # Write CSV
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        logger.success(f"Exported {len(rows)} results to {output_path}")
        return output_path

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with statistics
        """
        apps = self.load_all_results()
        
        if not apps:
            return {
                "total_saved": 0,
                "categories": {},
                "average_confidence": 0.0,
            }
        
        # Calculate statistics
        categories = defaultdict(int)
        total_confidence = 0.0
        
        for app in apps:
            categories[app.category] += 1
            total_confidence += app.confidence_score
        
        return {
            "total_saved": len(apps),
            "categories": dict(categories),
            "average_confidence": round(total_confidence / len(apps), 2),
            "progress": self.get_progress(),
        }