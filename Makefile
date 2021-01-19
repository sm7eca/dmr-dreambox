
all: binary

SOURCEDIR = sketch_dreambox
SOURCES = $(wildcard ${SOURCEDIR}/*.ino)
ARDUINO_BOARD_FQDN = "arduino:samd:mkr1000"
ARDUINO_BOARD_CORE = "arduino:samd"
ARDUINO_PROGRAMMER_PORT = /dev/ttyACM0
ARDUINO_CLI_DOCKER_TAG = local/arduino-cli:latest
BUILD_DIR = build

.PHONY := board-core
board-core:
	arduino-cli core install ${ARDUINO_BOARD_CORE}

binary: docker board-core ${BUILD_DIR}/${SOURCEDIR}.elf
	

${BUILD_DIR}/%.elf: Makefile ${SOURCES}
	test -d ${BUILD_DIR} || mkdir -p ${BUILD_DIR}
	arduino-cli compile --output-dir ${BUILD_DIR} --fqbn ${ARDUINO_BOARD_FQDN} ${SOURCEDIR}/

upload: binary
	@echo "ready to upload file to board: ${ARDUINO_BOARD_FQDN}"
	arduino-cli upload --input-dir ${BUILD_DIR} -p ${ARDUINO_PROGRAMMER_PORT} --fqbn ${ARDUINO_BOARD_FQDN}

docker: .built-docker

.built-docker: docker/Dockerfile
	docker build -t ${ARDUINO_CLI_DOCKER_TAG} docker/
	@touch $@

clean:
	rm -rf build
	rm -f .built*
