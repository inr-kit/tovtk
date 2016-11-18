SHELL = /bin/bash

.SUFFIXES:
.SECONDARY:
.ONESHELL:

.PHONY: all 

all: 5.meshtal 6.meshtal

%.meshtal: inp
	rm -f $*.*
	mcnp$* inp = inp run = $*.runtp out = $*.outp mesht = $*.meshtal tasks 3


