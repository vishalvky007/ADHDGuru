from langchain.prompts import PromptTemplate
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from states import CalendarOutput
parser = PydanticOutputParser(pydantic_object=CalendarOutput)

ROUTER_PROMPT = """
You are an AI converstaional assistant and you are responsible to make descisions on what action to perform with the user's calender.
You have to take into account the whole conversation so far to make a decision to determine what would be the best next response.
GENERAL RULES:
1. Always consider the whole conversation before you make a decision.
2. Only return one of these outputs - 'create_event', 'read_event'.

IMPORTANT RULES FOR CREATING AN EVENT:
1. ONLY create an when there is an EXPLICIT request by the user to add a task or event.
2. DO NOT create events for general messages and descriptions.
3. There should be an intent of the user to create a new task in his calender. 

IMPORTANT RULES FOR READING EVENTS:
1. Only read an event if there is an explicit request by the user to know about the events.
2. Only read an event if the user wants to know about his calender.ipynb
3. Only read an event if the user wants to know about his pending or future tasks.


The output must be one of:
1. 'create_event' - only when the intent for the user is to create a new event in his calender
2. 'read_event' - only when there is an intent of the user to know about his tasks and events.



"""

CALENDER_OUTPUT_PROMPT = PromptTemplate(
    template="""
    Extract the event details from the following input and return the structured output in JSON format:

    {input_text}

    {format_instructions}
    Give output only in JSON format
    """,
    input_variables=["input_text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)