🪻 A small demonstration app that allows you to enter a text (we're thinking of biomedical texts here), and ask ChatGPT to (a) summarise and (b) simplify it. 

👧 You can chose from different personas, and so regulate the level of simplification.

# Usage

* it's a `streamlit` app, under `poetry` dependency management, so use the following command to run:

```
poetry run streamlit run app.py
```

# Development

* I like to use `poetry`, but I always forget that `streamlit` doesn't, so I need to remember to `poetry export -f requirements.txt --output requirements.txt` before `push`ing
