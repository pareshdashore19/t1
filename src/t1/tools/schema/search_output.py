from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchResultsOutputModel(BaseModel):
    search_results: List[Dict] = Field(
        default=None, description="List of search results."
    )
    query_summary: Optional[str] = Field(
        default=None, description="Response to customer."
    )
    model_config = ConfigDict(extra="forbid")
