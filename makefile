CONTAINER_COMMAND ?= 'docker'

run-in-container:
	${CONTAINER_COMMAND} run -it --rm -p 8000:8000 -v $$(pwd):/docs quintana-docker.artifactory.cwp.pnp-hcl.com/dxubi:v1.0.0_8.7-1031 /bin/bash -c "sh /docs/jenkins/helpers/02-serve-doc.sh"

run-in-faster-container:
	${CONTAINER_COMMAND} run -it --rm -p 8000:8000 -v $$(pwd):/docs python:3.10-alpine /bin/sh -c "apk add git && git config --global --add safe.directory /docs && cd /docs && pip3 install -r ./requirements.txt && mkdocs serve -a 0.0.0.0:8000 --dirtyreload"

check-templates:
	@! grep -rn -e '{{' -e 'TODO(fill)' docs/ --include='*.md' \
	  || (echo "Unfilled template placeholder in docs/" && exit 1)

# Guards against a missing site/ on purpose: grep exits non-zero on a missing
# directory, which the leading "!" would otherwise turn into a silent pass.
check-raw-md:
	@test -d site || (echo "site/ not built - run 'mkdocs build' first" && exit 1)
	@! grep -rn -e '--8<--' site/ --include='*.md' \
	  || (echo "Unresolved snippet include in published raw Markdown" && exit 1)
