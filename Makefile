
all: binary

SOURCEDIR = sketch_dreambox
SOURCES = $(wildcard ${SOURCEDIR}/*.ino)
ARDUINO_BOARD_FQDN = "esp32:esp32:esp32"
ARDUINO_PROGRAMMER_PORT = /dev/ttyACM0
ARDUINO_CLI_DOCKER_TAG = local/arduino-cli:latest
BUILD_DIR = build


binary: boards libs ${BUILD_DIR}/${SOURCEDIR}.bin
	

${BUILD_DIR}/%.bin: Makefile ${SOURCES}
	@echo "==> Compiling binary for ${ARDUINO_BOARD_FQDN}"
	@test -d ${BUILD_DIR} || mkdir -p ${BUILD_DIR}
	@arduino-cli compile --config-file arduino-cli.yaml --output-dir ${BUILD_DIR} --fqbn ${ARDUINO_BOARD_FQDN} ${SOURCEDIR}/

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


libs: .built-libs

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