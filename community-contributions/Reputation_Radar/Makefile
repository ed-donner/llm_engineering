PYTHON ?= python

.PHONY: install run test

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

run:
	streamlit run app.py

test:
	pytest
