
run:
	docker run -it \
		-v $(PWD):/build \
		-e ANSIBLE_SSH_KEY \
		-e ANSIBLE_VAULT_KEY \
		registry-gitlab.raccoongang.com/devops/configuration:ironwood-rg-develop \
		bash -c "cd /build && bash"
