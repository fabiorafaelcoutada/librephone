# The wpss.b01 Blob

This binary appears to be an ATMel AVR8 (ATmega8) micro-controller
embedded in the WCN6750. Other manufactures than Qualcomm have an
equivalent Wireless Processor SubSystem (WPSS) implementation, and
they also contain an embedded ATMel micro-controller. This is an 8 bit
chip, and the GNU toolchain has maintained support for it.

Using the *radre2* program you can disassemble the raw binary into
assembly. The *cutter-re* program manages to figure this out without
the options. Assuming it's properly identifying the architecture that
is. The assembly code *looks* good, further reading is necessary.

	r2 -e bin.relocs.apply=true -a avr wpss.b01


[Machine options](https://www.nongnu.org/avr-libc/user-manual/using_tools.html)

What weird is while the GNU toolchain has AVR support, objdump refuses
to recognize the format, so it's also possible the generated
disassembly is junk. That won't be obvious until I figure out where
each file is getting loaded.
