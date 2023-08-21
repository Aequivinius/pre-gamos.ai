from Bio import Entrez
from Bio.Entrez import efetch, read
import difflib
from streamlit import cache_data
import openai
from constants import *

# SETUP
Entrez.email = "nicola.colic@supsi.ch"


def chunker(iterable, chunksize):
    for i, c in enumerate(iterable[::chunksize]):
        yield iterable[i * chunksize : (i + 1) * chunksize]


############
# PMID STUFF
############
@cache_data
def fetch_abstract(pmid):
    handle = efetch(db="pubmed", id=pmid, retmode="xml")
    xml_data = read(handle)
    try:
        article = xml_data["PubmedArticle"][0]["MedlineCitation"]["Article"]
        abstract = article["Abstract"]["AbstractText"]
        return abstract[0]
    except IndexError:
        return "Paper could not be found"


@cache_data
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


##############
# OPENAI STUFF
##############
def prompt(max_tokens, temperature, prompt, persona, language):
    length = LENGTHS[int(max_tokens / 200)]
    characteristics = CHARACTERISTICS[persona]
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant for text summarization.",
        },
        {
            "role": "user",
            "content": f"Create a {length} summary of the following text {characteristics}: {prompt}",
        },
    ]

    if language != "English":
        messages.append(
            {"role": "user", "content": f"Now translate this into {language}"}
        )

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,
    )
    return res["choices"][0]["message"]["content"], res["choices"][0]["finish_reason"]
