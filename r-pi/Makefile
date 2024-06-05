SHELL := /bin/bash

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.PHONY: update_portainer install_portainer clean_portainer

update_portainer: ## Update to new portainer release
	@$(MAKE) clean_portainer
	@$(MAKE) install_portainer

install_portainer: ## Install portainer from scratch
	@echo "Running docker to install portainer .."
	docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest

clean_portainer: ## Stop and remove portainer
	@echo "Stopping portainer container .."
	docker stop portainer
	@echo "Removing portainer container .."
	docker rm portainer
