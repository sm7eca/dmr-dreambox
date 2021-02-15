
# EIM Service

- Docker based
- 2 containers, one for the core and one for the MongoDB

## Network Setup

- Core exposes port 80 outwards exposing the Rest API
- MongoDB container is isolated on the so-called "backend"
  network, it has no access to the internet, only the Core 
  will be able to connect to it.

## Volume Setup

- A single persistent volume is created in order to store the
  MongoDB and make it persistent between restarts.


# Deployment

## Local Deployment

- For local deployment run the following command.

    docker-compose up -d

## Remote Deployment

- For remote deployment, the code provides an Ansible
  playbook that fully automates the deployment to any
  Linux machine capabable of running Python.
- Ensure that you update the deployment/inventory.yml
  with correct hostnames.
- Before running the playbook, one has to copy a valid
  SSH public key to the remote server and paste it's
  content into the file called ~/.ssh/autorized_keys.

    cd deployment/
    ansible-playbook -i inventory.yml site.yml
