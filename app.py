import os
import json
import openai
import streamlit as st
import io
import zipfile
import difflib
from annotated_text import annotated_text as at

openai.api_key = st.secrets["OPENAI_API_KEY"]

INPUT_LIMIT = 10000

LANGUAGES = {
    "English": "EN",
    "Spanish": "ES",
    "Italian": "IT",
    "German": "DE",
    "Japanese": "JP",
}

PERSONAE = {
    "Teenager": "👶",
    "Adult Layperson": "🧑",
    "University Student in Biomedicine": "🧑‍🎓",
    "Professional Clinician": "🧑‍⚕️",
}

st.set_page_config(
    page_title="Biomedical text summarisation",
    page_icon="🧊",
)


def chunker(iterable, chunksize):
    for i, c in enumerate(iterable[::chunksize]):
        yield iterable[i * chunksize : (i + 1) * chunksize]


def markup_text(text, code):
    mapping = {
        "delete": 'style="text-decoration: line-through;',
        "insert": 'style="color: green;"',
        "replace": 'style="color: blue" id="1245"',
    }
    try:
        return f'<span {mapping[code]};">{text}</span>'
    except:
        return text


def markup(tokens, code):
    return [markup_text(token, code) for token in tokens]


def show_diff(a, b):
    """Unify operations between two compared strings
    seqm is a difflib.SequenceMatcher instance whose a & b are strings"""
    seqm = difflib.SequenceMatcher(None, a.split(" "), b.split(" "))
    output_a, output_b = [], []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == "equal":
            output_a.append(" ".join(seqm.a[a0:a1]) + " ")
            output_b.append(" ".join(seqm.b[b0:b1]) + " ")
        if opcode == "delete":
            output_a.append((" ".join(seqm.a[a0:a1]), "delete", "#f4baba"))
        if opcode == "replace":
            output_a.append((" ".join(seqm.a[a0:a1]), "replace", "#babdf4"))
            output_b.append((" ".join(seqm.b[b0:b1]), "replace", "#babdf4"))
        if opcode == "insert":
            output_b.append((" ".join(seqm.b[b0:b1]), "insert", "#baf4cc"))
    return output_a, output_b


@st.cache_data
def summarise(max_tokens, temperature, text_to_summarise, persona, language):
    if len(text_to_summarise) > INPUT_LIMIT:
        st.warning(
            "The text you selected longer than GPT's character limit. We will therefore split it up into chunks and obtain summaries for each of the chunks."
        )

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

        if finish_reason == "length":
            st.error(
                "The model's response was cut off because the result was longer than the selected `max_tokens` value. Try selecting a higher value."
            )
    return message


def prompt(max_tokens, temperature, prompt, person_type, language):
    lengths = ["extremely short", "short", "long"]
    length = lengths[int(max_tokens / 200)]

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant for text summarization.",
            },
            {
                "role": "user",
                "content": f"Create a {length} summary of the following for a {person_type},: {prompt}",
            },
            {"role": "user", "content": f"Now translate this into {language}"},
        ],
    )
    return res["choices"][0]["message"]["content"], res["choices"][0]["finish_reason"]


# init the app
papers = {}
if "paper" not in st.session_state:
    st.session_state.paper = ""

if "compare" not in st.session_state:
    st.session_state.compare = False

with open("papers.json") as f:
    papers = json.load(f)

# layout app
st.title(
    "Biomedical :blue[text summarization] and :blue[simplification] using GPT-3.5 🤖"
)
st.subheader(
    "By selecting a specific persona from the drop down menu below, you can indicate the degree to which your text should be simplified."
)

st.write("---")

column1, column2 = st.columns([0.66, 0.33])

with column1:
    input_text = st.text_area(
        "Enter a text you want to summarize:",
        height=200,
        placeholder=papers[st.session_state.paper]["Text"],
    )

with column2:
    options = {"": "Select an option"}
    for p in papers.keys():
        options[p] = papers[p]["Label"]

    paper = st.selectbox(
        "Or select one of the pre-chosen paper segments below:",
        options.keys(),
        key="paper",
        format_func=lambda x: options[x],
    )

    if paper or input_text:
        st.success("Yay! 🎉")
    else:
        st.warning("No option is selected")

st.write("---")

# options
options_column1, options_column2, options_column3 = st.columns(3)


# Slider to control the model hyperparameter
with options_column1:
    token = st.slider(
        "maximum № tokens",
        min_value=0,
        max_value=500,
        value=250,
        step=1,
        help="""GPT does not allow generation of responses of a certain length; rather, it will finish when it it has *finished an idea*. However, this value will influence the prompt: `max_tokens < 200` for *extremely short*, `200-300` for *short* and above that for *long*. However, while it has some effect on the response, it is not deterministic.""",
    )
    temp = st.slider(
        "🌡️ Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.01,
        help="Temperature indicates how reproducable GPT-3.5's results will be, with 0 meaning very reproduceable, and 1 meaning practically random.",
    )

# Selection box to select the summarization style
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

# Creating button for execute the text summarization
if st.button(
    "Summarize!",
    type="primary",
    use_container_width=True,
    disabled=bool(not (paper or input_text)),
):
    text_to_summarise = input_text if input_text else papers[paper]["Text"]
    data = {
        "text_to_summarise": text_to_summarise,
        "language": language,
        "temperature": temp,
        "max_lenght": token,
    }

    if st.session_state.compare:
        persona_columns = st.columns(len(PERSONAE))

        for pc in zip(persona_columns, PERSONAE.keys()):
            with pc[0]:
                st.subheader(pc[1])
                message = summarise(token, temp, text_to_summarise, pc[1], language)

            data[pc[1]] = message

        st.write("---")

        download_column_1, download_column_2 = st.columns(2)

        with download_column_1:
            st.download_button(
                "⬇️ Download results as JSON",
                json.dumps(data),
                file_name="results.json",
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
                        f"{key}.txt", io.BytesIO(str.encode(value)).getvalue()
                    )

            st.download_button(
                "⬇️ Download results as plain text",
                zip_buffer.getvalue(),
                file_name="results.zip",
                mime="application/zip",
                use_container_width=True,
            )

        st.write("---")
        st.header("Comparison")
        compare_column_1, compare_column_2 = st.columns(2)

        marked_a, marked_b = show_diff(data[list(PERSONAE)[0]], data[list(PERSONAE)[1]])

        with compare_column_1:
            st.subheader(list(PERSONAE)[0])
            at(marked_a)

        with compare_column_2:
            st.subheader(list(PERSONAE)[1])
            at(marked_b)

        st.write("---")
        compare_column_1, compare_column_2 = st.columns(2)

        marked_a, marked_b = show_diff(data[list(PERSONAE)[1]], data[list(PERSONAE)[2]])

        with compare_column_1:
            st.subheader(list(PERSONAE)[1])
            at(marked_a)

        with compare_column_2:
            st.subheader(list(PERSONAE)[2])
            at(marked_b)

        st.write("---")

        compare_column_1, compare_column_2 = st.columns(2)

        marked_a, marked_b = show_diff(data[list(PERSONAE)[2]], data[list(PERSONAE)[3]])

        with compare_column_1:
            st.subheader(list(PERSONAE)[2])
            at(marked_a)

        with compare_column_2:
            st.subheader(list(PERSONAE)[3])
            at(marked_b)

        st.write("---")

    else:
        message = summarise(token, temp, text_to_summarise, persona, language)
        data[persona] = message

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

if not (paper or input_text):
    st.warning("Enter text or select paper first")
