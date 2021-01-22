
all: binary

SOURCEDIR = sketch_dreambox
SOURCES = $(wildcard ${SOURCEDIR}/*.ino)
ARDUINO_BOARD_FQDN = "esp32:esp32:esp32"
ARDUINO_PROGRAMMER_PORT = /dev/ttyACM0
ARDUINO_CLI_DOCKER_TAG = local/arduino-cli:latest
BUILD_DIR = build

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