import os
import json
import openai
import streamlit as st

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


def chunker(iterable, chunksize):
    for i, c in enumerate(iterable[::chunksize]):
        yield iterable[i * chunksize : (i + 1) * chunksize]


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

    if st.session_state.compare:
        persona_columns = st.columns(len(PERSONAE))
        data = {
            "text_to_summarise": text_to_summarise,
            "language": language,
            "temperature": temp,
            "max_lenght": token,
        }
        for pc in zip(persona_columns, PERSONAE.keys()):
            with pc[0]:
                st.subheader(pc[1])
                message = summarise(token, temp, text_to_summarise, pc[1], language)
            data[pc[1]] = message
        st.download_button(
            "⬇️ Download results",
            json.dumps(data),
            file_name="results.json",
            mime="text/json",
            use_container_width=True,
        )

    else:
        summarise(token, temp, text_to_summarise, persona, language)

if not (paper or input_text):
    st.warning("Enter text or select paper first")
