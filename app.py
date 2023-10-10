from helpers import *

from itertools import combinations
import openai
import streamlit as st
import json
import io
import zipfile
from annotated_text import annotated_text as at

# SETUP
openai.api_key = st.secrets["OPENAI_API_KEY"]

# SESSION VARIABLES
for variable, initialisation in SESSION_STATES.items():
    if variable not in st.session_state:
        st.session_state[variable] = initialisation

##############
# TITLE MATTER
##############
st.set_page_config(
    page_title="Biomedical text summarisation",
    page_icon="🧊",
)

st.title(
    "Biomedical :blue[text summarisation] and :blue[simplification] using GPT-3.5 🤖"
)

"---"


######################
# INPUT TEXT SELECTION
######################
def set_input():
    st.session_state.placeholder = ""
    if st.session_state.manual:
        st.session_state.text_to_summarise = st.session_state.manual

    if st.session_state.paper:
        paper = st.session_state.paper
        st.session_state.text_to_summarise = PAPERS[paper]["Text"]
        st.session_state.manual = PAPERS[paper]["Text"]

    if st.session_state.pmid:
        abstract = fetch_abstract(st.session_state.pmid)
        st.session_state.text_to_summarise = abstract
        st.session_state.manual = abstract


input_column_1, input_column_2 = st.columns([0.66, 0.33])
with input_column_1:
    st.text_area(
        "Enter a text you want to summarise:",
        height=215,
        placeholder=st.session_state.placeholder,
        key="manual",
        on_change=set_input,
    )

with input_column_2:
    options = {p: PAPERS[p]["Label"] for p in PAPERS.keys()}
    options[""] = "Select an option"

    paper = st.selectbox(
        "Or select one of the pre-chosen paper segments below:",
        options.keys(),
        key="paper",
        format_func=lambda x: options[x],
        on_change=set_input,
    )

    pmid = st.text_input("Or enter a PMID:", key="pmid", on_change=set_input)
    if pmid != "" and not pmid.isdigit():
        st.warning("Only numbers can be PMIDs")


if any([st.session_state.manual, st.session_state.pmid, st.session_state.paper]):
    st.success("Yay! 🎉")
else:
    st.warning("No option is selected")

st.write("---")

##################
# HYPER-PARAMETERS
##################
options_column1, options_column2, options_column3 = st.columns(3)

# Slider to control the model hyperparameter
with options_column1:
    token = st.slider(
        "maximum № tokens",
        min_value=200,
        max_value=1000,
        value=1000,
        step=10,
        help="""GPT does not allow generation of responses of a certain length; rather, it will finish when it it has *finished an idea*. This value will just cut off the generation to prevent incuring high costs.""",
    )
    temp = st.slider(
        "🌡️ Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.01,
        help="Temperature indicates how reproducable GPT-3.5's results will be, with 0 meaning very reproduceable, and 1 meaning practically random.",
    )

# Selection box to select the summarisation style
with options_column2:
    persona = st.selectbox(
        "How do you like to be explained?",
        PERSONAE.keys(),
        format_func=lambda x: f"{PERSONAE[x]} {x}",
        disabled=st.session_state.compare,
    )

    st.checkbox(
        "**Comparison mode**: one request for each persona will be sent to GPT and the results displayed next to each other!",
        key="compare",
    )

with options_column3:
    language = st.radio(
        "What language would you like the output to be in?",
        LANGUAGES.keys(),
        format_func=lambda x: LANGUAGES[x],
    )


###############
# SUMMARISATION
###############
@st.cache_data
def summarise(max_tokens, temperature, text_to_summarise, persona, language):
    if len(text_to_summarise) > INPUT_LIMIT:
        st.warning(
            "The text you selected longer than GPT's character limit. We will therefore if it up into chunks and obtain summaries for each of the chunks."
        )
    messages = ""
    for chunk in chunker(text_to_summarise, INPUT_LIMIT):
        with st.spinner("Request sent to GPT-3.5"):
            message, finish_reason = prompt(
                max_tokens,
                temperature,
                chunk,
                persona,
                language,
            )
            st.success(message)
            messages += message + " "

        if finish_reason == "length":
            st.error(
                "The model's response was cut off because the result was longer than the selected `max_tokens` value. Try selecting a higher value."
            )
    return messages.strip()


