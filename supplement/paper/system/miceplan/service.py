from __future__ import annotations

import uuid

from .geometry import GeometryValidator, compute_diff
from .models import Proposal
from .parser import Parser
from .repository import InMemoryRepository, RepositoryError
from .solver import DeterministicLayoutSolver, SolveError


class ServiceError(RuntimeError):
    pass


class MICEPlanService:
    def __init__(self, repository: InMemoryRepository, parser: Parser, solver: DeterministicLayoutSolver | None = None, validator: GeometryValidator | None = None):
        self.repository = repository
        self.parser = parser
        self.solver = solver or DeterministicLayoutSolver()
        self.validator = validator or GeometryValidator()

    def preview(self, project_id: str, source_version: str, request_text: str) -> Proposal:
        source = self.repository.get_layout(project_id, source_version)
        ir = self.parser.parse(request_text, source)
        proposal = Proposal(
            id=f"proposal-{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            source_version=source_version,
            state="parsed",
            request_text=request_text,
            ir=ir,
        )
        if ir.requires_confirmation:
            proposal.state = "needs_confirmation"
            return self.repository.save_proposal(proposal)
        try:
            candidate = self.solver.solve(source, ir)
        except SolveError as exc:
            proposal.state = "infeasible"
            proposal.error = str(exc)
            return self.repository.save_proposal(proposal)
        report = self.validator.validate(source, candidate, ir)
        proposal.candidate = candidate
        proposal.validation = report
        proposal.diff = compute_diff(source, candidate)
        proposal.state = "awaiting_approval" if report.valid else "blocked"
        return self.repository.save_proposal(proposal)

    def approve(self, proposal_id: str) -> Proposal:
        proposal = self.repository.get_proposal(proposal_id)
        if proposal.state != "awaiting_approval" or proposal.candidate is None:
            raise ServiceError(f"Only an awaiting_approval proposal can be approved; current state is {proposal.state}")
        source = self.repository.get_layout(proposal.project_id, proposal.source_version)
        repeated_report = self.validator.validate(source, proposal.candidate, proposal.ir)
        if not repeated_report.valid:
            proposal.state = "blocked"
            proposal.validation = repeated_report
            raise ServiceError("Approval was blocked because repeated independent validation failed")
        accepted = self.repository.accept_candidate(proposal)
        proposal.state = "approved"
        proposal.created_version = accepted.version
        return proposal

    def reject(self, proposal_id: str) -> Proposal:
        proposal = self.repository.get_proposal(proposal_id)
        if proposal.state not in {"awaiting_approval", "needs_confirmation", "infeasible", "blocked"}:
            raise ServiceError(f"Proposal in state {proposal.state} cannot be rejected")
        proposal.state = "rejected"
        return proposal

    def list_versions(self, project_id: str) -> list[dict]:
        try:
            return [layout.to_dict() for layout in self.repository.list_layouts(project_id)]
        except RepositoryError as exc:
            raise ServiceError(str(exc)) from exc
