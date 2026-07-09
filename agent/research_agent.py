"""
Research Agent module for the AI Research Agent.

Main orchestrator for the research pipeline. Coordinates all components
to research SaaS applications one at a time with resume support.

Responsibilities:
- Load apps.json
- Validate app entries
- Iterate through apps
- Process one app at a time
- Resume from previous runs
- Save progress after every completed app
- Skip already completed apps
"""

from typing import Dict, List, Optional, Any, Protocol, runtime_checkable
from pathlib import Path
from datetime import datetime
import json

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.console import Console

from .config import settings
from .logger import get_logger
from .models import AppResearch
from .utils import read_json
from .storage import ResearchStorage


logger = get_logger(__name__)
console = Console()


@runtime_checkable
class ResearchService(Protocol):
    """
    Protocol for research service implementations.
    
    Defines the interface that any research provider must implement.
    This enables dependency injection and allows different LLM providers
    to be plugged in without modifying the ResearchAgent.
    """
    
    def research(self, app: Dict[str, Any]) -> AppResearch:
        """
        Research a single application.
        
        Args:
            app: App dictionary with name and website
            
        Returns:
            AppResearch object with researched data
            
        Raises:
            Exception: If research fails
        """
        ...


class ResearchAgent:
    """
    Main research agent orchestrating the research pipeline.
    
    Coordinates app loading, research processing, and result storage.
    Designed for processing 100+ SaaS applications with resume support
    and graceful error handling.
    
    Uses dependency injection to accept any ResearchService implementation,
    making it easy to swap LLM providers without changing the agent code.
    """
    
    def __init__(
        self,
        research_service: Optional[ResearchService] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize research agent with dependency injection.
        
        Args:
            research_service: Research service instance (required for processing)
            output_dir: Output directory (defaults to settings.OUTPUT_DIR)
        """
        self.research_service = research_service
        self.storage = ResearchStorage(output_dir or settings.OUTPUT_DIR)
        self.apps: List[Dict[str, Any]] = []
        self.existing_results: Dict[str, AppResearch] = {}
        
        logger.info("Research Agent initialized")
    
    # ============================================================================
    # App Loading
    # ============================================================================
    
    def load_apps(self, apps_file: Path) -> List[Dict[str, Any]]:
        """
        Load applications from JSON file.
        
        Args:
            apps_file: Path to apps.json
            
        Returns:
            List of app dictionaries
            
        Raises:
            FileNotFoundError: If apps file doesn't exist
            ValueError: If apps file is invalid
        """
        logger.info(f"Loading apps from {apps_file}")
        
        data = read_json(apps_file)
        
        # Handle both formats: {"apps": [...]} or [...]
        if isinstance(data, dict):
            apps = data.get("apps", [])
        else:
            apps = data
        
        # Validate app entries
        validated_apps = []
        for i, app in enumerate(apps):
            if self._validate_app_entry(app, i):
                validated_apps.append(app)
        
        self.apps = validated_apps
        logger.success(f"Loaded {len(validated_apps)} apps")
        return validated_apps
    
    def _validate_app_entry(self, app: Dict[str, Any], index: int) -> bool:
        """
        Validate a single app entry.
        
        Args:
            app: App dictionary to validate
            index: Index in the apps list (for error reporting)
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(app, dict):
            logger.warning(f"App at index {index} is not a dictionary, skipping")
            return False
        
        if "name" not in app:
            logger.warning(f"App at index {index} missing 'name' field, skipping")
            return False
        
        if "website" not in app:
            logger.warning(f"App '{app.get('name', 'unknown')}' missing 'website' field, skipping")
            return False
        
        return True
    
    # ============================================================================
    # Results Loading
    # ============================================================================
    
    def load_existing_results(self) -> Dict[str, AppResearch]:
        """
        Load existing research results from storage.
        
        This enables resume support by loading previously completed
        research so the agent can skip those apps.
        
        Returns:
            Dictionary mapping app names to AppResearch objects
        """
        logger.info("Loading existing results")
        
        results = self.storage.load_all_results()
        self.existing_results = {app.name: app for app in results}
        
        logger.success(f"Loaded {len(self.existing_results)} existing results")
        return self.existing_results
    
    # ============================================================================
    # Single App Processing
    # ============================================================================
    
    def process_single_app(
        self,
        app: Dict[str, Any],
        force: bool = False,
    ) -> Optional[AppResearch]:
        """
        Process a single application using the injected research service.
        
        Args:
            app: App dictionary with name and website
            force: Force reprocessing even if already done
            
        Returns:
            AppResearch object if successful, None otherwise
        """
        app_name = app.get("name", "Unknown")
        
        # Check if already processed
        if not force and app_name in self.existing_results:
            logger.info(f"{app_name} already processed, skipping")
            return self.existing_results[app_name]
        
        # Check if already processed in storage
        if not force and self.storage.is_processed(app_name):
            logger.info(f"{app_name} already processed, skipping")
            return self.storage.load_result(app_name)
        
        # Ensure research service is available
        if self.research_service is None:
            logger.error("No research service configured")
            return None
        
        try:
            # Delegate to the research service
            result = self.research_service.research(app)
            
            # Save the result
            self.save_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process {app_name}: {e}")
            self.storage.mark_processed(app_name, success=False, error=str(e))
            return None
    
    # ============================================================================
    # Result Saving
    # ============================================================================
    
    def save_result(self, result: AppResearch) -> Path:
        """
        Save a research result to storage.
        
        Args:
            result: AppResearch object to save
            
        Returns:
            Path to the saved file
        """
        logger.info(f"Saving result for {result.name}")
        
        file_path = self.storage.save_result(result)
        
        # Update in-memory cache
        self.existing_results[result.name] = result
        
        logger.success(f"Saved result for {result.name}")
        return file_path
    
    def save_progress(self) -> None:
        """
        Save current progress to storage.
        
        This is called after each app is processed to enable
        resume support in case of interruption.
        """
        # Progress is automatically saved by storage after each app
        # This method exists for explicit progress saving if needed
        progress = self.storage.get_progress()
        logger.debug(f"Progress saved: {progress}")
    
    # ============================================================================
    # Main Run Method
    # ============================================================================
    
    def run(
        self,
        apps_file: Optional[Path] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the research pipeline.
        
        Loads apps, processes each one, and saves results with
        progress tracking and resume support.
        
        Args:
            apps_file: Optional path to apps.json (uses default if None)
            force: Force reprocessing of all apps
            
        Returns:
            Dictionary with processing summary
        """
        # Load apps if file provided
        if apps_file:
            self.load_apps(apps_file)
        
        if not self.apps:
            logger.warning("No apps to process")
            return {"processed": 0, "failed": 0, "skipped": 0}
        
        # Load existing results for resume support
        if not force:
            self.load_existing_results()
        
        # Initialize summary
        summary = {
            "total": len(self.apps),
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "results": [],
            "errors": [],
        }
        
        # Create Rich progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Loading apps...",
                total=len(self.apps),
            )
            
            # Update after loading
            progress.update(task, description=f"Loaded {len(self.apps)} apps")
            
            # Process each app
            for app in self.apps:
                app_name = app.get("name", "Unknown")
                
                # Skip if already processed
                if not force and app_name in self.existing_results:
                    summary["skipped"] += 1
                    progress.advance(task)
                    continue
                
                progress.update(task, description=f"Processing {app_name}...")
                
                result = self.process_single_app(app, force=force)
                
                if result:
                    summary["processed"] += 1
                    summary["results"].append(result)
                else:
                    summary["failed"] += 1
                    summary["errors"].append({
                        "app": app_name,
                        "error": f"Failed to process {app_name}",
                    })
                
                # Save progress after each app
                self.save_progress()
                
                progress.advance(task)
        
        logger.success(
            f"Completed: {summary['processed']} processed, "
            f"{summary['failed']} failed, {summary['skipped']} skipped"
        )
        
        return summary
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def get_pending_apps(self) -> List[Dict[str, Any]]:
        """
        Get list of apps not yet processed.
        
        Returns:
            List of pending app dictionaries
        """
        if not self.apps:
            return []
        
        pending = [
            app for app in self.apps
            if app.get("name", "") not in self.existing_results
            and not self.storage.is_processed(app.get("name", ""))
        ]
        
        logger.info(f"{len(pending)} apps pending")
        return pending
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get research statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.storage.get_statistics()
    
    def close(self) -> None:
        """Close all resources."""
        # No resources to close currently
        logger.debug("Research agent resources closed")
    
    def __enter__(self) -> "ResearchAgent":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()