import os
import chainlit as cl
import asyncio
from agents import  Agent,RunConfig,OpenAIChatCompletionsModel,set_tracing_disabled, AsyncOpenAI, Runner,RunContextWrapper,  GuardrailFunctionOutput, input_guardrail,InputGuardrailTripwireTriggered,TResponseInputItem
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel
from agents.tool import function_tool
from dataclasses import dataclass
import agentops
from dotenv import load_dotenv ,find_dotenv
load_dotenv(find_dotenv())

gemini_api_key = os.getenv("GEMINI_API_KEY")

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

Model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client,
)

run_config =RunConfig(
    model=Model,
    model_provider=external_client,
    tracing_disabled=True
)

@dataclass   # objest using dataclass for context
class UserInfo:
    name: str
    last_answer: str
    age: int
    is_math_task: bool     # guardrail for math task

# Create user info for context
userinfo = UserInfo(
    name="Urooj Fatima",
    last_answer="43",
    age=19,
    is_math_task=False
)    #  context

 # for guardrail agent
guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is question about math",
    output_type=UserInfo 
)

@function_tool
def add(wrapper: RunContextWrapper[UserInfo], a: int, b: int) -> int:
    """Add two numbers and greet user from context."""
    name = wrapper.context.name      # name for context
    print(f"Hello {name}, performing addition.")
    return a + b

@function_tool
def subtract(wrapper: RunContextWrapper[UserInfo], a: int, b: int) -> int: #context 
    """Subtract two numbers"""
    name = wrapper.context.name     # name for context
    print(f"Hello {name}, performing subtraction.")
    return a - b

@function_tool
def multiply(wrapper: RunContextWrapper[UserInfo], a: int, b: int) -> int:
    """Multiply two numbers"""
    name = wrapper.context.name    # name for context
    print(f"Hello {name}, performing multiplication.")
    return a * b

@function_tool
def divide(wrapper: RunContextWrapper[UserInfo], a: int, b: int) -> float:
    """Divide first number by second"""
    name = wrapper.context.name
    print(f"Hello {name}, performing division.")
    return a / b


# Agent 1 - Calculator Agent
calculator_agent = Agent[UserInfo](
    name=" Calculator Agent",
    instructions="""You are a helpful calculator assistant.
    When answering math questions:
    1. Always address the user by name
    2. Provide the answer clearly
    3. Format: "Hello [Name], the answer to [question] is [result]"

    Example: "Hello Urooj Fatima, the answer to 7 + 9 is 16"
    Don't mention last_answer unless asked.""",
    tools=[add, subtract, multiply, divide],
)

# Agent 2 - Chitchat Agent
chitchat_agent = Agent[UserInfo](
    name="Chitchat Agent",
    instructions="""Respond to general questions conversationally.
    Always address the user by their actual name (Urooj Fatima).
    Example: "Hello Urooj Fatima, how are you today?"
    The user is 19 years old."""
)
@input_guardrail
async def math_guardrail(ctx,agent,input_data):
  result=await Runner.run(guardrail_agent,input_data,context=ctx.context,run_config=run_config)

  final_output= result.final_output_as(UserInfo)
  return GuardrailFunctionOutput(
      output_info=result.final_output,
      tripwire_triggered= final_output.is_math_task, # not se triggred nh hoga 
    )

# Triage agent for handoffs
triage_agent = Agent[UserInfo](
    name="Triage Agent",
    instructions="""If the question is about math, handoff to the Calculator Agent.
    Otherwise, handoff to the Chitchat Agent.
    The user's name is Urooj Fatima and they are 19 years old.
    """,
    handoffs=[calculator_agent, chitchat_agent],
    input_guardrails=[math_guardrail]
)
# agentops tracing
api_key="fa56d1a5-1b65-45d4-b2b3-a8c0fe444f2f"  # agentops api key
agentops.init(api_key)

@cl.on_chat_start        #to start chainlit UI
async def handle_chat_start():
    cl.user_session.set("history",[])
    await cl.Message(content="Hello!,How can i help You?").send()
 
@cl.on_message        
async def handle_message(message: cl.Message):
    history = cl.user_session.get("history")

    msg=cl.Message(content="")
    await msg.send()

    history.append({"role": "user","content": message.content})
    result= Runner.run_streamed(
        triage_agent,
        input= history,
        run_config= run_config,
        context=userinfo,  # Pass the userinfo context
        )
    async for event in result.stream_events():
       if event.type == "raw_response_event" and isinstance(event.data,ResponseTextDeltaEvent):
        await  msg.stream_token(event.data.delta)
    

    history.append({"role":"assistant", "content":result.final_output})
    cl.user_session.set("history",history)

