import os
import hmac
import streamlit as st
from dotenv import load_dotenv

from company_matcher import match_company
from rag import ask_rag

load_dotenv()

st.set_page_config(
    page_title="AI Work Application Assistant",
    page_icon="🤖",
    layout="wide"
)


def get_setting(name):
    try:
        return st.secrets.get(name, os.getenv(name, ""))
    except Exception:
        return os.getenv(name, "")


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



# -----------------------------
# SESSION STATE
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "language" not in st.session_state:
    st.session_state.language = "en"

if "recruiter_name" not in st.session_state:
    st.session_state.recruiter_name = None

if "company_name" not in st.session_state:
    st.session_state.company_name = None

if "company_id" not in st.session_state:
    st.session_state.company_id = None

if "authenticated_company" not in st.session_state:
    st.session_state.authenticated_company = False



TRANSLATIONS = {
    "en": {
        "language": "Language",
        "welcome": "👋 Welcome",
        "app_title": "AI Work Application Assistant",
        "intro": (
            "This assistant provides additional information about my professional "
            "experience, technical skills, projects, and suitability for the "
            "position I have applied for.\\n\\n"
            "To get started, please enter your details below."
        ),
        "first_name": "Your first name",
        "first_name_placeholder": "Enter your first name",
        "company_name": "Company name",
        "company_placeholder": "Enter your company name",
        "access_code": "Access code",
        "access_code_placeholder": "Enter access code",
        "continue": "Continue",
        "missing_name": "Please enter your first name.",
        "missing_company": "Please enter your company.",
        "missing_code": "Please enter the access code.",
        "code_not_configured": "The access code has not been configured for this app.",
        "incorrect_code": "Incorrect access code.",
        "unknown_company": (
            "Sorry, this assistant doesn't currently contain information "
            "about an open position at **{company}**. "
            "Please check the company name and try again."
        ),
        "sidebar_title": "🤖 Application Assistant",
        "recruiter": "Recruiter",
        "company": "Company",
        "technology": "Technology",
        "clear_conversation": "Clear conversation",
        "header_welcome": (
            "Welcome, {name}. Ask about Miika's experience, skills, projects, "
            "or suitability for the position."
        ),
        "try_example": "Try an example",
        "example_company": "🏢 Tell me about the company",
        "example_position": "💼 Tell me about the position",
        "example_fit": "🎯 Tell me how Miika fits the position",
        "example_company_q": "Tell me about the company.",
        "example_position_q": "Tell me about the position.",
        "example_fit_q": "Tell me how Miika fits the position.",
        "start_hint": "Choose an example above or ask your own question below to start the conversation.",
        "chat_placeholder": "Ask about Miika's experience, skills, projects, or suitability...",
        "evidence": "Evidence",
        "sources": "Sources",
        "technical_details": "Technical details — RAG retrieval",
        "original_question": "Original question",
        "rewritten_query": "Rewritten retrieval query",
        "retrieved_chunks": "Retrieved chunks",
        "document_type": "Document type",
        "company_id": "Company ID",
        "source": "Source",
        "open_source": "Open source",
        "score": "Score",
        "chunk_id": "Chunk ID",
        "title": "Title",
        "result": "Result",
        "citation": "Citation",
        "not_available": "Not available.",
        "searching": "Searching the application knowledge base...",
        "greeting": (
            "Hello {name}! 👋\\n\\n"
            "I'm Miika's AI Work Application Assistant. "
            "I can help you learn more about:\\n\\n"
            "- Miika's professional experience and technical skills\\n"
            "- The position he has applied for\\n"
            "- How his experience matches the position\\n"
            "- His AI, automation and software development projects\\n"
            "- Relevant technologies, certifications and areas of expertise\\n\\n"
            "You can choose one of the example questions above or ask me "
            "anything related to Miika's application."
        ),
    },
    "fi": {
        "language": "Kieli",
        "welcome": "👋 Tervetuloa",
        "app_title": "AI-työhakemusavustaja",
        "intro": (
            "Tämä avustaja tarjoaa lisätietoa ammatillisesta kokemuksestani, "
            "teknisestä osaamisestani, projekteistani ja soveltuvuudestani "
            "hakemaani tehtävään.\\n\\n"
            "Aloita syöttämällä tietosi alle."
        ),
        "first_name": "Etunimesi",
        "first_name_placeholder": "Syötä etunimesi",
        "company_name": "Yrityksen nimi",
        "company_placeholder": "Syötä yrityksen nimi",
        "access_code": "Pääsykoodi",
        "access_code_placeholder": "Syötä pääsykoodi",
        "continue": "Jatka",
        "missing_name": "Syötä etunimesi.",
        "missing_company": "Syötä yrityksen nimi.",
        "missing_code": "Syötä pääsykoodi.",
        "code_not_configured": "Pääsykoodia ei ole määritetty tälle sovellukselle.",
        "incorrect_code": "Virheellinen pääsykoodi.",
        "unknown_company": (
            "Valitettavasti avustaja ei tällä hetkellä sisällä tietoa "
            "avoimesta tehtävästä yrityksessä **{company}**. "
            "Tarkista yrityksen nimi ja yritä uudelleen."
        ),
        "sidebar_title": "🤖 Työhakemusavustaja",
        "recruiter": "Rekrytoija",
        "company": "Yritys",
        "technology": "Teknologiat",
        "clear_conversation": "Tyhjennä keskustelu",
        "header_welcome": (
            "Tervetuloa, {name}. Voit kysyä Miikan kokemuksesta, taidoista, "
            "projekteista tai soveltuvuudesta tehtävään."
        ),
        "try_example": "Kokeile esimerkkikysymystä",
        "example_company": "🏢 Kerro yrityksestä",
        "example_position": "💼 Kerro tehtävästä",
        "example_fit": "🎯 Miten Miika sopii tehtävään?",
        "example_company_q": "Kerro yrityksestä.",
        "example_position_q": "Kerro tehtävästä.",
        "example_fit_q": "Kerro, miten Miika sopii tehtävään.",
        "start_hint": "Valitse esimerkkikysymys yllä tai kirjoita oma kysymyksesi alle.",
        "chat_placeholder": "Kysy Miikan kokemuksesta, taidoista, projekteista tai soveltuvuudesta...",
        "evidence": "Todisteet",
        "sources": "Lähteet",
        "technical_details": "Tekniset tiedot — RAG-haku",
        "original_question": "Alkuperäinen kysymys",
        "rewritten_query": "Uudelleenkirjoitettu hakukysely",
        "retrieved_chunks": "Haetut tekstikatkelmat",
        "document_type": "Dokumenttityyppi",
        "company_id": "Yritystunnus",
        "source": "Lähde",
        "open_source": "Avaa lähde",
        "score": "Pisteet",
        "chunk_id": "Katkelman ID",
        "title": "Otsikko",
        "result": "Tulos",
        "citation": "Viite",
        "not_available": "Ei saatavilla.",
        "searching": "Haetaan tietoa hakemuksen tietopohjasta...",
        "greeting": (
            "Hei {name}! 👋\\n\\n"
            "Olen Miikan AI-työhakemusavustaja. Voin kertoa esimerkiksi:\\n\\n"
            "- Miikan ammatillisesta kokemuksesta ja teknisestä osaamisesta\\n"
            "- Tehtävästä, johon hän on hakenut\\n"
            "- Miten hänen kokemuksensa vastaa tehtävää\\n"
            "- Hänen AI-, automaatio- ja ohjelmistokehitysprojekteistaan\\n"
            "- Tehtävän kannalta olennaisista teknologioista ja osaamisalueista\\n\\n"
            "Voit valita esimerkkikysymyksen yllä tai kysyä vapaasti Miikan hakemukseen liittyen."
        ),
    },
}


