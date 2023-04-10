.PHONY: setup run clean

setup:
	python3 -m venv venv
	. venv/bin/activate; pip install -r requirements.txt

run:
	. venv/bin/activate; python -m music_transcriber.ui

clean:
	rm -rf venv
	rm -rf __pycache__
	rm -rf music_transcriber/__pycache__
