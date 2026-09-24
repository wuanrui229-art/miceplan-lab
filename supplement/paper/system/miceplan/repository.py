from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from .models import HallLayout, Proposal


class RepositoryError(RuntimeError):
    pass


class InMemoryRepository:
    """Small immutable-version repository used by the prototype and tests."""

    def __init__(self, project_id: str, initial_layout: HallLayout):
        self._projects: dict[str, dict[str, HallLayout]] = {project_id: {initial_layout.version: initial_layout}}
        self._proposals: dict[str, Proposal] = {}

    def get_layout(self, project_id: str, version: str) -> HallLayout:
        try:
            return self._projects[project_id][version]
        except KeyError as exc:
            raise RepositoryError(f"Unknown project/version: {project_id}/{version}") from exc

    def list_layouts(self, project_id: str) -> tuple[HallLayout, ...]:
        try:
            return tuple(self._projects[project_id].values())
        except KeyError as exc:
            raise RepositoryError(f"Unknown project: {project_id}") from exc

    def save_proposal(self, proposal: Proposal) -> Proposal:
        self._proposals[proposal.id] = proposal
        return proposal

    def get_proposal(self, proposal_id: str) -> Proposal:
        try:
            return self._proposals[proposal_id]
        except KeyError as exc:
            raise RepositoryError(f"Unknown proposal: {proposal_id}") from exc

    def accept_candidate(self, proposal: Proposal) -> HallLayout:
        if proposal.candidate is None:
            raise RepositoryError("A proposal without a candidate cannot be accepted")
        versions = self._projects[proposal.project_id]
        new_version = f"v{len(versions) + 1}"
        if new_version in versions:
            raise RepositoryError(f"Version already exists: {new_version}")
        accepted = replace(
            proposal.candidate,
            version=new_version,
            parent_version=proposal.source_version,
            request_id=proposal.ir.request_id,
            accepted_at=datetime.now(timezone.utc).isoformat(),
        )
        versions[new_version] = accepted
        return accepted
