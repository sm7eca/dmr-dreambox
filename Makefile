
all: binary

SOURCEDIR = sketch_dreambox
SOURCES = $(wildcard ${SOURCEDIR}/*.ino)
ARDUINO_BOARD_FQDN = "arduino:samd:mkr1000"
ARDUINO_BOARD_CORE = "arduino:samd"
ARDUINO_PROGRAMMER_PORT = /dev/ttyACM0
BUILD_DIR = build

.PHONY := board-core
board-core:
	arduino-cli core install ${ARDUINO_BOARD_CORE}

binary: board-core ${BUILD_DIR}/${SOURCEDIR}.elf
	

${BUILD_DIR}/%.elf: Makefile ${SOURCES}
	test -d ${BUILD_DIR} || mkdir -p ${BUILD_DIR}
	arduino-cli compile --output-dir ${BUILD_DIR} --fqbn ${ARDUINO_BOARD_FQDN} ${SOURCEDIR}/

upload: binary
	@echo "ready to upload file to board: ${ARDUINO_BOARD_FQDN}"
	arduino-cli upload --input-dir ${BUILD_DIR} -p ${ARDUINO_PROGRAMMER_PORT} --fqbn ${ARDUINO_BOARD_FQDN}

clean:
	rm -rf build/*
	rm -f .built*
