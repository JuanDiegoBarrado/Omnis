from omnis.domain import Pipe
from omnis.ports.repository.repository import Repository


class PipeRepository(Repository[Pipe]):
    """The pipes of one flow, under artifacts/pipes/."""

    location = "artifacts/pipes"
