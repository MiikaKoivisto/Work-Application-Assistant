import streamlit as st
from rag import ask_rag


st.set_page_config(
    page_title="Microsoft 365 Assistant",
    page_icon="🤖",
    layout="wide"
)


# -----------------------------
# SESSION STATE
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_debug" not in st.session_state:
    st.session_state.show_debug = False


# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:
    st.title("🤖 AI support assistant built with:")

    st.markdown(
        """
        - Azure OpenAI
        - Azure AI Search
        - Hybrid retrieval
        - Vector embeddings
        - Streamlit
        """
    )

    st.divider()

    st.subheader("Supported products")

    st.markdown(
        """
        - Microsoft Teams
        - Outlook
        - OneDrive
        """
    )

    st.divider()

    st.session_state.show_debug = st.toggle(
        "Show RAG debug information",
        value=st.session_state.show_debug
    )

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()


# -----------------------------
# HEADER
# -----------------------------

st.title("Microsoft 365 Support Assistant")

st.caption(
    "Ask questions about Teams, Outlook and OneDrive. "
    "Answers are grounded in Microsoft Support documentation."
)


# -----------------------------
# EXAMPLE QUESTIONS
# -----------------------------

if not st.session_state.messages:

    st.subheader("Try an example")

    col1, col2, col3 = st.columns(3)

    with col1:
        example_1 = st.button(
            "🖥️ How do I share my screen in Teams?",
            use_container_width=True
        )

    with col2:
        example_2 = st.button(
            "📧 How do I set an automatic reply?",
            use_container_width=True
        )

    with col3:
        example_3 = st.button(
            "☁️ How can I recover a deleted OneDrive file?",
            use_container_width=True
        )

else:
    example_1 = False
    example_2 = False
    example_3 = False


# -----------------------------
# DISPLAY CHAT HISTORY
# -----------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message["role"] == "assistant":

            sources = message.get("sources", [])

            if sources:
                with st.expander("Sources"):

                    for source in sources:
                        st.markdown(
                            f"**{source['product']} — "
                            f"{source['title']}**"
                        )

                        st.markdown(
                            f"[Open Microsoft Support article]"
                            f"({source['url']})"
                        )

            if (
                st.session_state.show_debug
                and message.get("retrieved_chunks")
            ):

                with st.expander(
                    "RAG Debug — Retrieved Chunks"
                ):

                    for index, chunk in enumerate(
                        message["retrieved_chunks"],
                        start=1
                    ):

                        st.markdown(
                            f"### Result #{index}"
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(
                                f"**Product:** "
                                f"{chunk['product']}"
                            )

                            st.write(
                                f"**Category:** "
                                f"{chunk['category']}"
                            )

                        with col2:
                            st.write(
                                f"**Score:** "
                                f"{chunk['score']:.4f}"
                            )

                            st.write(
                                f"**Chunk ID:** "
                                f"{chunk['chunk_id']}"
                            )

                        st.write(
                            f"**Title:** {chunk['title']}"
                        )

                        st.code(
                            chunk["content"],
                            language=None
                        )

                        st.divider()


# -----------------------------
# QUESTION INPUT
# -----------------------------

question = st.chat_input(
    "Ask a Microsoft 365 support question..."
)


# Use example buttons as questions
if example_1:
    question = "How do I share my screen in Microsoft Teams?"

elif example_2:
    question = "How do I set an automatic reply in Outlook?"

elif example_3:
    question = "How can I recover a deleted file from OneDrive?"


# -----------------------------
# PROCESS QUESTION
# -----------------------------

if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching Microsoft 365 documentation..."
        ):
            result = ask_rag(question)

        st.markdown(result["answer"])

        if result["sources"]:

            with st.expander("Sources"):

                for source in result["sources"]:

                    st.markdown(
                        f"**{source['product']} — "
                        f"{source['title']}**"
                    )

                    st.markdown(
                        f"[Open Microsoft Support article]"
                        f"({source['url']})"
                    )

        if (
            st.session_state.show_debug
            and result["retrieved_chunks"]
        ):

            with st.expander(
                "RAG Debug — Retrieved Chunks"
            ):

                for index, chunk in enumerate(
                    result["retrieved_chunks"],
                    start=1
                ):

                    st.markdown(
                        f"### Result #{index}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(
                            f"**Product:** "
                            f"{chunk['product']}"
                        )

                        st.write(
                            f"**Category:** "
                            f"{chunk['category']}"
                        )

                    with col2:
                        st.write(
                            f"**Score:** "
                            f"{chunk['score']:.4f}"
                        )

                        st.write(
                            f"**Chunk ID:** "
                            f"{chunk['chunk_id']}"
                        )

                    st.write(
                        f"**Title:** {chunk['title']}"
                    )

                    st.code(
                        chunk["content"],
                        language=None
                    )

                    st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "retrieved_chunks": result["retrieved_chunks"]
    })