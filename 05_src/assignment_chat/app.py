from assignment_chat.main import get_graph
from langchain_core.messages import HumanMessage, AIMessage
import gradio as gr
from dotenv import load_dotenv

from utils.logger import get_logger

_logs = get_logger(__name__)

graph = get_graph()

load_dotenv(".env")
load_dotenv(".secrets")


def assignment_chat(message: str, history: list[dict]) -> str:
    langchain_messages = []
    _logs.debug(f"History: {history}")
    for msg in history:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
    langchain_messages.append(HumanMessage(content=message))

    state = {"messages": langchain_messages}
    response = graph.invoke(state)
    return response["messages"][-1].content


chat = gr.ChatInterface(
    fn=assignment_chat,
    type="messages",
    title="The Night Owl Frequency",
    description="Call in to Vinyl's late-night radio show for weather vibes, artist spotlights, and album picks from the crate.",
    chatbot=gr.Chatbot(latex_delimiters=[], type="messages"),
)

if __name__ == "__main__":
    _logs.info("Starting The Night Owl Frequency chat app...")
    chat.launch()
