
run:
	docker run -it \
		-v $(PWD):/build \
		-e ANSIBLE_SSH_KEY \
		-e ANSIBLE_VAULT_KEY \
		registry-gitlab.raccoongang.com/duck-team/ironwood-rg/configuration:ironwood-rg-develop \
		bash -c "cd /build && bash"
