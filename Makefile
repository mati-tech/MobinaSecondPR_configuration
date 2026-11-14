PYTHON ?= python3
PACKAGE ?= A

.PHONY: run test clean

run:
	$(PYTHON) -m src.main --package $(PACKAGE) --test-mode \
		--test-file tests/fixtures/acyclic.txt --ascii-tree --load-order

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -f graph.png graph.d2
