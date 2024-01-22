from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
import os
import json
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.prompts import PromptTemplate
from langchain.schema import AgentAction, AgentFinish, agent
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.tools.render import render_text_description
from langchain_community.chat_models import ChatOpenAI
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.tools import Tool
from typing import List
from callbacks import AgentCallbackHandler
from astrapy.db import AstraDB, AstraDBCollection
from langchain.tools.retriever import create_retriever_tool
import re

load_dotenv()

CUSTOMER_ID = 'f08a6894-1863-491d-8116-3945fb915597'

astra_db = AstraDB(
    api_endpoint=os.environ.get("ASTRA_DB_VECTOR_API_ENDPOINT"),
    token=os.environ.get("ASTRA_DB_VECTOR_TOKEN"),
)

airline_tickets_collection = AstraDBCollection(
    "airlines_tickets",  astra_db=astra_db)

# For the connection with CQL Tables, we will leverage the AstraDB REST API.
def astra_rest(table, pk, params={}, filters=[], method='GET', data={}):
    headers = {'Accept': 'application/json',
               'X-Cassandra-Token': f'{os.environ.get("ASTRA_TOKEN")}'}
    url = f'{os.environ.get("ASTRA_API_ENDPOINT")}/api/rest/v2/keyspaces/{os.environ.get("ASTRA_KEYSPACE")}/{table}/{"/".join(pk)}?{urlencode(params)}'

    res = requests.request(
        method, url=url, headers=headers, data=json.dumps(data))

    if int(res.status_code) >= 400:
        return res.text

    try:
        res_data = res.json()
        return res_data
    except ValueError:
        res_data = res.status_code
        return res_data


# TOOL Definition
    
class CustomerFeatureInput(BaseModel):
    customer_id: str = Field(
        description="The UUID that represents the customer")
    feature: str = Field(
        description="The information about the customer: date_of_birth, gender, has_TSA, meal_preference, miles, miles category, nationality ")


@tool(args_schema=CustomerFeatureInput)
def get_customer_feature(customer_id: str, feature: str) -> str:
    """Given a customer_id and a feature, returns and information about the customer"""
    return _get_customer_feature(customer_id, feature)


def _get_customer_feature(customer_id: str, feature: str) -> str:
    print(f"get_customer_feature: {feature}")
    feature = astra_rest('airlinecustomerfeaturestore',
                         [customer_id, feature],
                         {'page-size': 1,
                          'fields': 'feature,value'})
    if len(feature['data']) == 1:
        return feature['data'][0]['value']
    else:
        return 'Not found'


# TOOL Definition =  Scheduled Flights

class ScheduledFlightsInput(BaseModel):
    customer_id: str = Field(
        description="The UUID that represents the customer")
    conditions: dict = Field(
        description="The conditions for the fields: arrivalairport, departureairport, departuredatetime ")


@tool(args_schema=ScheduledFlightsInput)
def get_scheduled_flights(customer_id: str, conditions: dict) -> [str]:
    """Returns information about scheduled flights considering conditions for arrivalAirport, departureAirport, departureDateTime. Consider Airport codes and Dates in ISO format """
    filter = {"customerId": customer_id, **conditions}
    
    flights = airline_tickets_collection.find(filter=filter, projection={
                                              "departureAirport": 1, "arrivalAirport": 1, "departureDateTime": 1})
    return flights['data']['documents']

class ScheduledFlightDetailInput(BaseModel):
    ticket_id: str = Field(
        description="The UUID for a specific flight ticket")


# TOOL Definition =  Scheduled Flight  Detail

@tool(args_schema=ScheduledFlightDetailInput)
def get_flight_detail(ticket_id: str) -> [str]:
    """Returns information about on flight"""
    filter = {"_id": ticket_id}
    flights = airline_tickets_collection.find_one(filter=filter)
    return flights['data']['document']

# Auxiliary functions

def find_tool_by_name(tools: List[Tool], tool_name: str) -> Tool:
    for tool in tools:
        if tool.name == tool_name:
            return tool
    raise ValueError(f"Tool wtih name {tool_name} not found")

def remove_json_comments(json_with_comments):
    """Sometimes, the JSON returned by the LLM contains comments, then it is needed to remove it"""
    comment_pattern = r'/\*.*?\*/|//.*?$'
    json_without_comments = re.sub(comment_pattern, '', json_with_comments, flags=re.MULTILINE)
    return json_without_comments


# The Agent
class TheFlightAssistant:
    agent = None
    tools = [get_customer_feature, get_scheduled_flights, get_flight_detail]
    def __init__(self, customer_id, retriever = None, memory = None):
        retriever_tool = create_retriever_tool(
            retriever,
            "search_qa",
            "Knowledge base for general questions.",
        )
    
        self.tools.append(retriever_tool)
        # https://smith.langchain.com/hub/hwchase17/react
        template = """
        Answer the following questions as best you can. You have access to the following tools:

        {tools}

        You are talking to {customer_name}.
        Customer ID: {customer_id}
        Answer in {language}.

        {chat_history}
        
        Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action in JSON format without comments.
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        Begin!

        Question: {input}
        Thought: {agent_scratchpad}
        """

        prompt = PromptTemplate.from_template(template=template).partial(
            tools=render_text_description(self.tools),
            tool_names=', '.join([t.name for t in self.tools]),
            customer_id=customer_id,
            customer_name=_get_customer_feature(customer_id, 'name'),
            language=_get_customer_feature(customer_id, 'language')
        )

        llm = ChatOpenAI(temperature=0,
                        model_name='gpt-4-1106-preview',
                        stop=["\nObservation"],
                        memory=memory,
                        callbacks=[AgentCallbackHandler()])

    
        self.agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_log_to_str(x["agent_scratchpad"]),
                # "chat_history": memory.
            }
            | prompt
            | llm
            | ReActSingleInputOutputParser()
        )
        print("THE FLIGHT ASSISTANT - Initialized")

    def invoke(self, question):
        agent_step = ""
        intermediate_steps = []
        while not isinstance(agent_step, AgentFinish):
            agent_step: [AgentFinish, AgentAction] = self.agent.invoke(
                {"input": question,
                "agent_scratchpad": intermediate_steps})

            print(agent_step)

            if isinstance(agent_step, AgentAction):
                tool_name = agent_step.tool
                tool_to_use = find_tool_by_name(self.tools, tool_name)
                tool_input = agent_step.tool_input
                print("Tool input: ", tool_input)
                observation = tool_to_use.func(**json.loads(remove_json_comments(tool_input)))
                print(f"{observation=}")
                intermediate_steps.append((agent_step, str(observation)))

        if isinstance(agent_step, AgentFinish):
            print(f"Finish: {agent_step.return_values}")

        return agent_step.return_values['output']
