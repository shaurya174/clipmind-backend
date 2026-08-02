from pydantic import BaseModel

class SummarizeRequest(BaseModel):
    url: str