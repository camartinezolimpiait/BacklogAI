
import os

from sqlalchemy import text
from typer import prompt
from app.api.apiFast_tools import (
    GetOrdersDatasetTool,
    GetOrderTool,
    QueryRAGTool,
    RegisterReturnOrderTool,
    VerifyEligibilityOrderTool
)
from langchain_openai import AzureChatOpenAI
from app.config import settings
from langchain.agents import initialize_agent, AgentType
from langgraph.graph import StateGraph, END

from typing import TypedDict, List, Any

# Minimal state schema for LangGraph agent
class AgentState(TypedDict):
    input: str
    intermediate_steps: List[Any]

class LangAgent:

    def __init__(self):
        """
        Initializes the class by creating instances of order-related tools and loading all application settings.
        Attributes:
            get_order_tool (GetOrderTool): Tool for retrieving order information.
            register_return_order_tool (RegisterReturnOrderTool): Tool for registering return orders.
            verify_eligibility_order_tool (VerifyEligibilityOrderTool): Tool for verifying order eligibility.
            allSettings (dict): Dictionary containing all application settings.
        """
               
        self.get_order_tool = GetOrderTool()
        self.register_return_order_tool = RegisterReturnOrderTool()
        self.verify_eligibility_order_tool = VerifyEligibilityOrderTool()
        self.allSettings = settings.get_settings()
        
    
    def load_agent(self): 
        """
        Initializes and configures a language model agent with predefined tools and settings.
        This method sets up an agent using the AzureChatOpenAI language model and a list of custom tools
        for handling order-related tasks. The agent is configured with a specific prompt, verbosity, 
        error handling, and iteration limits.
        Returns:
            An initialized agent node ready to process structured chat interactions using the specified tools and model.
        """
        Tools = [
            self.get_order_tool,
            self.register_return_order_tool,
            self.verify_eligibility_order_tool
        ]

        llm_model = AzureChatOpenAI(
            azure_deployment=self.allSettings.azure_openai_deployment_name,
            temperature=0,
            azure_endpoint=self.allSettings.azure_openai_endpoint,
            api_key=self.allSettings.azure_openai_key,
            api_version=self.allSettings.azure_openai_api_version
        )

        # Configurar el agente con las herramientas
        agent_node = initialize_agent(
            tools=Tools,
            llm=llm_model,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,   
            max_iterations=5,   
            agent_kwargs={
                "prefix": self.get_prompt("PROMPTBASE")
            },
        )
        
        return agent_node

    def get_prompt(self, name):
        """
        Retrieves the text of a prompt from the 'app/rag/prompts.txt' file given its name.

        Args:
            name (str): The name of the prompt to retrieve.

        Returns:
            str: The text content of the specified prompt.

        Raises:
            ValueError: If the prompt with the given name is not found in 'prompts.txt'.

        Notes:
            The prompts in 'prompts.txt' should be defined in the following format:
                prompt_name = ""
                prompt text = ""
               
        """
       
        import re
        ruta = os.path.join(os.path.dirname(__file__), "..", "rag", "prompts.txt")
        ruta = os.path.abspath(ruta)
        with open(ruta, encoding="utf-8") as f:
            contenido = f.read()
        patron = rf'{name}\s*=\s*"""(.*?)"""'
        match = re.search(patron, contenido, re.DOTALL)
        if match:
            return match.group(1).strip()
        raise ValueError(f"Prompt '{name}' no encontrado en prompts.txt")
    
    


 
