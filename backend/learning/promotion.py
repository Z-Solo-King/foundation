"""Self-improvement infrastructure with shadow/canary/rollback.

Measures behavior changes via regression tests, shadows old vs new,
canalies on subset, promotes with thresholds, auto-rollbacks on failure.

Protected policy (privacy, security, access controls) is immutable.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Callable, Any


class PromotionMode(StrEnum):
    SHADOW = "shadow"  # Old and new in parallel, no change to production
    CANARY = "canary"  # Route small sample to new version
    PROMOTED = "promoted"  # New version fully live
    ROLLED_BACK = "rolled_back"  # Reverted to previous version


@dataclass(frozen=True)
class BehaviorChange:
    """Proposed behavior change."""
    change_id: str
    description: str
    affected_component: str  # e.g., "extractor", "verifier", "router"
    old_implementation: Callable
    new_implementation: Callable
    is_mutable: bool = True  # False for protected policy
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.now(timezone.utc))


@dataclass(frozen=True)
class EvaluationMetrics:
    """Metrics from running old vs new implementation."""
    old_score: float  # 0-100
    new_score: float  # 0-100
    improvement: float  # new - old
    latency_old_ms: float
    latency_new_ms: float
    regression_count: int  # Cases that got worse
    improvement_count: int  # Cases that got better
    neutral_count: int  # Cases unchanged


class PromotionGate:
    """Controls promotion of behavior changes."""
    
    SHADOW_REGRESSION_THRESHOLD = 0.05  # 5% regression acceptable in shadow
    CANARY_REGRESSION_THRESHOLD = 0.02  # 2% regression acceptable in canary
    PROMOTION_IMPROVEMENT_THRESHOLD = 0.01  # 1% improvement required
    ROLLBACK_THRESHOLD = 0.1  # 10% regression triggers rollback
    
    def __init__(self):
        self._changes: dict[str, BehaviorChange] = {}
        self._modes: dict[str, PromotionMode] = {}
        self._metrics: dict[str, EvaluationMetrics] = {}
    
    def register_change(self, change: BehaviorChange) -> None:
        """Register a proposed behavior change.
        
        Args:
            change: BehaviorChange to evaluate
            
        Raises:
            ValueError: If protected policy change is attempted
        """
        if not change.is_mutable:
            raise ValueError(f"cannot modify protected policy: {change.affected_component}")
        
        if change.change_id in self._changes:
            raise ValueError(f"change {change.change_id} already registered")
        
        self._changes[change.change_id] = change
        self._modes[change.change_id] = PromotionMode.SHADOW
    
    def shadow_evaluation(
        self,
        change_id: str,
        test_cases: list[Any],
        evaluator: Callable,
    ) -> EvaluationMetrics:
        """Run old and new in parallel; measure regression.
        
        Args:
            change_id: ID of registered change
            test_cases: Test cases to evaluate
            evaluator: Function that scores (old_output, new_output, expected)
            
        Returns:
            EvaluationMetrics with old vs new scores
        """
        change = self._changes[change_id]
        
        old_scores = []
        new_scores = []
        old_latency = []
        new_latency = []
        
        for case in test_cases:
            # Old implementation
            import time
            start = time.time()
            try:
                old_result = change.old_implementation(case)
                old_latency.append((time.time() - start) * 1000)
            except Exception:
                old_result = None
                old_latency.append(None)
            
            # New implementation
            start = time.time()
            try:
                new_result = change.new_implementation(case)
                new_latency.append((time.time() - start) * 1000)
            except Exception:
                new_result = None
                new_latency.append(None)
            
            # Score
            score_old, score_new = evaluator(old_result, new_result, case)
            old_scores.append(score_old)
            new_scores.append(score_new)
        
        old_avg = sum(old_scores) / len(old_scores) if old_scores else 0
        new_avg = sum(new_scores) / len(new_scores) if new_scores else 0
        
        regression = sum(1 for o, n in zip(old_scores, new_scores) if n < o)
        improvement = sum(1 for o, n in zip(old_scores, new_scores) if n > o)
        neutral = len(old_scores) - regression - improvement
        
        old_lat_avg = sum(l for l in old_latency if l) / len([l for l in old_latency if l]) if old_latency else 0
        new_lat_avg = sum(l for l in new_latency if l) / len([l for l in new_latency if l]) if new_latency else 0
        
        metrics = EvaluationMetrics(
            old_score=old_avg,
            new_score=new_avg,
            improvement=new_avg - old_avg,
            latency_old_ms=old_lat_avg,
            latency_new_ms=new_lat_avg,
            regression_count=regression,
            improvement_count=improvement,
            neutral_count=neutral,
        )
        
        self._metrics[change_id] = metrics
        return metrics
    
    def approve_canary(
        self,
        change_id: str,
        metrics: EvaluationMetrics,
    ) -> tuple[bool, str]:
        """Check if metrics support promotion to canary.
        
        Args:
            change_id: ID of change
            metrics: Metrics from shadow evaluation
            
        Returns:
            (approved, reason)
        """
        regression_rate = metrics.regression_count / (metrics.regression_count + metrics.improvement_count + metrics.neutral_count) if (metrics.regression_count + metrics.improvement_count + metrics.neutral_count) > 0 else 0
        
        if regression_rate > self.SHADOW_REGRESSION_THRESHOLD:
            return False, f"regression rate {regression_rate:.1%} exceeds shadow threshold {self.SHADOW_REGRESSION_THRESHOLD:.1%}"
        
        if metrics.improvement <= 0:
            return False, "no measurable improvement"
        
        self._modes[change_id] = PromotionMode.CANARY
        return True, "approved for canary"
    
    def approve_promotion(
        self,
        change_id: str,
        canary_metrics: EvaluationMetrics,
    ) -> tuple[bool, str]:
        """Check if canary metrics support full promotion.
        
        Args:
            change_id: ID of change
            canary_metrics: Metrics from canary evaluation
            
        Returns:
            (approved, reason)
        """
        regression_rate = canary_metrics.regression_count / (canary_metrics.regression_count + canary_metrics.improvement_count + canary_metrics.neutral_count) if (canary_metrics.regression_count + canary_metrics.improvement_count + canary_metrics.neutral_count) > 0 else 0
        
        if regression_rate > self.CANARY_REGRESSION_THRESHOLD:
            return False, f"canary regression rate {regression_rate:.1%} exceeds threshold {self.CANARY_REGRESSION_THRESHOLD:.1%}"
        
        if canary_metrics.improvement < self.PROMOTION_IMPROVEMENT_THRESHOLD:
            return False, f"improvement {canary_metrics.improvement:.1%} below threshold {self.PROMOTION_IMPROVEMENT_THRESHOLD:.1%}"
        
        self._modes[change_id] = PromotionMode.PROMOTED
        return True, "promoted to production"
    
    def check_rollback(
        self,
        change_id: str,
        production_metrics: EvaluationMetrics,
    ) -> tuple[bool, str]:
        """Check if production metrics warrant automatic rollback.
        
        Args:
            change_id: ID of change
            production_metrics: Metrics from production
            
        Returns:
            (should_rollback, reason)
        """
        regression_rate = production_metrics.regression_count / (production_metrics.regression_count + production_metrics.improvement_count + production_metrics.neutral_count) if (production_metrics.regression_count + production_metrics.improvement_count + production_metrics.neutral_count) > 0 else 0
        
        if regression_rate > self.ROLLBACK_THRESHOLD:
            self._modes[change_id] = PromotionMode.ROLLED_BACK
            return True, f"production regression {regression_rate:.1%} exceeds rollback threshold {self.ROLLBACK_THRESHOLD:.1%}"
        
        return False, "metrics within acceptable range"
