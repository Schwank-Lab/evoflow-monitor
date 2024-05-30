SHELL := /bin/bash

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' 

.PHONY: help build_base test

build_base: ## Build IDEC Docker Base image
	docker build --no-cache --build-arg ssh_private_key="$$(cat ~/.ssh/idec_github)" -t idec_base .
