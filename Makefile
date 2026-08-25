.PHONY: setup pipeline dashboard

setup:
	pip install -r requirements.txt

pipeline:
	python load_data.py
	python analysis.py

dashboard:
	streamlit run app.py --server.port 8501 --server.address 0.0.0.0