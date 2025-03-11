import os
import shutil
import nest_asyncio
import chromadb
import streamlit as st

from llama_index.llms import AzureOpenAI
from llama_index import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.vector_stores import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index import set_global_service_context
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.retrievers import QueryFusionRetriever
from llama_index.embeddings import AzureOpenAIEmbedding
from chromadb.config import Settings

nest_asyncio.apply()

# Initializing LLM
llm = AzureOpenAI(
    engine="genai_gpt",
    api_key="api_key",
    azure_endpoint="endpoint_url",
    api_version="2023-05-15",
    model="gpt-35-turbo",
    temperature=0
)

# Embeddings
embed_model = AzureOpenAIEmbedding(
    model="text-embedding-ada-002",
    deployment_name='genai_ada',
    api_key='api_key',
    azure_endpoint='endpoint_url',
    api_version="2023-05-15"
)

service_context = ServiceContext.from_defaults(llm=llm, embed_model=embed_model)
set_global_service_context(service_context)

# Initializing ChromaDB for storing embeddings
if "chroma_client" not in st.session_state:
    st.session_state.chroma_client = chromadb.PersistentClient(
        path='./chroma_db', settings=Settings(allow_reset=True)
    )

chroma_collection = st.session_state.chroma_client.get_or_create_collection('collection')

if "uploaded" not in st.session_state:
    st.session_state.uploaded = []
if "indicies" not in st.session_state:
    st.session_state.indicies = []

# Deleting Data folder on rerun
shutil.rmtree("./Data", ignore_errors=True)

# Locally saving files in a Data folder
folder_path = os.path.join(os.getcwd(), 'Data')
os.makedirs(folder_path, exist_ok=True)

st.header("Chat with the docs 💬 📚")

# Initializing the chat message history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ask me a question about your document"}]


# Creating index
def create_vector_store(file_path):
    reader = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, show_progress=True
    )
    print("Vector store created")
    st.session_state.indicies.append(index)


# Initializing retriever and query engine
def simpleFusion(indices):
    retriever = QueryFusionRetriever(
        [x.as_retriever() for x in indices],
        similarity_top_k=2,
        num_queries=4,
        use_async=True,
        verbose=True,
        llm=llm
    )
    query_engine = RetrieverQueryEngine.from_args(retriever)
    return query_engine


def main():
    if "index" not in st.session_state:
        st.session_state.index = None

    with st.sidebar:
        with st.spinner("Processing"):
            st.subheader("Your documents")
            docs = st.file_uploader("Upload your documents and click on 'Process'", accept_multiple_files=True)

            for doc in docs:
                with open(os.path.join(folder_path, doc.name), "wb") as f:
                    f.write(doc.getbuffer())

            files_in_folder = os.listdir(folder_path)
            for file in files_in_folder:
                file_path = os.path.join(folder_path, file)
                if file not in st.session_state.uploaded:
                    st.session_state.uploaded.append(file)
                    create_vector_store(file_path)

            st.session_state.query_engine = simpleFusion(st.session_state.indicies)
            st.success("Document Processed Successfully")

    # Prompt for user input and saving to chat history
    if prompt := st.chat_input("Your question"):
        st.session_state.messages.append({"role": "user", "content": prompt})

    # Displaying the prior chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # If last message is not from assistant, generate a new response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.query_engine.query(prompt)
                meta = next(iter(response.metadata))
                page_number = response.metadata[meta].get("page_label", None)
                file_name = response.metadata[meta].get("file_name", None)

                st.write(response.response)
                st.write("Page number:", page_number)
                st.write("File name:", file_name)

                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message)


if __name__ == "__main__":
    main()
