from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EtlFile(BaseModel):
    """Structure of an ETL file (dags/<flow>/etls/<etl>.yaml)."""

    model_config = ConfigDict(extra="forbid")

    destination: str
    pipe: str
    strategy: Literal["full_rebuild", "merge"] = "full_rebuild"
    key: list[str] = Field(default_factory=list)
    pre_statement: str | None = None
    post_statement: str | None = None


class EtlNodeFile(BaseModel):
    """A node of a flow that runs the ETL of the same name."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["etl"] = "etl"
    after: list[str] = Field(default_factory=list)


class RawLoadNodeFile(BaseModel):
    """A node of a flow that lands the raw files under `source` into `destination`."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["raw_load"]
    source: str
    destination: str
    columns: list[str]
    after: list[str] = Field(default_factory=list)


class EtlGraphFile(BaseModel):
    """Structure of the graph of a flow (dags/<flow>/graph.yaml)."""

    model_config = ConfigDict(extra="forbid")

    nodes: dict[str, EtlNodeFile | RawLoadNodeFile]
