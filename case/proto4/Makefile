.PHONY: all
all: box case mounts

.PHONY: mounts
mounts: mounts/p4_imx290.stl mounts/p4_mft.stl mounts/p4_cmount.stl

.PHONY: box
box: box_bottom.stl box_top.stl

.PHONY: case
PROTO4_TARGETS=$(shell sed '/^module [a-z0-9_-]*().*make..\?me.*$$/!d;s/module //;s/().*/.stl/' case_proto4.scad)
case: ${PROTO4_TARGETS}
.SECONDARY: $(shell echo "${PROTO4_TARGETS}" | sed 's/\.stl/.scad/g')

%.scad:
	echo -ne 'use <case_proto4.scad>\n$*();' > $@

box_bottom.stl: case_box.scad
	openscad -m make -o $@ -d $@.deps -D "render_bottom=true"  $<

box_top.stl: case_box.scad
	openscad -m make -o $@ -d $@.deps -D "render_bottom=false"  $<

include $(wildcard *.deps)

%.stl: %.scad
	openscad -m make -o $@ -d $@.deps $<

.PHONY: clean
clean:
	rm -f *.stl
	rm -f *.deps
	rm -f mounts/*.stl
	rm -f mounts/*.deps
	rm -f case_front.scad case_rear.scad