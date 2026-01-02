from pydantic import BaseModel
from typing import Optional, List

class RunRequest(BaseModel):
    code: str
    language: str
    stdin: Optional[str] = ""
    expected_output: Optional[str] = None 

class TestCase(BaseModel):
    input: str
    output: str

class SubmitRequest(BaseModel):
    code: str
    language: str
    testcases: Optional[List[TestCase]] = None
    user_id: Optional[int] = None
    problem_slug: Optional[str] = None
