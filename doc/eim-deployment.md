
## Deployment

### Internals

Every deployment consist of the following steps.

- Build the ESP code using _arduino_cli_
- Prepare a ZIP file containing ESP binaries and Nextion configuration binary
- Run unit tests against the Python code
- Build Docker images
- Bring up the service locally
- Run function test against locally deployed
- Tag those approved images and upload them to _DockerHub_ with the release name.
- Run the _Ansible_ playbook that will generate required files and bring up the stack on the target machine.
- Git is used to create a tag in _Github_ repository.

And everyting we have to do that is running the following command.

```bash
make eim-deploy
```

If everything is green, ensure that the create Git tag is pushed to _Github_ by running the following command.

```bash
git push --tags
```

The remaining thing is to create a release in _Github_ by going to the list of tags, identify that has recently been pushed and turn that one into a _Github release_. There will be a dialogue where one is allowed to upload attachments. Ensure that you upload the ZIP file found in `build/` folder.


## Release is broken? - Just role back.

In case that the release is broken - don't panic - just role back. The follow listing shows how to achieve that.

```bash
# get back to the main branch
git checkout main

# checkout a previous release, this is done through Git tags - you remember?
git checkout <LAST_RELEASE_NAME_THAT_WAS_WORKING>

# remove any previous build artifacts
make clean

# run a deployment for that given version - Done!
make eim-deploy
```


## Prerequisites

### Developer Machine

- A Linux machine
- An SSH login on the target machine
- Installed Docker, docker-compose, Python3, Ansible and Git as well as Make

### Service Host

- A Linux machine running preferably Ubuntu
- Installed Docker, docker-compose as well as Python3

