"""
Analytics module for the AI Research Agent.

Analyzes researched dataset and discovers meaningful product insights.
Identifies patterns across SaaS applications.

Responsibilities:
- Authentication statistics
- Category statistics
- API statistics
- Buildability insights
- Confidence analysis
- Pattern detection
- Opportunity identification
"""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from collections import Counter, defaultdict

from .logger import get_logger
from .models import AppResearch, Category, AuthMethod, VerificationStatus
from .storage import ResearchStorage
from .config import settings

logger = get_logger(__name__)


class AnalyticsEngine:
    """
    Analytics engine for analyzing research data.
    
    Provides comprehensive analytics on researched applications including
    statistics, trends, insights generation, and opportunity detection.
    """
    
    def __init__(self, apps: Optional[List[AppResearch]] = None) -> None:
        """
        Initialize analytics engine.
        
        Args:
            apps: Optional list of AppResearch objects to analyze
        """
        self.apps = apps or []
        self._cache: Dict[str, Any] = {}
    
    def load_apps(self, apps: List[AppResearch]) -> None:
        """
        Load applications for analysis.
        
        Args:
            apps: List of AppResearch objects
        """
        self.apps = apps
        self._cache.clear()
    
    def load_from_storage(self) -> None:
        """Load applications from storage."""
        storage = ResearchStorage(settings.OUTPUT_DIR)
        self.apps = storage.load_all_results()
        self._cache.clear()
        logger.info(f"Loaded {len(self.apps)} apps from storage")
    
    # ============================================================================
    # Authentication Statistics
    # ============================================================================
    
    def get_auth_statistics(self) -> Dict[str, Any]:
        """
        Generate authentication method statistics.
        
        Returns:
            Dictionary with auth method distribution and analysis
        """
        auth_counter = Counter()
        auth_by_category: Dict[str, Counter] = defaultdict(Counter)
        multi_auth_count = 0
        
        for app in self.apps:
            if app.auth_methods:
                auth_counter.update(app.auth_methods)
                if len(app.auth_methods) > 1:
                    multi_auth_count += 1
            
            for method in app.auth_methods:
                auth_by_category[app.category].update([method])
        
        return {
            "total_apps_with_auth": sum(auth_counter.values()),
            "auth_method_distribution": dict(auth_counter),
            "most_common_methods": [m for m, _ in auth_counter.most_common(5)],
            "auth_by_category": {k: dict(v) for k, v in auth_by_category.items()},
            "multi_auth_percentage": (multi_auth_count / len(self.apps) * 100) if self.apps else 0,
        }
    
    def get_auth_trends_by_category(self) -> Dict[str, List[str]]:
        """
        Analyze authentication trends across categories.
        
        Returns:
            Dictionary mapping categories to their most common auth methods
        """
        auth_by_category: Dict[str, Counter] = defaultdict(Counter)
        
        for app in self.apps:
            for method in app.auth_methods:
                auth_by_category[app.category].update([method])
        
        return {
            cat: [m for m, _ in counter.most_common(3)]
            for cat, counter in auth_by_category.items()
        }
    
    # ============================================================================
    # Category Statistics
    # ============================================================================
    
    def get_category_statistics(self) -> Dict[str, Any]:
        """
        Generate category distribution statistics.
        
        Returns:
            Dictionary with category distribution
        """
        category_counter = Counter(app.category for app in self.apps)
        
        return {
            "total_categories": len(category_counter),
            "category_distribution": dict(category_counter),
            "most_common_category": category_counter.most_common(1)[0][0] if category_counter else None,
            "category_percentages": {
                cat: count / len(self.apps) * 100
                for cat, count in category_counter.items()
            },
        }
    
    # ============================================================================
    # API Statistics
    # ============================================================================
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """
        Generate API surface statistics.
        
        Returns:
            Dictionary with API analysis
        """
        api_keywords = ["rest", "graphql", "sdk", "webhook", "openapi"]
        api_counts = {kw: 0 for kw in api_keywords}
        api_counts["mixed"] = 0
        
        for app in self.apps:
            if app.api_surface:
                found = []
                for kw in api_keywords:
                    if kw in app.api_surface.lower():
                        found.append(kw)
                if len(found) > 1:
                    api_counts["mixed"] += 1
                elif found:
                    api_counts[found[0]] += 1
        
        return {
            "apps_with_api": sum(1 for app in self.apps if app.api_surface),
            "api_coverage_percentage": sum(1 for app in self.apps if app.api_surface) / len(self.apps) * 100 if self.apps else 0,
            "api_type_distribution": api_counts,
        }
    
    # ============================================================================
    # Accessibility Statistics
    # ============================================================================
    
    def get_accessibility_statistics(self) -> Dict[str, Any]:
        """
        Generate accessibility statistics.
        
        Returns:
            Dictionary with self-serve and access analysis
        """
        self_serve_count = sum(1 for app in self.apps if app.self_serve is True)
        enterprise_only_count = sum(1 for app in self.apps if app.self_serve is False)
        unknown_count = sum(1 for app in self.apps if app.self_serve is None)
        
        return {
            "self_serve": self_serve_count,
            "enterprise_only": enterprise_only_count,
            "unknown": unknown_count,
            "self_serve_percentage": self_serve_count / len(self.apps) * 100 if self.apps else 0,
        }
    
    # ============================================================================
    # MCP Statistics
    # ============================================================================
    
    def get_mcp_statistics(self) -> Dict[str, Any]:
        """
        Generate MCP support statistics.
        
        Returns:
            Dictionary with MCP analysis
        """
        mcp_available = sum(1 for app in self.apps if app.mcp_support is True)
        mcp_not_available = sum(1 for app in self.apps if app.mcp_support is False)
        mcp_unknown = sum(1 for app in self.apps if app.mcp_support is None)
        
        return {
            "available": mcp_available,
            "not_available": mcp_not_available,
            "unknown": mcp_unknown,
            "mcp_support_rate": mcp_available / len(self.apps) * 100 if self.apps else 0,
        }
    
    # ============================================================================
    # Buildability Statistics
    # ============================================================================
    
    def get_buildability_statistics(self) -> Dict[str, Any]:
        """
        Generate buildability statistics.
        
        Returns:
            Dictionary with buildability analysis
        """
        buildability_counter = Counter(app.buildability for app in self.apps if app.buildability)
        
        return {
            "easy": buildability_counter.get("high", 0),
            "medium": buildability_counter.get("medium", 0),
            "hard": buildability_counter.get("low", 0),
            "blocked": sum(1 for app in self.apps if app.main_blocker),
            "buildability_distribution": dict(buildability_counter),
        }
    
    # ============================================================================
    # Main Blockers Analysis
    # ============================================================================
    
    def get_blocker_clusters(self) -> Dict[str, Any]:
        """
        Cluster and analyze main blockers.
        
        Returns:
            Dictionary with blocker analysis
        """
        blocker_counter = Counter(app.main_blocker for app in self.apps if app.main_blocker)
        
        # Normalize blocker names
        normalized = {}
        for blocker, count in blocker_counter.items():
            key = blocker.lower().strip()
            if "api" in key and "public" in key:
                normalized["No Public API"] = normalized.get("No Public API", 0) + count
            elif "enterprise" in key:
                normalized["Enterprise Only"] = normalized.get("Enterprise Only", 0) + count
            elif "partner" in key:
                normalized["Partner Approval"] = normalized.get("Partner Approval", 0) + count
            elif "beta" in key:
                normalized["Private Beta"] = normalized.get("Private Beta", 0) + count
            elif "oauth" in key:
                normalized["No OAuth"] = normalized.get("No OAuth", 0) + count
            else:
                normalized[blocker] = count
        
        return {
            "blocker_distribution": normalized,
            "top_blockers": sorted(normalized.items(), key=lambda x: -x[1])[:5],
            "total_blocked": sum(1 for app in self.apps if app.main_blocker),
        }
    
    # ============================================================================
    # Insights Engine
    # ============================================================================
    
    def generate_insights(self) -> List[Dict[str, str]]:
        """
        Generate meaningful insights from the data.
        
        Returns:
            List of insight dictionaries
        """
        insights = []
        
        # Get statistics
        auth_stats = self.get_auth_statistics()
        category_stats = self.get_category_statistics()
        api_stats = self.get_api_statistics()
        access_stats = self.get_accessibility_statistics()
        mcp_stats = self.get_mcp_statistics()
        build_stats = self.get_buildability_statistics()
        
        # Insight 1: CRM platforms and OAuth
        crm_apps = [app for app in self.apps if app.category == "crm"]
        crm_oauth = sum(1 for app in crm_apps if "oauth2" in app.auth_methods)
        if crm_apps and crm_oauth / len(crm_apps) > 0.5:
            insights.append({
                "insight": "Most CRM platforms support OAuth",
                "evidence": f"{crm_oauth}/{len(crm_apps)} CRM apps have OAuth support",
                "category": "authentication",
            })
        
        # Insight 2: Finance APIs are gated
        finance_apps = [app for app in self.apps if app.category == "finance"]
        finance_gated = sum(1 for app in finance_apps if app.self_serve is False)
        if finance_apps and finance_gated / len(finance_apps) > 0.5:
            insights.append({
                "insight": "Finance APIs are significantly more gated",
                "evidence": f"{finance_gated}/{len(finance_apps)} finance apps require sales contact",
                "category": "accessibility",
            })
        
        # Insight 3: Developer tools are self-serve
        dev_apps = [app for app in self.apps if app.category == "developer_tools"]
        dev_self_serve = sum(1 for app in dev_apps if app.self_serve is True)
        if dev_apps and dev_self_serve / len(dev_apps) > 0.7:
            insights.append({
                "insight": "Developer tools are usually self-serve",
                "evidence": f"{dev_self_serve}/{len(dev_apps)} developer tools offer self-signup",
                "category": "accessibility",
            })
        
        # Insight 4: Marketing APIs require verification
        marketing_apps = [app for app in self.apps if app.category == "marketing"]
        marketing_blocked = sum(1 for app in marketing_apps if app.main_blocker)
        if marketing_apps and marketing_blocked / len(marketing_apps) > 0.3:
            insights.append({
                "insight": "Marketing APIs often require business verification",
                "evidence": f"{marketing_blocked}/{len(marketing_apps)} marketing apps have blockers",
                "category": "buildability",
            })
        
        # Insight 5: API key prevalence
        api_key_count = auth_stats["auth_method_distribution"].get("api_key", 0)
        if api_key_count > len(self.apps) * 0.5:
            insights.append({
                "insight": "API Key is the most common authentication method",
                "evidence": f"{api_key_count} apps support API key authentication",
                "category": "authentication",
            })
        
        # Insight 6: REST API dominance
        rest_count = api_stats["api_type_distribution"].get("rest", 0)
        if rest_count > len(self.apps) * 0.4:
            insights.append({
                "insight": "REST APIs dominate the landscape",
                "evidence": f"{rest_count} apps have REST API documentation",
                "category": "api",
            })
        
        # Insight 7: MCP adoption is low
        if mcp_stats["mcp_support_rate"] < 20:
            insights.append({
                "insight": "MCP adoption is still early",
                "evidence": f"Only {mcp_stats['mcp_support_rate']:.0f}% of apps support MCP",
                "category": "mcp",
            })
        
        # Insight 8: High buildability correlation with self-serve
        high_build_self_serve = sum(
            1 for app in self.apps
            if app.buildability == "high" and app.self_serve is True
        )
        high_build_count = build_stats["easy"]
        if high_build_count and high_build_self_serve / high_build_count > 0.7:
            insights.append({
                "insight": "Self-serve access strongly correlates with high buildability",
                "evidence": f"{high_build_self_serve}/{high_build_count} high-buildability apps are self-serve",
                "category": "buildability",
            })
        
        # Insight 9: Database APIs are well-documented
        db_apps = [app for app in self.apps if app.category == "database"]
        db_api = sum(1 for app in db_apps if app.api_surface)
        if db_apps and db_api / len(db_apps) > 0.8:
            insights.append({
                "insight": "Database services have excellent API documentation",
                "evidence": f"{db_api}/{len(db_apps)} database apps have API surface documented",
                "category": "api",
            })
        
        # Insight 10: Security tools are restrictive
        security_apps = [app for app in self.apps if app.category == "security"]
        security_blocked = sum(1 for app in security_apps if app.main_blocker)
        if security_apps and security_blocked / len(security_apps) > 0.5:
            insights.append({
                "insight": "Security tools have the most integration restrictions",
                "evidence": f"{security_blocked}/{len(security_apps)} security apps have blockers",
                "category": "buildability",
            })
        
        logger.info(f"Generated {len(insights)} insights")
        return insights
    
    # ============================================================================
    # Opportunity Detector
    # ============================================================================
    
    def generate_opportunities(self) -> Dict[str, Any]:
        """
        Generate opportunity analysis.
        
        Returns:
            Dictionary with easy_wins, medium_effort, high_effort lists
        """
        opportunities = {
            "easy_wins": [],
            "medium_effort": [],
            "high_effort": [],
        }
        
        for app in self.apps:
            # Easy wins: self-serve, high buildability, no blockers
            if (
                app.self_serve is True
                and app.buildability == "high"
                and not app.main_blocker
            ):
                opportunities["easy_wins"].append({
                    "name": app.name,
                    "category": app.category,
                    "reason": "Self-serve with high buildability and no blockers",
                })
            
            # Medium effort: self-serve but medium buildability
            elif (
                app.self_serve is True
                and app.buildability in ["medium", "high"]
            ):
                opportunities["medium_effort"].append({
                    "name": app.name,
                    "category": app.category,
                    "reason": f"Self-serve but {app.buildability} buildability",
                })
            
            # High effort: enterprise only or has blockers
            elif app.self_serve is False or app.main_blocker:
                opportunities["high_effort"].append({
                    "name": app.name,
                    "category": app.category,
                    "reason": "Requires sales contact or has integration blockers",
                })
        
        logger.info(f"Generated opportunities: {len(opportunities['easy_wins'])} easy, "
                   f"{len(opportunities['medium_effort'])} medium, "
                   f"{len(opportunities['high_effort'])} high")
        
        return opportunities
    
    # ============================================================================
    # Report Generation
    # ============================================================================
    
    def generate_statistics_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive statistics report.
        
        Returns:
            Dictionary with all statistics
        """
        return {
            "authentication": self.get_auth_statistics(),
            "categories": self.get_category_statistics(),
            "api": self.get_api_statistics(),
            "accessibility": self.get_accessibility_statistics(),
            "mcp": self.get_mcp_statistics(),
            "buildability": self.get_buildability_statistics(),
            "blockers": self.get_blocker_clusters(),
        }
    
    def save_reports(self) -> None:
        """Save all reports to output/reports/."""
        reports_dir = settings.REPORTS_DIR
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Save statistics
        stats = self.generate_statistics_report()
        with open(reports_dir / "statistics.json", "w") as f:
            json.dump(stats, f, indent=2, default=str)
        logger.info("Statistics report saved")
        
        # Save insights
        insights = self.generate_insights()
        with open(reports_dir / "insights.json", "w") as f:
            json.dump(insights, f, indent=2)
        logger.info("Insights report saved")
        
        # Save clusters
        clusters = self.get_blocker_clusters()
        with open(reports_dir / "clusters.json", "w") as f:
            json.dump(clusters, f, indent=2)
        logger.info("Clusters report saved")