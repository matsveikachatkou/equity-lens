from crewai.tools import BaseTool
from typing import Type, Union
from pydantic import BaseModel, Field
import os
import requests


class NotificationInput(BaseModel):
    """Input schema for push notification"""
    message: Union[str, dict] = Field(..., description="The message to send to the user.")


class PushNotifyTool(BaseTool):
    name: str = "Send Push Notification"
    description: str = (
        "Sends a push notification to the analyst's mobile device. "
        "Use this to alert the user when an investment decision has been made. "
        "Include company name, ticker, and a one-sentence rationale in the message."
    )
    args_schema: Type[BaseModel] = NotificationInput

    def _run(self, message: Union[str, dict]) -> str:
        # Handle case where LLM passes a dict instead of a plain string
        if isinstance(message, dict):
            message = (
                message.get("message") or
                message.get("description") or
                message.get("text") or
                str(message)
            )

        pushover_user = os.getenv("PUSHOVER_USER")
        pushover_token = os.getenv("PUSHOVER_TOKEN")

        if not pushover_user or not pushover_token:
            return '{"notification": "skipped - credentials not configured"}'

        pushover_url = "https://api.pushover.net/1/messages.json"
        payload = {
            "user": pushover_user,
            "token": pushover_token,
            "message": message,
            "title": "Equity Lens — Investment Decision"
        }

        try:
            response = requests.post(pushover_url, data=payload, timeout=10)
            response.raise_for_status()
            return '{"notification": "sent"}'
        except requests.exceptions.RequestException as e:
            return f'{{"notification": "failed", "error": "{str(e)}"}}'