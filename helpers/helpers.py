from Bio import Entrez
from Bio.Entrez import efetch, read
import difflib
from streamlit import cache_data, secrets
from openai import OpenAI
import fugashi
from . import constants

# SETUP
gpt_client = OpenAI(api_key=secrets["OPENAI_API_KEY"])

# SETUP
Entrez.email = "nicola.colic@supsi.ch"
jp_tagger = None


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
def show_diff(a, b, lang=None):
    """Unify operations between two compared strings
    seqm is a difflib.SequenceMatcher instance whose a & b are strings"""
    if lang != "Japanese":
        seqm = difflib.SequenceMatcher(None, a.split(" "), b.split(" "))
    else:
        global jp_tagger
        if jp_tagger is None:
            jp_tagger = fugashi.Tagger()
        a_tokens = [word.surface for word in jp_tagger(a)]
        b_tokens = [word.surface for word in jp_tagger(b)]
        seqm = difflib.SequenceMatcher(None, a_tokens, b_tokens)
    output_a, output_b = [], []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == "equal":
            output_a.append(" ".join(seqm.a[a0:a1]) + " ")
            output_b.append(" ".join(seqm.b[b0:b1]) + " ")
        if opcode == "delete":
            output_a.append((" ".join(seqm.a[a0:a1]), "", "#f4baba"))
        if opcode == "replace":
            output_a.append((" ".join(seqm.a[a0:a1]), "", "#babdf4"))
            output_b.append((" ".join(seqm.b[b0:b1]), "", "#babdf4"))
        if opcode == "insert":
            output_b.append((" ".join(seqm.b[b0:b1]), "", "#baf4cc"))
    return output_a, output_b


##############
# OPENAI STUFF
##############
@cache_data
def prompt(max_tokens, temperature, prompt, persona, language):
    characteristics = constants.CHARACTERISTICS[persona]

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant for text summarization.",
        },
        {
            "role": "user",
            "content": f"Create a summary { ('in ' + language) if language != 'English' else ''} of the following text {characteristics}: {prompt}",
        },
    ]

    res = gpt_client.chat.completions.create(
        model="gpt-3.5-turbo",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,
    )
    return res.choices[0].message.content, res.choices[0].finish_reason


############
# DATA STUFF
############
def data_to_csv(data):
    import csv, io

    csv_buffer = io.StringIO()
    fc = csv.DictWriter(csv_buffer, fieldnames=data[0].keys())
    fc.writeheader()
    fc.writerows(data)
    return csv_buffer.getvalue()
