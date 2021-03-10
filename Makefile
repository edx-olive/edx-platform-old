
run:
	docker run -it \
		-v $(PWD):/build \
		-e ANSIBLE_SSH_KEY \
		-e ANSIBLE_VAULT_KEY \
                koa-maintenance \
		bash -c "cd /build && bash"
