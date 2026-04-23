from __future__ import annotations
from dataclasses import dataclass, field


# ------------------------------------------------------------------
# Base
# ------------------------------------------------------------------

@dataclass
class ASTNode:
    """Abstract base for all RetailLang AST nodes."""

    def to_dict(self) -> dict:
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}({self.to_dict()})"


# ------------------------------------------------------------------
# Root
# ------------------------------------------------------------------

@dataclass
class ProgramNode(ASTNode):
    body: list[ASTNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "Program",
            "body": [node.to_dict() for node in self.body],
        }


# ------------------------------------------------------------------
# Statements
# ------------------------------------------------------------------

@dataclass
class LoadStatement(ASTNode):
    filename: str
    alias:    str | None = None

    def to_dict(self) -> dict:
        return {
            "type":     "LoadStatement",
            "filename": self.filename,
            "alias":    self.alias,
        }


@dataclass
class Condition:
    column:   str
    operator: str
    value:    str | float

    def to_dict(self) -> dict:
        return {
            "column":   self.column,
            "operator": self.operator,
            "value":    self.value,
        }


@dataclass
class FilterStatement(ASTNode):
    conditions: list[Condition] = field(default_factory=list)
    bool_op:    str             = "and"

    def to_dict(self) -> dict:
        return {
            "type":       "FilterStatement",
            "bool_op":    self.bool_op,
            "conditions": [c.to_dict() for c in self.conditions],
        }


@dataclass
class ComputeStatement(ASTNode):
    aggregation: str
    column:      str
    group_by:    list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type":        "ComputeStatement",
            "aggregation": self.aggregation,
            "column":      self.column,
            "group_by":    self.group_by,
        }


@dataclass
class ChartStatement(ASTNode):
    chart_type: str
    x:          str           = ""
    y:          str           = ""
    title:      str | None    = None
    compare:    list[str]     = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type":       "ChartStatement",
            "chart_type": self.chart_type,
            "x":          self.x,
            "y":          self.y,
            "title":      self.title,
            "compare":    self.compare,
        }


@dataclass
class PivotStatement(ASTNode):
    index:   str
    columns: str
    values:  str
    aggfunc: str = "sum"

    def to_dict(self) -> dict:
        return {
            "type":    "PivotStatement",
            "index":   self.index,
            "columns": self.columns,
            "values":  self.values,
            "aggfunc": self.aggfunc,
        }


@dataclass
class SortStatement(ASTNode):
    column:    str
    direction: str = "desc"

    def to_dict(self) -> dict:
        return {
            "type":      "SortStatement",
            "column":    self.column,
            "direction": self.direction,
        }