# The summarisation call and all the further processing
if st.button(
    "Summarise!",
    type="primary",
    use_container_width=True,
    disabled=bool(
        not any(
            [st.session_state.manual, st.session_state.pmid, st.session_state.paper]
        )
    ),
):
    data = {
        "text_to_summarise": st.session_state.text_to_summarise,
        "language": language,
        "temperature": temp,
        "max_lenght": token,
    }

    if st.session_state.compare:
        persona_columns = st.columns(len(PERSONAE))

        for persona_column, current_persona in zip(persona_columns, PERSONAE.keys()):
            with persona_column:
                st.subheader(current_persona)
                message = summarise(
                    token,
                    temp,
                    st.session_state.text_to_summarise,
                    current_persona,
                    language,
                )

                ease = readability(message, language)
                at((str(ease), "readability"))

            data[current_persona] = message
            data[f"readability_{current_persona}"] = ease

        st.write("---")

        #############
        # DOWNLOADING
        #############
        download_column_1, download_column_2 = st.columns(2)

        prefix = f'{data["text_to_summarise"][:10]}_{data["language"]}'

        with download_column_1:
            st.download_button(
                "⬇️ Download results as JSON",
                json.dumps(data),
                file_name=f"{prefix}.json",
                mime="text/json",
                use_container_width=True,
            )

        with download_column_2:
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(
                zip_buffer, "a", zipfile.ZIP_DEFLATED, False
            ) as zip_file:
                for key, value in {
                    k: v for k, v in data.items() if k in PERSONAE.keys()
                }.items():
                    zip_file.writestr(
                        f"{prefix}_{key}.txt", io.BytesIO(str.encode(value)).getvalue()
                    )

            st.download_button(
                "⬇️ Download results as plain text",
                zip_buffer.getvalue(),
                file_name=f"{prefix}.zip",
                mime="application/zip",
                use_container_width=True,
            )

        st.write("---")

        ############
        # COMPARISON
        ############
        st.header("Comparison")

        with st.columns(3)[1]:
            legend = [
                ("delete", "", "#f4baba"),
                ("replace", "", "#babdf4"),
                ("insert", "", "#baf4cc"),
            ]
            at(legend)

        for a, b in combinations(PERSONAE, 2):
            marked_a, marked_b = show_diff(data[a], data[b], language)

            compare_column_1, compare_column_2 = st.columns(2)
            with compare_column_1:
                st.subheader(a)
                at(marked_a)

            with compare_column_2:
                st.subheader(b)
                at(marked_b)

            st.write("---")

    else:
        message = summarise(
            token, temp, st.session_state.text_to_summarise, persona, language
        )
        data[persona] = message

        ease = readability(message, language)
        at((str(ease), "readability"))
        data["readability"] = ease

        download_column_1, download_column_2 = st.columns(2)

        with download_column_1:
            st.download_button(
                "⬇️ Download result as JSON",
                json.dumps(data),
                file_name="result.json",
                mime="text/json",
                use_container_width=True,
            )

        with download_column_2:
            st.download_button(
                "⬇️ Download result as plain text",
                message,
                file_name=f"result_{persona}.txt",
                mime="text/plain",
                use_container_width=True,
            )

if not any([st.session_state.manual, st.session_state.pmid, st.session_state.paper]):
    st.warning("Enter text (press enter) or PMID or select paper first")


def batch(st=st):
    progress_sofar = 0.0
    progress_bar = st.progress(progress_sofar)
    calls = len(QUESTIONAIRE_PAPERS) * len(LANGUAGES.keys()) * len(PERSONAE.keys())
    step = 1.0 / calls

    data = []
    for paper in QUESTIONAIRE_PAPERS:
        for language in LANGUAGES.keys():
            for persona in PERSONAE.keys():
                message, finish_reason = prompt(
                    token, temp, PAPERS[paper], persona, language
                )

                data.append(
                    {
                        "language": language,
                        "paper": paper,
                        "persona": persona,
                        "summary": message if message else finish_reason,
                        "readability": readability(message, language),
                    }
                )

                progress_sofar += step
                progress_bar.progress(progress_sofar if progress_sofar < 1.0 else 1.0)

    st.download_button(
        "⬇️ Download result as JSON",
        json.dumps(data),
        file_name="batch.json",
        mime="text/json",
        use_container_width=True,
    )

    st.download_button(
        "⬇️ Download result as CSV",
        data_to_csv(data),
        file_name="batch.csv",
        mime="text/plain",
        use_container_width=True,
    )


"---"
batch_expander = st.expander("Batch summarisation", expanded=False)
batch_expander.caption(
    f"This will query all languages for all personae for three specific papers ({', '.join(QUESTIONAIRE_PAPERS)})."
)

batch_expander.checkbox(
    "The following action runs quite a lot of queries to ChatGPT and thus incurs somewhat of a cost. Please use this feature sparingly (if not previously cached)! 🙏",
    key="batch",
)

if batch_expander.button(
    "Generate!",
    type="secondary",
    use_container_width=True,
    disabled=not st.session_state.batch,
):
    batch(batch_expander)
