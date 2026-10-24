"""
Adapters grouped by the port they implement: one folder per port, one module per adapter. The
folders mirror ports/, so the adapters of the datasource/ ports are grouped the same.
The repositories are not here: they are concrete (ports/repository/), built on a DataSource and a Parser.
"""
from .database import PostgresDatabase
from .datasource.file_datasource import LocalDataSource, S3DataSource
from .datasource.parser import SqlPipeParser, SqlTableParser, TaskParser, YamlParser, YamlTaskDependenciesParser
from .task_runner import SqlDdlRunner, SqlEtlRunner, SqlRawLoadRunner
from .task_type import EtlTaskType, RawLoadTaskType

__all__ = [
    "LocalDataSource",
    "S3DataSource",
    "YamlParser",
    "YamlTaskDependenciesParser",
    "TaskParser",
    "SqlPipeParser",
    "SqlTableParser",
    "PostgresDatabase",
    "EtlTaskType",
    "RawLoadTaskType",
    "SqlDdlRunner",
    "SqlEtlRunner",
    "SqlRawLoadRunner",
]
