from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from typing import Optional, Literal, List
from datetime import datetime
from typing_extensions import Literal


class RouterResponse(BaseModel):
    response_type: str = Field(description="The response type to give to the user. It must be one of: 'create_event' or 'read_event'")

class CalendarOutput(BaseModel):
    """ A data model for structuring event details in a calendar application.

    Attributes:
        start_date (str): The start date and time of the event in YYYY-MM-DD T format.
        end_date (str): The end date and time of the event (optional) YYYY-MM-DD T format, if not mentioned then take that day's end of the day as end time
        title (str): The title or name of the event.
        description (str): A brief description of the event.

    This class ensures that event details are stored in a structured format,
    making it easy to process, validate, and integrate into scheduling systems."
    """
    start_date: str = Field(description="The start date and time of the event. YYYY-MM-DD T format")
    end_date: str = Field(description="The end date and time of the event (optional) YYYY-MM-DD T format, if not mentioned then take that day's end of the day as end time") 
    title: str = Field(description="The title or name of the event.")
    description: str =Field(description="A brief description of the event.")


class St(BaseModel):
    messages : str
    workflow : Optional[Literal["create_event", "read_event"]] = None
    cal_output : Optional[CalendarOutput] = None
    schedule_out : Optional[str]= None
    read_out : Optional[List]= None
    
