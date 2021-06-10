#!/bin/bash
export ANSIBLE_VAULT_KEY=`cat /home/ubuntu/vault_password `
export ANSIBLE_SSH_KEY=`cat /home/ubuntu/.ssh/id_rsa`
chmod 600 ~/.ssh/id_rsa
echo -e "Host gitlab.raccoongang.com\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config
env
git clone git@gitlab.raccoongang.com:hippoteam/spectrum/configuration.git

git clone git@gitlab.raccoongang.com:hippoteam/spectrum/deployment.git

if [ -z "$ANSIBLE_SSH_KEY" ]
then
    echo "ANSIBLE_SSH_KEY env variable is needed to use image."
    echo "By default it's provided by Gitlab CI."
    echo "If you want to use this image locally please provide it yourself"
    exit 1
fi

if [ -z "$ANSIBLE_VAULT_KEY" ]
then
    echo "ANSIBLE_VAULT_KEY env variable is needed to use image."
    echo "By default it's provided by Gitlab CI."
    echo "If you want to use this image locally please provide it yourself"
    exit 1
fi

sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install python3-dev python3-pip default-libmysqlclient-dev build-essential -y
sudo pip install ansible     datadog     PyYAML     zabbix-api     mysqlclient     && rm -rf ~/.cache

export ANSIBLE_ROLES_PATH="/home/ubuntu/configuration/playbooks/roles"
export ANSIBLE_CONFIG="/home/ubuntu/configuration/playbooks/ansible.cfg"
export ANSIBLE_VAULT_PASSWORD_FILE="/home/ubuntu/vault_password"
export ANSIBLE_RETRY_FILES_SAVE_PATH="/tmp"
export ANSIBLE_LIBRARY="/home/ubuntu/configuration/playbooks/library"
export ANSIBLE_INVENTORY="/home/ubuntu/configuration/inventory/hosts.yml,/home/ubuntu/deployment/hosts.yml"

cd deployment

ansible-playbook dev.yml -vvv

rm -rf /home/ubuntu/deployment
rm -rf /home/ubuntu/configuration
