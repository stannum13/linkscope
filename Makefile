.PHONY: test lint smoke bench clean

test:
	pytest

lint:
	ruff check .

smoke:
	scripts/reproduce_e001.sh experiments/e001/configs/smoke.json

bench:
	python -m photon_link_lab.cli benchmark

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info artifacts plots results/e001
