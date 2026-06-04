install:
	sudo apt update
	sudo apt install -y python3-pip
	sudo apt install -y vlc
	pip3 install -r requirements.txt

dev:
	python3 -m venv venv
	venv/bin/pip3 install -r requirements.txt
	@echo "Run: source venv/bin/activate"

test:
	venv/bin/python3 -m pytest tests/test.py

