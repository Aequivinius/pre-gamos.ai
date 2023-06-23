import os
import json
import openai
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_summarizer(
    max_tokens,
    temperature,
    prompt,
    person_type,
    language
):
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
                "content": f"Summarize this for a {person_type},: {prompt}",
            },
            {
                "role": "user",
                "content": f"Now translate this into {language}"
            }
        ],
    )
    return res["choices"][0]["message"]["content"]


# init the app
papers = {}
if "paper" not in st.session_state:
    st.session_state.paper = ""

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
    token = st.slider("№ tokens", min_value=0, max_value=200, value=100, step=1)
    temp = st.slider(
        "🌡️ Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.01,
        help="Temperature indicates how reproducable GPT-3.5's results will be, with 0 meaning very reproduceable, and 1 meaning practically random.",
    )
    # top_p = st.slider(
    #    "Nucleus Sampling", min_value=0.0, max_value=1.0, value=0.5, step=0.01
    # )
    # f_pen = st.slider(
    #    "Frequency Penalty", min_value=-1.0, max_value=1.0, value=0.0, step=0.01
    # ) """  # these are not so relevant to this demonstration

# Selection box to select the summarization style
with options_column2:
    persona = st.selectbox(
        "How do you like to be explained?",
        (
            "Second-Grader",
            "Professional Data Scientist",
            "Layperson",
            "University Student",
        ),
    )

with options_column3:
    languages = {
        "English" : "🇬🇧",
        "Spanish" : "🇪🇸",
        "German" : "🇩🇪",
        "Japanese" : "🇯🇵"
    }

    language = st.radio(
        "What language would you like the output to be in?", 
        languages.keys(),
        format_func = lambda x: languages[x]
    )

# Creating button for execute the text summarization
if st.button("Summarize!", type="primary", use_container_width=True, disabled=bool(not (paper or input_text))):
    with st.spinner("Request sent to GPT-3.5"):
        st.success(generate_summarizer(token, temp, input_text if input_text else papers[paper]["Text"], persona, language))

if not(paper or input_text):
    st.warning("Enter text or select paper first")