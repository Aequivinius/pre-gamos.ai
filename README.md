🪻 A small demonstration app that allows you to enter a text (we're thinking of biomedical texts here), and ask ChatGPT to (a) summarise and (b) simplify it. 

👧 You can chose from different personas, and thus regulate the level of simplification.

# Usage

* it's a `streamlit` app, under `poetry` dependency management, so use the following command to run:

```
poetry run streamlit run app.py
```

# Development

* I like to use `poetry`, but I always forget that `streamlit` doesn't, so I need to add the packages to the `requirements.txt` and then [reboot](https://share.streamlit.io/) the app.

# Wish List

- [ ] Refactoring for the main generation
- [ ] Test cases, pre-commits etc.
    - [ ] Try out `mypy`
- [ ] Tidy out `helpers` package