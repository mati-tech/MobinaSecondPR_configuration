PYTHON ?= python3
PACKAGE ?= A
REPO_URL := $(shell $(PYTHON) -c "from pathlib import Path; \
print(Path('tests/fixtures/maven_repo').resolve().as_uri())")
MAVEN_ARGS = --repository $(REPO_URL) --version 1.0 --max-depth 5 \
	--ascii-tree --load-order

.PHONY: run test demo clean

run:
	$(PYTHON) -m src.main --package $(PACKAGE) --test-mode \
		--repository tests/fixtures/acyclic.txt --ascii-tree --load-order

test:
	$(PYTHON) -m unittest discover -s tests -v

demo:
	mkdir -p build
	$(PYTHON) -m src.main --package com.example:app $(MAVEN_ARGS) \
		--image build/app.png --d2-file build/app.d2
	$(PYTHON) -m src.main --package com.example:webapp $(MAVEN_ARGS) \
		--image build/webapp.png --d2-file build/webapp.d2
	$(PYTHON) -m src.main --package com.example:cyc-a $(MAVEN_ARGS) \
		--image build/cyc-a.png --d2-file build/cyc-a.d2

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf build dependency-graph.png dependency-graph.d2
