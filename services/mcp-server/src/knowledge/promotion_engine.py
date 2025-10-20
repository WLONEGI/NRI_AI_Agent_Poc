"""Promotion engine for escalating knowledge from personal to team level."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from knowledge.promotion_repository import PromotionRepository

DEFAULT_SIMILARITY = 0.75
DEFAULT_CONTRIBUTORS = 3
DEFAULT_COVERAGE = 0.5


@dataclass
class PromotionDecision:
    knowledge_id: str
    similarity: float
    contributors: int
    coverage: float
    status: str
    reason: str


class PromotionEngine:
    def __init__(
        self,
        *,
        repository: PromotionRepository,
        logger: logging.Logger | None = None,
        min_similarity: float = DEFAULT_SIMILARITY,
        min_contributors: int = DEFAULT_CONTRIBUTORS,
        min_coverage: float = DEFAULT_COVERAGE,
    ) -> None:
        self._repository = repository
        self._logger = logger or logging.getLogger(__name__)
        self._min_similarity = min_similarity
        self._min_contributors = min_contributors
        self._min_coverage = min_coverage

    def run(self, team_id: str, *, dry_run: bool = False) -> Dict[str, Sequence[Dict[str, object]]]:
        decisions: List[PromotionDecision] = []
        candidates = self._repository.fetch_personal_knowledge(team_id)
        for candidate in candidates:
            knowledge_id = candidate.get("id")
            similarity = float(candidate.get("similarity", 0.0))
            contributors = candidate.get("contributors", set())
            if not isinstance(contributors, set):
                contributors = set(contributors)
            coverage = float(candidate.get("coverage", 0.0))

            eligible = (
                similarity >= self._min_similarity
                and len(contributors) >= self._min_contributors
                and coverage >= self._min_coverage
            )

            if eligible:
                decision = PromotionDecision(
                    knowledge_id=knowledge_id,
                    similarity=similarity,
                    contributors=len(contributors),
                    coverage=coverage,
                    status="promoted",
                    reason="",
                )
                if not dry_run:
                    promoted_id = self._repository.promote_to_team(
                        knowledge_id=knowledge_id,
                        team_id=team_id,
                        promoted_by=None,
                    )
                    decision.reason = promoted_id
                    self._repository.record_audit_event(
                        team_id=team_id,
                        knowledge_id=knowledge_id,
                        status="promoted",
                        similarity=similarity,
                        contributor_count=len(contributors),
                        coverage=coverage,
                        reason="",
                        dry_run=False,
                    )
                decisions.append(decision)
            else:
                reason = self._build_skip_reason(similarity, len(contributors), coverage)
                decision = PromotionDecision(
                    knowledge_id=knowledge_id,
                    similarity=similarity,
                    contributors=len(contributors),
                    coverage=coverage,
                    status="skipped",
                    reason=reason,
                )
                if not dry_run:
                    self._repository.record_audit_event(
                        team_id=team_id,
                        knowledge_id=knowledge_id,
                        status="skipped",
                        similarity=similarity,
                        contributor_count=len(contributors),
                        coverage=coverage,
                        reason=reason,
                        dry_run=False,
                    )
                decisions.append(decision)

        promoted = [
            {
                "knowledge_id": d.knowledge_id,
                "similarity": d.similarity,
                "contributors": d.contributors,
                "coverage": d.coverage,
            }
            for d in decisions
            if d.status == "promoted"
        ]
        skipped = [
            {
                "knowledge_id": d.knowledge_id,
                "reason": d.reason,
                "similarity": d.similarity,
                "contributors": d.contributors,
                "coverage": d.coverage,
            }
            for d in decisions
            if d.status == "skipped"
        ]

        if promoted:
            self._logger.info("Promoted knowledge", extra={"ids": [d["knowledge_id"] for d in promoted], "team_id": team_id})

        return {"promoted": promoted, "skipped": skipped}

    def _build_skip_reason(self, similarity: float, contributors: int, coverage: float) -> str:
        if similarity < self._min_similarity:
            return "similarity_below_threshold"
        if contributors < self._min_contributors:
            return "insufficient_contributors"
        if coverage < self._min_coverage:
            return "coverage_below_threshold"
        return "unknown"
