.PHONY: dev-deps offline-deps test test-docker build-test-image

dev-deps:
	python3 -m pip install -r requirements-dev.txt

offline-deps:
	bash tools/install_offline.sh

test:
	pytest -q

build-test-image:
	docker build -f Dockerfile.test -t commons-tests .

test-docker: build-test-image
	docker run --rm commons-tests 