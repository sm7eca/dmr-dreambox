
all: binary

SOURCEDIR = sketch_dreambox
SOURCES = $(wildcard ${SOURCEDIR}/*.ino)
ARDUINO_BOARD_FQDN = "esp32:esp32:esp32-DevKitLipo"
ARDUINO_PROGRAMMER_PORT = /dev/ttyACM0
ARDUINO_CLI_DOCKER_TAG = local/arduino-cli:latest
BUILD_DIR = build
RELEASE_VERSION_STRING=$(shell sed -n 's/^.*SoftwareVersion.* *= *//p' sketch_dreambox/sketch_dreambox.ino | sed 's/[;"]*//g')

# ${BUILD_DIR}/${SOURCEDIR}.bin

binary: venv boards libs ${BUILD_DIR}/${SOURCEDIR}.ino.bin

${BUILD_DIR}/%.bin: Makefile ${SOURCES}
	@echo "==> Compiling binary for ${ARDUINO_BOARD_FQDN}"
	@test -d ${BUILD_DIR} || mkdir -p ${BUILD_DIR}
	( \
		. .venv/bin/activate ; \
		arduino-cli compile --config-file arduino-cli.yaml --output-dir ${BUILD_DIR} --fqbn ${ARDUINO_BOARD_FQDN} ${SOURCEDIR}/ ; \
	)

upload: binary
	@echo "ready to upload file to board: ${ARDUINO_BOARD_FQDN}"
	arduino-cli upload --input-dir ${BUILD_DIR} -p ${ARDUINO_PROGRAMMER_PORT} --fqbn ${ARDUINO_BOARD_FQDN}

release: binary
	@echo "==> Creating a release for version ${RELEASE_VERSION_STRING}"
	@mkdir -p ${BUILD_DIR}/${RELEASE_VERSION_STRING}
	@cp ${BUILD_DIR}/*.{bin,elf} ${BUILD_DIR}/${RELEASE_VERSION_STRING}/.
	@zip -r ${BUILD_DIR}/${RELEASE_VERSION_STRING}.zip ${BUILD_DIR}/${RELEASE_VERSION_STRING}/ 1> /dev/null
	@tar czf ${BUILD_DIR}/${RELEASE_VERSION_STRING}.tar.gz ${BUILD_DIR}/${RELEASE_VERSION_STRING}/

docker: .built-docker

.built-docker: docker/Dockerfile
	docker build -t ${ARDUINO_CLI_DOCKER_TAG} docker/
	@touch $@

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

ctags: .built-ctags

.ctags-files: ${SOURCES}
	ls -1 ${SOURCEDIR}/*.ino > $@

${SOURCEDIR}/.tags: .ctags-files
	arduino-ctags -R -L $< --langmap=C:.ino -f $@

.built-ctags: ${SOURCEDIR}/.tags
	@touch $@
