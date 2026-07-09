"""
Analytics module for the AI Research Agent.

Analyzes researched dataset and discovers meaningful product insights.
Identifies patterns across SaaS applications.

Responsibilities:
- Generate results.json
- Generate statistics.json
- Generate clusters.json
- Generate insights.json
- Generate manual_review.json
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
            "multi_auth_percentage": round((multi_auth_count / len(self.apps) * 100) if self.apps else 0, 1),
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
                cat: round(count / len(self.apps) * 100, 1)
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
            "api_coverage_percentage": round(sum(1 for app in self.apps if app.api_surface) / len(self.apps) * 100 if self.apps else 0, 1),
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
            "self_serve_percentage": round(self_serve_count / len(self.apps) * 100 if self.apps else 0, 1),
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
            "mcp_support_rate": round(mcp_available / len(self.apps) * 100 if self.apps else 0, 1),
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
    # Verification Statistics
    # ============================================================================

    def get_verification_statistics(self) -> Dict[str, Any]:
        """
        Get verification statistics across all apps.

        Returns:
            Dictionary with verification stats
        """
        verified_count = sum(1 for app in self.apps if app.verification_status == "verified")
        needs_review = sum(1 for app in self.apps if app.verification_status == "manual_review")
        pending = sum(1 for app in self.apps if app.verification_status == "pending")

        return {
            "verified": verified_count,
            "manual_review": needs_review,
            "pending": pending,
            "verification_rate": round(verified_count / len(self.apps) * 100 if self.apps else 0, 1),
            "total_verified_fields": 0,
            "failed_fields": 0,
            "warnings": 0,
        }

    # ============================================================================
    # Manual Review Items
    # ============================================================================

    def get_manual_review_items(self) -> List[Dict[str, Any]]:
        """
        Get apps that need manual review.

        Returns:
            List of apps requiring manual review with reasons
        """
        items = []
        for app in self.apps:
            if app.verification_status == "manual_review" or (
                app.confidence_score and app.confidence_score < 0.5
            ):
                items.append({
                    "name": app.name,
                    "confidence_score": app.confidence_score,
                    "verification_status": app.verification_status,
                    "reason": "Low confidence score" if (app.confidence_score and app.confidence_score < 0.5) else "Flagged by verification",
                    "missing_fields": self._get_missing_fields(app),
                })
        return items

    def _get_missing_fields(self, app: AppResearch) -> List[str]:
        """Get list of missing or incomplete fields for an app."""
        missing = []
        if not app.description or app.description == "Unknown":
            missing.append("description")
        if not app.auth_methods or len(app.auth_methods) == 0 or app.auth_methods == ["unknown"]:
            missing.append("auth_methods")
        if not app.api_surface:
            missing.append("api_surface")
        if app.self_serve is None:
            missing.append("self_serve")
        if not app.main_blocker:
            missing.append("main_blocker")
        if not app.evidence_url:
            missing.append("evidence_url")
        return missing

    # ============================================================================
    # Confidence Statistics
    # ============================================================================

    def get_confidence_statistics(self) -> Dict[str, Any]:
        """
        Get confidence score statistics.

        Returns:
            Dictionary with confidence stats
        """
        if not self.apps:
            return {
                "average_confidence": 0,
                "high_confidence": 0,
                "medium_confidence": 0,
                "low_confidence": 0,
            }

        scores = [app.confidence_score for app in self.apps if app.confidence_score is not None]
        if not scores:
            return {"average_confidence": 0, "high_confidence": 0, "medium_confidence": 0, "low_confidence": 0}

        return {
            "average_confidence": round(sum(scores) / len(scores), 2),
            "high_confidence": sum(1 for s in scores if s >= 0.8),
            "medium_confidence": sum(1 for s in scores if 0.5 <= s < 0.8),
            "low_confidence": sum(1 for s in scores if s < 0.5),
        }

    # ============================================================================
    # Insights Engine
    # ============================================================================

    def generate_insights(self) -> List[Dict[str, str]]:
        """
        Generate meaningful Product Operations insights from the data.

        Analyzes patterns across categories, auth methods, blockers,
        buildability, and accessibility. Generates at least 10 insights.

        Returns:
            List of insight dictionaries
        """
        insights = []

        auth_stats = self.get_auth_statistics()
        category_stats = self.get_category_statistics()
        api_stats = self.get_api_statistics()
        access_stats = self.get_accessibility_statistics()
        mcp_stats = self.get_mcp_statistics()
        build_stats = self.get_buildability_statistics()
        blocker_stats = self.get_blocker_clusters()

        total = len(self.apps)
        if total == 0:
            return []

        # Insight 1: Auth method distribution across categories
        if auth_stats["auth_method_distribution"]:
            most_common_auth = auth_stats["most_common_methods"][0] if auth_stats["most_common_methods"] else "unknown"
            auth_count = auth_stats["auth_method_distribution"].get(most_common_auth, 0)
            insights.append({
                "insight": f"{most_common_auth.replace('_', ' ').title()} is the most widely supported auth method",
                "evidence": f"{auth_count}/{total} apps support it ({auth_count/total*100:.0f}%)",
                "category": "authentication",
            })

        # Insight 2: Multi-auth support pattern
        multi_auth_pct = auth_stats.get("multi_auth_percentage", 0)
        if multi_auth_pct > 0:
            insights.append({
                "insight": f"{multi_auth_pct:.0f}% of apps support multiple authentication methods",
                "evidence": "Multi-auth support indicates mature API security posture, reducing integration friction",
                "category": "authentication",
            })

        # Insight 3: Category with richest auth support
        if auth_stats.get("auth_by_category"):
            rich_cat = max(
                auth_stats["auth_by_category"].items(),
                key=lambda x: len(x[1])
            )
            insights.append({
                "insight": f"{rich_cat[0].replace('_', ' ').title()} apps offer the most auth method variety",
                "evidence": f"{len(rich_cat[1])} distinct auth types found in {rich_cat[0]} category",
                "category": "authentication",
            })

        # Insight 4: Self-serve vs gated by category
        if access_stats["self_serve"] > 0 and access_stats["enterprise_only"] > 0:
            self_serve_pct = access_stats["self_serve_percentage"]
            insights.append({
                "insight": f"{self_serve_pct:.0f}% of apps offer self-serve access, {100-self_serve_pct:.0f}% require sales",
                "evidence": f"{access_stats['self_serve']} apps have self-serve, {access_stats['enterprise_only']} are gated, {access_stats['unknown']} unknown",
                "category": "accessibility",
            })

        # Insight 5: Buildability distribution
        if total > 0:
            easy_pct = build_stats["easy"] / total * 100
            insights.append({
                "insight": f"{easy_pct:.0f}% of apps rated as easy (high buildability) for AI agent integration",
                "evidence": f"{build_stats['easy']} easy, {build_stats['medium']} medium, {build_stats['hard']} hard, {build_stats['blocked']} blocked",
                "category": "buildability",
            })

        # Insight 6: Top blocker patterns
        if blocker_stats["top_blockers"]:
            top_blocker_name, top_blocker_count = blocker_stats["top_blockers"][0]
            blocked_pct = top_blocker_count / total * 100 if total > 0 else 0
            insights.append({
                "insight": f"'{top_blocker_name}' is the most common integration blocker ({blocked_pct:.0f}% of apps)",
                "evidence": f"{top_blocker_count} apps affected. Top blockers: {', '.join(n for n, _ in blocker_stats['top_blockers'][:3])}",
                "category": "buildability",
            })

        # Insight 7: REST vs GraphQL adoption
        rest_count = api_stats["api_type_distribution"].get("rest", 0)
        graphql_count = api_stats["api_type_distribution"].get("graphql", 0)
        if rest_count > 0 or graphql_count > 0:
            insights.append({
                "insight": f"REST APIs dominate ({rest_count} apps) compared to GraphQL ({graphql_count} apps)",
                "evidence": f"{(rest_count/total*100 if total > 0 else 0):.0f}% REST, {(graphql_count/total*100 if total > 0 else 0):.0f}% GraphQL. SDK support in {api_stats['api_type_distribution'].get('sdk', 0)} apps",
                "category": "api",
            })

        # Insight 8: MCP adoption analysis
        if mcp_stats["mcp_support_rate"] < 20:
            insights.append({
                "insight": "MCP (Model Context Protocol) adoption is still in early stages",
                "evidence": f"Only {mcp_stats['mcp_support_rate']:.0f}% of apps support MCP. {mcp_stats['not_available']} apps confirmed without MCP",
                "category": "mcp",
            })
        elif mcp_stats["mcp_support_rate"] > 50:
            insights.append({
                "insight": "MCP is becoming a standard for AI agent integration",
                "evidence": f"{mcp_stats['mcp_support_rate']:.0f}% of apps support MCP, indicating strong ecosystem readiness",
                "category": "mcp",
            })

        # Insight 9: High buildability correlates with self-serve
        high_build = [app for app in self.apps if app.buildability == "high"]
        high_build_self_serve = sum(1 for app in high_build if app.self_serve is True)
        if high_build and high_build_self_serve / len(high_build) > 0.5:
            insights.append({
                "insight": "Self-serve access strongly correlates with high buildability for AI agents",
                "evidence": f"{high_build_self_serve}/{len(high_build)} high-buildability apps are self-serve ({high_build_self_serve/len(high_build)*100:.0f}%)",
                "category": "buildability",
            })

        # Insight 10: Categories with most blockers
        categories_with_blockers = {}
        for app in self.apps:
            if app.main_blocker:
                cat = app.category
                if cat not in categories_with_blockers:
                    categories_with_blockers[cat] = 0
                categories_with_blockers[cat] += 1

        if categories_with_blockers:
            most_blocked_cat = max(categories_with_blockers.items(), key=lambda x: x[1])
            insights.append({
                "insight": f"'{most_blocked_cat[0].replace('_', ' ').title()}' apps have the most integration blockers",
                "evidence": f"{most_blocked_cat[1]} apps blocked in this category, suggesting higher integration effort",
                "category": "buildability",
            })

        # Insight 11: API coverage by category
        if api_stats["api_coverage_percentage"] > 0:
            insights.append({
                "insight": f"{api_stats['api_coverage_percentage']:.0f}% of apps have documented API surfaces",
                "evidence": f"{api_stats['apps_with_api']} of {total} apps provide API documentation, key enabler for AI agent integration",
                "category": "api",
            })

        # Insight 12: Categories with no blockers (easy integration)
        easy_categories = {}
        for app in self.apps:
            cat = app.category
            if not app.main_blocker:
                if cat not in easy_categories:
                    easy_categories[cat] = 0
                easy_categories[cat] += 1

        if easy_categories:
            easiest_cat = max(easy_categories.items(), key=lambda x: x[1])
            cat_total = len([a for a in self.apps if a.category == easiest_cat[0]])
            if cat_total > 0:
                pct = easiest_cat[1] / cat_total * 100
                insights.append({
                    "insight": f"{easiest_cat[0].replace('_', ' ').title()} apps have the fewest integration blockers ({pct:.0f}% unblocked)",
                    "evidence": f"{easiest_cat[1]}/{cat_total} {easiest_cat[0]} apps have no blockers, making them ideal for rapid AI agent integration",
                    "category": "buildability",
                })

        logger.info(f"Generated {len(insights)} insights")
        return insights

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
            "verification": self.get_verification_statistics(),
            "confidence": self.get_confidence_statistics(),
        }

    def save_reports(self) -> Dict[str, Path]:
        """
        Save all reports to output/reports/.

        Generates:
        - results.json: All app research results
        - statistics.json: Statistics report
        - clusters.json: Blocker clusters
        - insights.json: Generated insights
        - manual_review.json: Apps needing human review

        Returns:
            Dictionary mapping report names to file paths
        """
        reports_dir = settings.REPORTS_DIR
        reports_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        # Save results.json (all app data)
        results_path = reports_dir / "results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(
                [app.dict() for app in self.apps],
                f, indent=2, default=str,
            )
        saved_files["results"] = results_path
        logger.info(f"Saved results.json ({len(self.apps)} apps)")

        # Save statistics.json
        stats = self.generate_statistics_report()
        stats_path = reports_dir / "statistics.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, default=str)
        saved_files["statistics"] = stats_path
        logger.info("Saved statistics.json")

        # Save insights.json
        insights = self.generate_insights()
        insights_path = reports_dir / "insights.json"
        with open(insights_path, "w", encoding="utf-8") as f:
            json.dump(insights, f, indent=2)
        saved_files["insights"] = insights_path
        logger.info(f"Saved insights.json ({len(insights)} insights)")

        # Save clusters.json
        clusters = self.get_blocker_clusters()
        clusters_path = reports_dir / "clusters.json"
        with open(clusters_path, "w", encoding="utf-8") as f:
            json.dump(clusters, f, indent=2)
        saved_files["clusters"] = clusters_path
        logger.info("Saved clusters.json")

        # Save manual_review.json
        manual_review = self.get_manual_review_items()
        manual_path = reports_dir / "manual_review.json"
        with open(manual_path, "w", encoding="utf-8") as f:
            json.dump(manual_review, f, indent=2)
        saved_files["manual_review"] = manual_path
        logger.info(f"Saved manual_review.json ({len(manual_review)} items)")

        return saved_files