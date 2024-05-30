SHELL := /bin/bash

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' 

.PHONY: help build_listener build_ui

build_listener: ## Build the listener Docker image
	cd evoflow_listener && docker build --no-cache -t evoflow_listener --progress=plain . &> build_listener.log 

build_ui: ## Build the UI Docker image
	cd evoflow_ui && docker build --no-cache -t evoflow_ui --progress=plain . &> buil_ui.log 
