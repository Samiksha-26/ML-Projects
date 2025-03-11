from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

class ClassifierAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="model",
            temperature=0,
            api_key="api_key",
            base_url="url"
        )

    def categorize_email(self, subject, content):
        """Uses LLM to classify emails into Urgent, Work-Related, or General."""
        prompt = f"""
        Categorize the following email into one of these:
        - Urgent: Requires immediate attention (meetings, deadlines, client requests).
        - Work-Related: Important but not urgent (task updates, reports, discussions).
        - General: Non-essential (newsletters, social notifications, promotional emails).

        Email Subject: {subject}
        Email Content: {content}
        Category: 
        """
        response = self.llm([HumanMessage(content=prompt)])
        return response.content.strip()
