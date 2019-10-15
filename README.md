How to start
============

1. Fork this repo into project group
2. Clone repo locally
3. Switch to `ironwood-rg` branch
```
git checkout ironwood-rg
```
4. Generate secrets by running this command
```
perl -pi -e 's/(XXX+)/join "", map { ("a" .. "z", "A" .. "Z", 0 .. 9)[rand(62)] } 1 .. length($1)/eg' group_vars/project_name/secrets.yml
```
5. Encrypt secrets with raccoondeploy vault password
```
ansible-vault encrypt --ask-vault-pass group_vars/project_name_group/secrets.yml 
```
6. Rename inventory directories `project_name` to group and hosts from [inventory](https://gitlab.raccoongang.com/DevOps/inventory) repository
```
git mv group_vars/project_name group_vars/project_name_group
git mv host_vars/project_name_stage host_vars/project_name_stage_host
git mv host_vars/project_name_dev host_vars/project_name_dev_host
```
7. Replace all occurrence of `project_name` phrase with values from Project Requirements document
```
grep -lr 'project_name' * .gitlab-ci.yml
```
8. Configure OpenEdx extra-vars as difference from [configuration repository](https://gitlab.raccoongang.com/edx/configuration.git)
9. Push changes into `master` branch of project repository
10. Configure GitLab CI/CD variables:
  - JENKINS_DEPLOY_KEY
  - DEVOPS_VAULT_KEY
  - CONFIGURATION_IMAGE_DEV
  - CONFIGURATION_IMAGE_STAGE
  - CONFIGURATION_IMAGE_PRODUCTION
  - EDX_PLATFORM_VERSION_DEV
  - EDX_PLATFORM_VERSION_STAGE
  - EDX_PLATFORM_VERSION_PRODUCTION
