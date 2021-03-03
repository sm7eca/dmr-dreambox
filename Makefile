
all: help

PROJECT_NAME = dmr_dreambox
SOURCEDIR = sketch_dreambox
SOURCES_EIM_SERVICE = $(shell find eim-service/ -type f -name "*.py")
SOURCES_C = $(wildcard ${SOURCEDIR}/*.ino)
SOURCES_H = $(wildcard ${SOURCEDIR}/*.h)
ARDUINO_BOARD_FQDN = "esp32:esp32:esp32-DevKitLipo"
ARDUINO_PROGRAMMER_PORT = /dev/ttyUSB0
ARDUINO_CLI_DOCKER_TAG = local/arduino-cli:latest
BUILD_DIR = build
RELEASE_VERSION_STRING=$(shell sed -n 's/^.*SoftwareVersion.* *= *//p' sketch_dreambox/sketch_dreambox.ino | sed 's/[;"]*//g')
RELEASE_NAME = ${PROJECT_NAME}_${RELEASE_VERSION_STRING}
RELEASE_DIR = ${BUILD_DIR}/${RELEASE_NAME}
GIT_COMMIT_HASH = $(shell git rev-parse HEAD)
TIMESTAMP = $(shell date +"%Y%m%d_%H%M%S")

CHANGES := $(shell git diff-index --name-only HEAD -- | wc -l)

.PHONY = help
help:
	@echo -e "\n  Make system for DMR Dreambox project"
	@echo "    release     : build ESP binary, create ZIP file, build and upload Docker container"
	@echo "    esp-binary  : build ESP binary "
	@echo "    esp-upload  : build and upload ESP binary"
	@echo "    eim-release : build and upload EIM Docker container"
	@echo "    eim-deploy  : deploy EIM service to production"
	@echo

esp-binary: venv boards libs ${BUILD_DIR}/${SOURCEDIR}.ino.bin

${BUILD_DIR}/%.bin: venv Makefile ${SOURCES_C} ${SOURCES_H}
	@echo "==> Compiling binary for ${ARDUINO_BOARD_FQDN}"
	@test -d ${BUILD_DIR} || mkdir -p ${BUILD_DIR}
	@( \
		. .venv/bin/activate ; \
		arduino-cli compile --config-file arduino-cli.yaml --output-dir ${BUILD_DIR} --fqbn ${ARDUINO_BOARD_FQDN} ${SOURCEDIR}/ ; \
	)

esp-upload: esp-binary
	@echo "ready to upload file to board: ${ARDUINO_BOARD_FQDN}"
	arduino-cli upload --input-dir ${BUILD_DIR} -p ${ARDUINO_PROGRAMMER_PORT} --fqbn ${ARDUINO_BOARD_FQDN}

release: ${BUILD_DIR}/${RELEASE_NAME}.zip function-test eim-release release-tag
	@echo "==> Release DONE, push tags and upload binaries to Github https://github.com/sm7eca/dmr-dreambox/releases"

${RELEASE_DIR}:
	@test -d $@ || mkdir -p $@

manifest: ${RELEASE_DIR}/manifest.txt

${RELEASE_DIR}/manifest.txt: Makefile ${RELEASE_DIR}
	@echo "==> Writing manifest file"
	@rm -f $@
	@echo "project: ${PROJECT_NAME}" >> $@
	@echo "esp_board: ${ARDUINO_BOARD_FQDN}" >> $@
	@echo "git_commit_hash: ${GIT_COMMIT_HASH}" >> $@
	@echo "version: ${RELEASE_VERSION_STRING}" >> $@
	@echo "created: ${TIMESTAMP}" >> $@

check-changes:
	@if [ ${CHANGES} != 0 ]; then \
	  echo "local changes, please cleanup"; exit 1 ; \
	fi

${BUILD_DIR}/%.zip: check-changes esp-binary manifest ${RELEASE_DIR}
	@echo "==> Creating a release $@"
	@cp ${BUILD_DIR}/*.{bin,elf} ${RELEASE_DIR}/.
	@cp hmi/*.tft ${RELEASE_DIR}/.
	@( \
		cd ${BUILD_DIR} ; \
		zip -r ${RELEASE_NAME}.zip ${RELEASE_NAME}/ 1> /dev/null ; \
		sha256sum ${RELEASE_NAME}.zip > ${RELEASE_NAME}.zip.sha256 ; \
		rm -rf ${RELEASE_NAME}/ ; \
	)

.PHONY=clean
clean:
	rm -rf build
	rm -f .built*
	rm -rf .venv
	rm -rf Arduino/user
	rm -f .ctags-*
	rm -f ${SOURCEDIR}/.tags*

clean-all: clean
	rm -rf Arduino/

update:
	arduino-cli update --config-file arduino-cli.yaml


libs: .built-libs

venv: .built-venv

.built-venv: requirements.pip.txt
	( \
		python3 -m venv .venv ; \
		. .venv/bin/activate ; \
		python3 -m pip install --upgrade pip ; \
		python3 -m pip install -r $< ; \
		touch $@ ; \
	)

.built-libs: requirements.libraries.txt
	@echo "==> Installing libraries ***"
	arduino-cli lib update-index
	@if [ -e $< ]; \
	then while read -r i ; do echo ; \
	  echo "---> Installing " '"'$$i'"' ; \
	  arduino-cli lib install "$$i" ; \
	  touch $@; \
	done < $< ; \
	else echo "---> MISSING boards.arduino.txt file"; \
	fi

boards: .built-boards

.built-boards: requirements.boards.txt
	@echo "==> Installing board support ***"
	arduino-cli core update-index
	@if [ -e $< ]; \
	then while read -r i ; do echo ; \
	  echo "---> Installing " '"'$$i'"' ; \
	  arduino-cli core install "$$i" ; \
	  touch $@ ; \
	done < $< ; \
	else echo "---> MISSING requirements.boards.txt file"; \
	fi

eim-release: .built-pushed-docker

.PHONY = .built-pushed-docker
.built-pushed-docker: Makefile
	@echo "==> Build and push Docker container"
	@docker build -t eim-core-base:latest eim-service/docker/eim-core-base/.
	@docker-compose -f eim-service/docker-compose.yml build
	@docker tag eim-core:latest smangelsen/eim-core:${RELEASE_NAME}
	@docker tag eim-mongodb:latest smangelsen/eim-mongodb:${RELEASE_NAME}
	@docker tag eim-harvester:latest smangelsen/eim-harvester:${RELEASE_NAME}
	@docker push smangelsen/eim-core:${RELEASE_NAME}
	@docker push smangelsen/eim-mongodb:${RELEASE_NAME}
	@docker push smangelsen/eim-harvester:${RELEASE_NAME}
	@touch $@

ctags: .built-ctags

.ctags-files: ${SOURCES_C} ${SOURCES_H}
	ls -1 ${SOURCEDIR}/*.ino > $@

${SOURCEDIR}/.tags: .ctags-files
	arduino-ctags -R -L $< --langmap=C:.ino -f $@

.built-ctags: ${SOURCEDIR}/.tags
	@touch $@

eim-deploy: .built-eim-deploy

PHONY = eim-deploy-local
eim-deploy-local: ${SOURCES_EIM_SERVICE}
	@echo "==> deploy EIM service locally"
	@docker-compose -f eim-service/docker-compose.yml build
	@( \
		cd eim-service/deployment ; \
		ansible-playbook -i inventory.yml --extra-vars "dmr_release_name=${RELEASE_NAME}" --limit local site.yml; \
	)
	pwd

.built-eim-deploy: Makefile ${SOURCES_EIM_SERVICE}
	@echo "==> deploy EIM service to production"
	@( \
		cd eim-service/deployment ; \
		ansible-playbook -i inventory.yml --extra-vars "dmr_release_name=${RELEASE_NAME}" --limit production site.yml -K; \
	)
	pwd
	@touch $@

release-tag:
	$(call git-create-tag,${RELEASE_VERSION_STRING})
	@echo "==> create GIT tag: ${RELEASE_VERSION_STRING}"

function-test: venv-test eim-deploy-local .built-function-test

venv-test: .built-venv-test

.built-venv-test: Makefile requirements-test.txt
	@( \
		echo "==> build VENV"; \
		python3 -m venv .venv ; \
		. .venv/bin/activate ; \
		python3 -m pip install --upgrade pip ; \
		python3 -m pip install -r requirements-test.txt ; \
	)
	@touch $@

.built-function-test: venv-test Makefile
	@( \
		echo "==> run function tests"; \
		python3 -m venv .venv ; \
		. .venv/bin/activate ; \
		python3 -m pytest -xvs tests/ ; \
	)
	@touch $@

#
# functions
#
define git-create-tag
   @git tag -a -m "this_is_a_tag" $(1) HEAD
endef
