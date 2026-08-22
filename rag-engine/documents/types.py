"""Document-template types used by the generator."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


Requirement = Literal["required", "optional", "recommended"]
ProvisionClass = Literal["required", "recommended", "user_specific"]
FieldType = Literal[
    "text",
    "textarea",
    "select",
    "date",
    "number",
    "currency",
    "checkbox",
    "email",
    "tel",
]
Category = Literal["agreement", "legal_document"]


class FieldOption(TypedDict):
    value: str
    label: str


class FieldSpec(TypedDict, total=False):
    id: str
    label: str
    placeholder_label: str
    type: FieldType
    requirement: Requirement
    step: str
    help: str
    options: list[FieldOption]
    min: float
    max: float
    pattern: str


class StepSpec(TypedDict, total=False):
    id: str
    title: str
    description: str
    field_ids: list[str]


class PartySpec(TypedDict):
    id: str
    role: str
    name_field: str
    type_field: str
    address_field: str


class ClauseSpec(TypedDict, total=False):
    id: str
    title: str
    required: bool
    provision_class: ProvisionClass
    needs_legal_context: bool
    include_signature: bool
    condition: dict[str, Any] | None
    body: str


class TemplateSpec(TypedDict):
    id: str
    category: Category
    title: str
    description: str
    document_type: str
    jurisdiction_country: str
    legal_query: str
    parties: list[PartySpec]
    steps: list[StepSpec]
    fields: list[FieldSpec]
    clauses: list[ClauseSpec]
