from enum import Enum

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    COMPANY = "Company"
    LOCATION = "Location"
    EVENT = "Event"
    MATERIAL = "Material"
    PRODUCT = "Product"


class RelationType(str, Enum):
    """Edge direction = direction in which a disruption propagates.

    AFFECTS   Event    -> Location | Company | Material | Product
    HOSTS     Location -> Company            (company operates a site there)
    SUPPLIES  Company  -> Company            (supplier -> customer)
    INPUT_TO  Material | Product -> Product | Company
    """

    AFFECTS = "AFFECTS"
    HOSTS = "HOSTS"
    SUPPLIES = "SUPPLIES"
    INPUT_TO = "INPUT_TO"


class Relation(BaseModel):
    source: str = Field(description="Canonical name of the source entity")
    source_type: EntityType
    relation: RelationType
    target: str = Field(description="Canonical name of the target entity")
    target_type: EntityType
    evidence: str = Field(description="Short quote (max 25 words) from the article supporting this relation")
    confidence: float = Field(ge=0, le=1)


class Extraction(BaseModel):
    relations: list[Relation] = Field(default_factory=list)


class Article(BaseModel):
    url: str
    title: str
    published: str = ""
    text: str = ""


def entity_key(name: str, etype: EntityType | str) -> str:
    t = etype.value if isinstance(etype, EntityType) else etype
    return f"{t.lower()}:{' '.join(name.split()).casefold()}"
