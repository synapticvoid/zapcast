
.DEFAULT_GOAL := help

###############################################################################
# Variables
###############################################################################

# Update python path from venv commands (ruff, ty, etc)
export PYTHONPATH=$PYTHONPATH:${current_dir}/src

.PHONY: ruff
ruff:  ## Format and lint source code using Ruff
	ruff format src/
	ruff check --fix src/

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*?## "; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^\.SECTION:/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 11) } \
		/^[a-zA-Z_-]+:.*?## / { printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2 }' \
		$(MAKEFILE_LIST)