def t(key, **kwargs):
    value = TRANSLATIONS[st.session_state.language][key]
    return value.format(**kwargs) if kwargs else value



# -----------------------------
# ONBOARDING SCREEN
# -----------------------------

if not st.session_state.authenticated_company:

    language_choice = st.radio(
        t("language"),
        options=["EN", "FI"],
        horizontal=True,
        index=0 if st.session_state.language == "en" else 1,
        key="language_selector_onboarding",
    )

    selected_language = language_choice.lower()
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()

    st.title(t("welcome"))
    st.subheader(t("app_title"))

    st.markdown(t("intro"))
    st.divider()

    recruiter_name = st.text_input(
        t("first_name"),
        placeholder=t("first_name_placeholder"),
    )

    company_name = st.text_input(
        t("company_name"),
        placeholder=t("company_placeholder"),
    )

    access_code = st.text_input(
        t("access_code"),
        type="password",
        placeholder=t("access_code_placeholder"),
    )

    if st.button(
        t("continue"),
        type="primary",
        use_container_width=True,
    ):
        recruiter_name = recruiter_name.strip()
        company_name = company_name.strip()
        entered_code = str(access_code).strip()
        expected_code = str(get_setting("APP_ACCESS_CODE")).strip()

        if not recruiter_name:
            st.warning(t("missing_name"))

        elif not company_name:
            st.warning(t("missing_company"))

        elif not entered_code:
            st.warning(t("missing_code"))

        elif not expected_code:
            st.error(t("code_not_configured"))

        elif not hmac.compare_digest(entered_code, expected_code):
            st.error(t("incorrect_code"))

        else:
            company_id = match_company(company_name)

            if company_id is None:
                st.error(t("unknown_company", company=company_name))
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

    st.title(t("sidebar_title"))

    sidebar_language = st.radio(
        t("language"),
        options=["EN", "FI"],
        horizontal=True,
        index=0 if st.session_state.language == "en" else 1,
        key="language_selector_sidebar",
    )

    selected_sidebar_language = sidebar_language.lower()
    if selected_sidebar_language != st.session_state.language:
        st.session_state.language = selected_sidebar_language
        st.rerun()

    st.markdown(
        f"""
        **{t("recruiter")}:**  
        {st.session_state.recruiter_name}

        **{t("company")}:**  
        {st.session_state.company_name}
        """
    )

    st.divider()

    st.subheader(t("technology"))

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
        t("clear_conversation"),
        use_container_width=True
    ):
        st.session_state.messages = []
        st.rerun()


