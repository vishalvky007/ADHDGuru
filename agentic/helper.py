from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from prompts import ROUTER_PROMPT
from states import RouterResponse

load_dotenv()
API = os.environ['GROQ_API']

def get_llm():
    llm = ChatGroq(api_key=API, model="gemma2-9b-it")
    return llm
    
def get_router_chain():
    model = get_llm().with_structured_output(RouterResponse)

    prompt = ChatPromptTemplate.from_messages(
        [("system", ROUTER_PROMPT), MessagesPlaceholder(variable_name="messages")]
    )

    return prompt | model