.PHONY: test lint demo bench clean

test:
	pytest

lint:
	ruff check .

demo:
	python scripts/build_demo_artifacts.py --quick

bench:
	python -m photon_link_lab.cli benchmark

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
