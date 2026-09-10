import os
import hmac
import streamlit as st
from dotenv import load_dotenv

from company_matcher import match_company
from rag import ask_rag

load_dotenv()


def get_setting(name):
    try:
        return st.secrets.get(name, os.getenv(name, ""))
    except Exception:
        return os.getenv(name, "")


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def check_access_code():
    entered_code = st.session_state.get("access_code", "")
    expected_code = get_setting("APP_ACCESS_CODE")

    if expected_code and hmac.compare_digest(
        entered_code,
        expected_code
    ):
        st.session_state.authenticated = True
        st.session_state.pop("access_code", None)
    else:
        st.error("Incorrect access code.")


if not st.session_state.authenticated:
    st.title("AI Work Application Assistant")

    st.write(
        "This assistant provides additional information about my "
        "experience, skills, projects, and suitability for the position."
    )

    st.text_input(
        "Access code",
        type="password",
        key="access_code",
        placeholder="Enter access code"
    )

    st.button(
        "Continue",
        on_click=check_access_code,
        type="primary"
    )

    st.stop()


def is_greeting(message):
    greeting_words = {
        "hi",
        "hello",
        "hey",
        "hiya",
        "greetings",
        "good morning",
        "good afternoon",
        "good evening"
    }

    normalized = message.strip().lower().rstrip("!.,?")
    return normalized in greeting_words


st.set_page_config(
    page_title="AI Work Application Assistant",
    page_icon="🤖",
    layout="wide"
)


# -----------------------------
# SESSION STATE
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "recruiter_name" not in st.session_state:
    st.session_state.recruiter_name = None

if "company_name" not in st.session_state:
    st.session_state.company_name = None

if "company_id" not in st.session_state:
    st.session_state.company_id = None

if "authenticated_company" not in st.session_state:
    st.session_state.authenticated_company = False


# -----------------------------
# ONBOARDING SCREEN
# -----------------------------

if not st.session_state.authenticated_company:

    st.title("👋 Welcome")

    st.subheader("AI Work Application Assistant")

    st.markdown(
        """
        This assistant provides additional information about my professional
        experience, technical skills, projects, and suitability for the
        position I have applied for.

        To get started, please introduce yourself below.
        """
    )

    st.divider()

    recruiter_name = st.text_input(
        "Your first name"
    )

    company_name = st.text_input(
        "Company"
    )

    if st.button(
        "Continue",
        type="primary",
        use_container_width=True
    ):
        recruiter_name = recruiter_name.strip()
        company_name = company_name.strip()

        if not recruiter_name:
            st.warning("Please enter your first name.")

        elif not company_name:
            st.warning("Please enter your company.")

        else:
            company_id = match_company(company_name)

        if company_id is None:
                st.error(
                f"Sorry, this assistant doesn't currently contain information "
                f"about an open position at **{company_name}**. "
                f"Please check the company name and try again."
    )
        else:
                st.session_state.recruiter_name = recruiter_name
                st.session_state.company_name = company_name
                st.session_state.company_id = company_id
                st.session_state.authenticated_company = True

                st.rerun()

    st.stop()


# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:

    st.title("🤖 Application Assistant")

    st.markdown(
        f"""
        **Recruiter:**  
        {st.session_state.recruiter_name}

        **Company:**  
        {st.session_state.company_name}
        """
    )

    st.divider()

    st.subheader("Technology")

    st.markdown(
        """
        - Azure OpenAI
        - Azure AI Search
        - Hybrid retrieval
        - Vector embeddings
        - Metadata filtering
        - Streamlit
        """
    )

    st.divider()

    if st.button(
        "Clear conversation",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.rerun()


# -----------------------------
# HEADER
# -----------------------------

st.title("AI Work Application Assistant")

st.caption(
    f"Welcome, {st.session_state.recruiter_name}. "
    "Ask about Miika's experience, skills, projects, "
    "or suitability for the position."
)

st.divider()


# -----------------------------
# EXAMPLE QUESTIONS
# -----------------------------

example_1 = False
example_2 = False
example_3 = False

if not st.session_state.messages:

    st.subheader("Try an example")

    col1, col2, col3 = st.columns(3)

    with col1:
        example_1 = st.button(
            "🏢 Tell me about the company",
            use_container_width=True,
            key="example_company"
        )

    with col2:
        example_2 = st.button(
            "💼 Tell me about the position",
            use_container_width=True,
            key="example_position"
        )

    with col3:
        example_3 = st.button(
            "🎯 Tell me how Miika fits the position",
            use_container_width=True,
            key="example_fit"
        )


# -----------------------------
# DISPLAY CHAT HISTORY
# -----------------------------

chat_container = st.container(
    height=600,
    border=False
)

with chat_container:

    if not st.session_state.messages:
        st.caption(
            "Choose an example above or ask your own question below to start the conversation."
        )

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message["role"] == "assistant":

                citations = message.get("citations", [])

                if citations:
                    with st.expander("Evidence"):
                        for citation in citations:
                            st.markdown(
                                f"### [{citation['citation_number']}] "
                                f"{citation['title']}"
                            )

                            st.write(
                                f"**Document type:** "
                                f"{citation['document_type']}"
                            )

                            st.write(
                                f"**Company ID:** "
                                f"{citation['company_id']}"
                            )

                            if citation.get("source"):
                                st.caption(
                                    f"Source: {citation['source']}"
                                )

                            if citation.get("url"):
                                st.markdown(
                                    f"[Open source]({citation['url']})"
                                )

                            st.code(
                                citation["content"],
                                language=None
                            )

                            st.divider()

                sources = message.get("sources", [])

                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.markdown(
                                f"**{source['document_type'].replace('_', ' ').title()} — "
                                f"{source['title']}**"
                            )

                            if source.get("source"):
                                st.caption(
                                    f"Source: {source['source']}"
                                )

                            if source.get("url"):
                                st.markdown(
                                    f"[Open source]({source['url']})"
                                )

                retrieved_chunks = message.get(
                    "retrieved_chunks",
                    []
                )

                if retrieved_chunks:
                    with st.expander(
                        "Technical details — RAG retrieval"
                    ):
                        st.markdown("**Original question**")
                        st.code(
                            message.get(
                                "original_question",
                                "Not available."
                            ),
                            language=None
                        )

                        st.markdown("**Rewritten retrieval query**")
                        st.code(
                            message.get(
                                "retrieval_query",
                                "Not available."
                            ),
                            language=None
                        )

                        st.markdown("**Retrieved chunks**")

                        for index, chunk in enumerate(
                            retrieved_chunks,
                            start=1
                        ):
                            citation_number = chunk.get(
                                "citation_number",
                                index
                            )

                            st.markdown(
                                f"### Result #{index} — Citation [{citation_number}]"
                            )

                            col1, col2 = st.columns(2)

                            with col1:
                                st.write(
                                    f"**Company ID:** "
                                    f"{chunk['company_id']}"
                                )

                                st.write(
                                    f"**Document type:** "
                                    f"{chunk['document_type']}"
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
                                f"**Title:** "
                                f"{chunk['title']}"
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
    "Ask about Miika's experience, skills, projects, or suitability..."
)


# -----------------------------
# EXAMPLE QUESTION MAPPING
# -----------------------------

if example_1:
    question = "Tell me about the company."

elif example_2:
    question = "Tell me about the position."

elif example_3:
    question = "Tell me how Miika fits the position."


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

        if is_greeting(question):

            answer = (
                f"Hello {st.session_state.recruiter_name}! 👋\n\n"
                "I'm Miika's AI Work Application Assistant. "
                "I can help you learn more about:\n\n"
                "- Miika's professional experience and technical skills\n"
                "- The position he has applied for\n"
                "- How his experience matches the position\n"
                "- His AI, automation and software development projects\n"
                "- Relevant technologies, certifications and areas of expertise\n\n"
                "You can choose one of the example questions above or ask me "
                "anything related to Miika's application."
            )

            result = {
                "answer": answer,
                "sources": [],
                "citations": [],
                "retrieved_chunks": [],
                "retrieval_query": question
            }

        else:
            with st.spinner(
                "Searching the application knowledge base..."
            ):
                result = ask_rag(
                    question,
                    company_id=st.session_state.company_id,
                    history=st.session_state.messages[:-1]
                )

        st.markdown(result["answer"])

        citations = result.get("citations", [])

        if citations:
            with st.expander("Evidence"):
                for citation in citations:
                    st.markdown(
                        f"### [{citation['citation_number']}] "
                        f"{citation['title']}"
                    )

                    st.write(
                        f"**Document type:** "
                        f"{citation['document_type']}"
                    )

                    st.write(
                        f"**Company ID:** "
                        f"{citation['company_id']}"
                    )

                    if citation.get("source"):
                        st.caption(
                            f"Source: {citation['source']}"
                        )

                    if citation.get("url"):
                        st.markdown(
                            f"[Open source]({citation['url']})"
                        )

                    st.code(
                        citation["content"],
                        language=None
                    )

                    st.divider()

        if result["sources"]:
            with st.expander("Sources"):
                for source in result["sources"]:
                    st.markdown(
                        f"**{source['document_type'].replace('_', ' ').title()} — "
                        f"{source['title']}**"
                    )

                    if source.get("source"):
                        st.caption(
                            f"Source: {source['source']}"
                        )

                    if source.get("url"):
                        st.markdown(
                            f"[Open source]({source['url']})"
                        )

        if result["retrieved_chunks"]:
            with st.expander(
                "Technical details — RAG retrieval"
            ):
                st.markdown("**Original question**")
                st.code(
                    question,
                    language=None
                )

                st.markdown("**Rewritten retrieval query**")
                st.code(
                    result.get(
                        "retrieval_query",
                        question
                    ),
                    language=None
                )

                st.markdown("**Retrieved chunks**")

                for index, chunk in enumerate(
                    result["retrieved_chunks"],
                    start=1
                ):
                    citation_number = chunk.get(
                        "citation_number",
                        index
                    )

                    st.markdown(
                        f"### Result #{index} — Citation [{citation_number}]"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(
                            f"**Company ID:** "
                            f"{chunk['company_id']}"
                        )

                        st.write(
                            f"**Document type:** "
                            f"{chunk['document_type']}"
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
                        f"**Title:** "
                        f"{chunk['title']}"
                    )

                    st.code(
                        chunk["content"],
                        language=None
                    )

                    st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "original_question": question,
        "retrieval_query": result.get(
            "retrieval_query",
            question
        ),
        "sources": result["sources"],
        "citations": result.get("citations", []),
        "retrieved_chunks": result["retrieved_chunks"]
    })
