
run:
	docker run -it \
		-v $(PWD):/build \
		-e ANSIBLE_SSH_KEY \
		-e ANSIBLE_VAULT_KEY \
		registry-gitlab.raccoongang.com/edx/configuration/configuration-ironwood-rg:latest \
		bash -c "cd /build && bash"
