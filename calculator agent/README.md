# Its My Calculator AGENT  + ChitChat AGENT 
## Using OpenAI Agent SDK & Chainlit UI 

- If you want to calculate any complex task you can solve it through and **Calculator Agent**     
- If you want to **ChitChat** or want any general question's Answers  My agent will  also do  
- It uses multiple agents to perform calculations, respond to casual questions, and manage handoffs between agents based on the user's input.



# Features
1. Calculator Agent (Add, Subtract, Multiply, Divide)
2. Chitchat Agent (General questions or greetings)
4. Triage Agent (Decides which agent to use)
3. Context-aware responses (e.g., user's name and age)
4. Guardrail for restrited about math question (if user questioning about math my input guardrail agent tripwire triggred)
5. Chainlit UI for interactive frontend
7. Gemini Model support
8. Streaming 

# How It Works

1. User sends a message 
2. The Triage Agent analyzes the message:    
   - If it's a math query ➝ forwards to *Calculator Agent*
   - Else ➝ forwards to *Chitchat Agent*
3. The agent responds with a friendly message including the user's name.
4. Context (like user's name and age) is passed to all agents for personalization.

# Setup
Make sure you activate virtual enviornment first.
## Installation:
> ``` uv add openai-agents```

## Using uv to run the project
> ```uv run chainlit run app.py - w```

That's it Hope you like it !