from langgraph.graph import StateGraph, START, END
# from IPython.display import Image, display
from langgraph.graph import MessagesState
from states import RouterResponse, CalendarOutput, St
from typing_extensions import Literal
from helper import get_router_chain, get_llm
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from prompts import CALENDER_OUTPUT_PROMPT
from langchain_google_community.calendar.create_event import CalendarCreateEvent
# from langchain_google_community.calendar.get_calendars_info import GetCalendarsInfo
from langchain_google_community.calendar.search_events import CalendarSearchEvents

import ast
import traceback
import datetime


class CalApp:
    
    def router_node(self, state: St) -> St:
        try:
            chain = get_router_chain()
            # a = St()
            # a.workflow = chain.invoke({'messages': [state.messages]}).response_type
            # a.messages = state.messages
            state.workflow = chain.invoke({'messages': state.messages}).response_type
            return state
        except Exception as e:
                raise(e)



    def select_workflow(
        self, state: St,
    ) -> Literal["create_event_node", "read_event_node"]:
        workflow = state.workflow

        if workflow == "create_event":
            return "create_event_node"

        elif workflow == "read_event":
            return "read_event_node"

    def create_event_node(self, state : St):
        
        try:
            parser = PydanticOutputParser(pydantic_object=CalendarOutput)
            llm = get_llm()
            formatted_prompt = CALENDER_OUTPUT_PROMPT.format(input_text=state.messages)
            response = llm.predict(formatted_prompt)
            print(response)
            state.cal_output = parser.parse(response)
            return state
        except Exception as e:
            raise(e)
            

    def schedule_event(self, state: St):

        tool = CalendarCreateEvent()
        res = tool.invoke(
            {
                "summary": state.cal_output.title,
                "start_datetime": state.cal_output.start_date.replace('T', ' '),
                "end_datetime": state.cal_output.end_date.replace('T', ' '),
                "timezone": "Asia/Kolkata",
                "location": "India",
                "description": state.cal_output.description,
                "reminders": [{"method": "popup", "minutes": 60}],
                "conference_data": True,
                "color_id": "5",
            }
        )
        state.schedule_out = res
        print(res)
        return state
        
    
    def read_event_node(self, state: St):
        calendars_info = '[{"id": "primary", "timeZone": "Asia/Kolkata"}]'

        tool = CalendarSearchEvents()

        result = tool.invoke({
            "calendars_info": calendars_info,
            "min_datetime": "2025-04-16 00:00:00",
            "max_datetime": "2025-04-30 00:00:00",
            "max_results": 5,
            "single_events": True,
            "order_by": "startTime",
            
        })
        state.read_out = ast.literal_eval(result)
        return state
        
    # def schedule_read():
    #     pass

    

    def compile_graph(self):
        builder = StateGraph(MessagesState)
        builder.add_node("router_node", self.router_node)
        # builder.add_node("select_workflow", self.select_workflow)
        builder.add_node("create_event_node", self.create_event_node)
        builder.add_node("read_event_node", self.read_event_node)
        builder.add_node("schedule_event", self.schedule_event)

        builder.add_edge(START,"router_node")
        builder.add_conditional_edges("router_node", self.select_workflow)
        # builder.add_edge("router_node", "select_workflow")
        builder.add_edge("create_event_node", "schedule_event")
        builder.add_edge("schedule_event", END)
        # builder.add_edge("read_event_node", "schedule_read")
        # builder.add_edge("schedule_read", END)
        builder.add_edge("read_event_node", END)



        return builder.compile()
    
    def __init__(self):
        self.graph= self.compile_graph()





while True :
    try:
        user_input=input("Enter:")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Bye")
            break
        s = St(messages = user_input)
        
        g = CalApp()
        g.graph.invoke(s)
        # agent.stream_graph_updates(user_input)
    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        break
