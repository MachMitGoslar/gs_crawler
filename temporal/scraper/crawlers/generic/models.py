from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Config — pydantic. Validated on construction, serialises for Temporal.
# ---------------------------------------------------------------------------

class Selector(BaseModel):
    """
    One field selector. Extra keys (e.g. nested-only 'template') are rejected
    so typos in YAML surface immediately.
    """
    selector: str = ""
    attribute: str = "text"
    prefix: str = ""
    regex: Optional[str] = None
    exclude: Optional[str] = None
    fallback: Optional[str] = None
    default: Optional[str] = None
    date_format: Optional[str] = None
    # nested-only
    template: Optional[str] = None
    item_id_attribute: str = "id"


class Items(BaseModel):
    selector: str = ""
    image_url: Optional[Selector] = None
    call_to_action_url: Optional[Selector] = None


class Selectors(BaseModel):
    container: str = ""
    title: Optional[Selector] = None
    description: Optional[Selector] = None
    image_url: Optional[Selector] = None
    call_to_action_url: Optional[Selector] = None
    published_at: Optional[Selector] = None
    category_title: Optional[Selector] = None
    items: Optional[Items] = None


class PostProcess(BaseModel):
    single_description_template: Optional[str] = None


class OutputVariant(BaseModel):
    enabled: bool = False
    filename: Optional[str] = None
    title_override: Optional[str] = None
    image_override: Optional[str] = None
    cta_override: Optional[str] = None


class Output(BaseModel):
    single: OutputVariant = Field(default_factory=OutputVariant)
    all: OutputVariant = Field(default_factory=OutputVariant)


class Selection(BaseModel):
    strategy: Literal["first", "random", "latest"] = "random"


class GenericCrawlerConfig(BaseModel):
    id: str
    name: str
    url: str
    base_url: str = ""
    type: Literal["simple", "nested"] = "simple"
    schedule: Optional[str] = None
    run_on_start: bool = False
    selectors: Selectors = Field(default_factory=Selectors)
    post_process: PostProcess = Field(default_factory=PostProcess)
    output: Output = Field(default_factory=Output)
    selection: Selection = Field(default_factory=Selection)

    @model_validator(mode="after")
    def _fill_base_url(self) -> "GenericCrawlerConfig":
        if not self.base_url:
            self.base_url = self.url
        return self


# ---------------------------------------------------------------------------
# Runtime data
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ScrapedEntry:
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    call_to_action_url: Optional[str] = None
    published_at: str = ""

    @property
    def has_content(self) -> bool:
        return bool(self.title or self.description)


@dataclass(slots=True)
class SingleCard:
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    call_to_action_url: Optional[str] = None
    published_at: str = ""


@dataclass(slots=True)
class ScrapeResult:
    crawler_id: str
    scraped_at: datetime
    all_entries: list[ScrapedEntry]
    single_entry: Optional[SingleCard]

    @property
    def entry_count(self) -> int:
        return len(self.all_entries)