SHELL := /bin/bash

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' 

.PHONY: help build_listener build_ui

build_listener: ## Build the listener Docker image
	docker build -t evoflow_listener -f evoflow_listener/Dockerfile .

build_ui: ## Build the UI Docker image
	docker build -t evoflow_ui -f evoflow_ui/Dockerfile .