# -----------------------------
# HEADER
# -----------------------------

st.title(t("app_title"))

st.caption(
    t("header_welcome", name=st.session_state.recruiter_name)
)

st.divider()


# -----------------------------
# EXAMPLE QUESTIONS
# -----------------------------

example_1 = False
example_2 = False
example_3 = False

if not st.session_state.messages:

    st.subheader(t("try_example"))

    col1, col2, col3 = st.columns(3)

    with col1:
        example_1 = st.button(
            t("example_company"),
            use_container_width=True,
            key="example_company"
        )

    with col2:
        example_2 = st.button(
            t("example_position"),
            use_container_width=True,
            key="example_position"
        )

    with col3:
        example_3 = st.button(
            t("example_fit"),
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
            t("start_hint")
        )

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message["role"] == "assistant":

                citations = message.get("citations", [])

                if citations:
                    with st.expander(t("evidence")):
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
                    with st.expander(t("sources")):
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
                        t("technical_details")
                    ):
                        st.markdown(f"**{t('original_question')}**")
                        st.code(
                            message.get(
                                "original_question",
                                "Not available."
                            ),
                            language=None
                        )

                        st.markdown(f"**{t('rewritten_query')}**")
                        st.code(
                            message.get(
                                "retrieval_query",
                                "Not available."
                            ),
                            language=None
                        )

                        st.markdown(f"**{t('retrieved_chunks')}**")

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
    t("chat_placeholder")
)


# -----------------------------
# EXAMPLE QUESTION MAPPING
# -----------------------------

if example_1:
    question = t("example_company_q")

elif example_2:
    question = t("example_position_q")

elif example_3:
    question = t("example_fit_q")


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

            answer = t("greeting", name=st.session_state.recruiter_name)

            result = {
                "answer": answer,
                "sources": [],
                "citations": [],
                "retrieved_chunks": [],
                "retrieval_query": question
            }

        else:
            with st.spinner(
                t("searching")
            ):
                result = ask_rag(
                    question,
                    company_id=st.session_state.company_id,
                    history=st.session_state.messages[:-1],
                    language=st.session_state.language,
                )

        st.markdown(result["answer"])

        citations = result.get("citations", [])

        if citations:
            with st.expander(t("evidence")):
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
            with st.expander(t("sources")):
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
                t("technical_details")
            ):
                st.markdown(f"**{t('original_question')}**")
                st.code(
                    question,
                    language=None
                )

                st.markdown(f"**{t('rewritten_query')}**")
                st.code(
                    result.get(
                        "retrieval_query",
                        question
                    ),
                    language=None
                )

                st.markdown(f"**{t('retrieved_chunks')}**")

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
