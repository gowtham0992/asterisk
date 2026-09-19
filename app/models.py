from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Artifact(StrictModel):
    name: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9][A-Za-z0-9_.-]*\.(csv|md|txt)$')
    content: str = Field(min_length=1, max_length=1_500_000)


class AuditInput(StrictModel):
    title: str = Field(min_length=1, max_length=120)
    claim: str = Field(min_length=12, max_length=2000)
    files: list[Artifact] = Field(min_length=2, max_length=8)

    @model_validator(mode='after')
    def check_files(self):
        if len({f.name for f in self.files}) != len(self.files):
            raise ValueError('File names must be unique.')
        if sum(len(f.content.encode()) for f in self.files) > 4_000_000:
            raise ValueError('Total input size must not exceed 4 MB.')
        if not any(f.name.endswith('.csv') for f in self.files):
            raise ValueError('Add at least one CSV file.')
        if not any(f.name.endswith(('.md', '.txt')) for f in self.files):
            raise ValueError('Add a text or Markdown document explaining the dataset.')
        return self


class Citation(StrictModel):
    file: str = Field(max_length=100)
    quote: str = Field(min_length=12, max_length=1000)


class Rule(StrictModel):
    unit: str = Field(min_length=1, max_length=80)
    explanation: str = Field(min_length=1, max_length=2000)
    split_file: str = Field(max_length=100)
    sample_column: str = Field(max_length=100)
    partition_column: str = Field(max_length=100)
    train_values: list[str] = Field(min_length=1, max_length=10)
    test_values: list[str] = Field(min_length=1, max_length=10)
    mapping_file: str | None = Field(default=None, max_length=100)
    mapping_sample_column: str | None = Field(default=None, max_length=100)
    entity_column: str = Field(max_length=100)
    citations: list[Citation] = Field(min_length=1, max_length=6)
    limitations: list[str] = Field(max_length=8)


class Proposal(StrictModel):
    status: Literal['ready', 'insufficient']
    rule: Rule | None = None
    questions: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode='after')
    def consistency(self):
        if self.status == 'ready' and self.rule is None:
            raise ValueError('A ready proposal needs a rule.')
        if self.status == 'insufficient' and not self.questions:
            raise ValueError('Specify the missing evidence.')
        return self


class RuleRevision(StrictModel):
    rule: Rule
    note: str = Field(min_length=8, max_length=1000)


class ExecutionRequest(StrictModel):
    remote: bool = False
    confirm_upload: bool = False
