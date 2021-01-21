
# Introduction

This project is intended to provide an Arduino based controller for a DMR board
that can be controlled from a Nextion display.

![DMR Dreambox](doc/img/IMG_20210119_232006.jpg)

# Installation

## Linux - Arch Linux

    sudo pacman -Sy arduino arduino-avr-core arduino-cli

## Linux - Ubuntu

    sudo apt install arduino arduino-cli

## Linux - Building inside a Docker container

This has the advantage that we would avoid installing all the necessary dependencies
on our system.

	docker build -t local/arduino-cli:latest docker/
	docker run -t -i local/arduino-cli:latest arduino-cli version

## Windows
Download the latest binaries from [software page](https://www.arduino.cc/en/software).

# References

* [Missing dependencies in Arch Linux](https://bugs.archlinux.org/task/60378)
* [Building inside a docker container](https://hub.docker.com/r/arduino/arduino-cli)
* [Arduino CLI - getting started](https://arduino.github.io/arduino-cli/latest/getting-started/)
* [Install ESP libraries](https://github.com/espressif/arduino-esp32#installation-instructions)
* [ESP libraries](https://github.com/espressif/arduino-esp32/tree/master/libraries)
* [Github - simple Makefile](https://github.com/digiampietro/arduino-makefile/blob/master/blink-arduino/Makefile)