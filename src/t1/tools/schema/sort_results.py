from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from t1.tools.schema.search_output import SearchResultsOutputModel


class SortResultsInputModel(BaseModel):
    results: SearchResultsOutputModel = Field(
        ..., description="Search results that need to be sorted"
    )
    column: str = Field(..., description="Column of the dataset to sort on.")
    ascending: Optional[bool] = Field(
        default=True,
        description="Sorting order either ascending or descending. Defaults to True which is ascending.",
    )
    model_config = ConfigDict(extra="forbid")
