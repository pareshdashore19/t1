from typing import Union

from pydantic import BaseModel, ConfigDict, Field

from t1.tools.schema.search_output import SearchResultsOutputModel


class GetCacheInputModel(BaseModel):
    key: str = Field(
        default=None,
        description="The input key",
    )
    model_config = ConfigDict(extra="forbid")


class SaveCacheInputModel(BaseModel):
    key: str = Field(
        default=None,
        description="The input key",
    )
    value: SearchResultsOutputModel = Field(
        default=None,
        description="The resulting value of the key to put into the cache.",
    )
    model_config = ConfigDict(extra="forbid")


class GetCacheOutputModel(BaseModel):
    result: SearchResultsOutputModel = Field(
        default=None, description="The result of the cache query."
    )
    model_config = ConfigDict(extra="forbid")
