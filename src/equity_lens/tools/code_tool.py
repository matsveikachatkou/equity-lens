from crewai.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field
from crewai_tools import CodeInterpreterTool


class CodeInput(BaseModel):
    code: Any = Field(..., description="Python3 code to execute")
    libraries_used: Any = Field(default=[], description="List of libraries used")


class RobustCodeTool(BaseTool):
    name: str = "Code Interpreter"
    description: str = (
        "Interprets Python3 code strings with a final print statement. "
        "Always include a print statement at the end to show results."
    )
    args_schema: Type[BaseModel] = CodeInput

    def _run(self, code: Any, libraries_used: Any = []) -> str:
        if isinstance(code, dict):
            code = (
                code.get("code") or
                code.get("description") or
                str(code)
            )

        if isinstance(libraries_used, str):
            libraries_used = [l.strip() for l in libraries_used.split(",") if l.strip()]
        elif not isinstance(libraries_used, list):
            libraries_used = []

        try:
            tool = CodeInterpreterTool()
            return tool.run(code=code, libraries_used=libraries_used)
        except Exception as e:
            return f'{{"error": "{str(e)}"}}'