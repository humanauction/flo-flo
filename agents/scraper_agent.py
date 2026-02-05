from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from agents.tools.scraper import scrape_headlines
from agents.tools.database import save_headlines_to_db, get_db_stats
from agents.config import config
import json

