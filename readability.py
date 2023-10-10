import textstat
import fugashi

readability_tagger = None


def readability(text, language):
    if language == "Japanese":
        return readability_jp(text)

    textstat.set_lang(
        {
            "English": "EN",
            "Spanish": "ES",
            "Italian": "IT",
            "German": "DE",
            "Japanese": "JP",
        }[language].lower()
    )
    return textstat.flesch_reading_ease(text)


def readability_jp(text):
    global readability_tagger
    if readability_tagger is None:
        readability_tagger = fugashi.Tagger()

    parsed = readability_tagger(text)
    num_words = len(parsed)
    num_sentences = text.count("。")
    num_syllables = sum(
        [
            len(word.feature.pron)
            if word.feature.pron and word.feature.pron != ""
            else len(word.surface)
            for word in parsed
        ]
    )

    average_word_length = num_syllables / num_words
    average_sentence_length = num_words / num_sentences
    return 206.835 - 84.6 * average_word_length - 1.015 * average_sentence_length
