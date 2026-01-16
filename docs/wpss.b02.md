# wpss.b02

This appears to be an AARCH32 executable using the T32 instruction
set. [Binwalk](https://github.com/ReFirmLabs/binwalk) fails to
identify the architecture. Experimenting with various options the
assembly for this looks like actual code. The [GNU
Binutils](https://www.gnu.org/software/binutils/) seems to think it's
an *elf32-littlearm* BFD target, and that's the only one that it
disassembles successfully. [Radre2](https://rada.re/advent/09.html)
seems to agree, and generates the same assembly output. Since I don't
see any weird code sequences or invalid instructions, it looks
legit. I'd have to really dig into reading the assembly to be sure.

I also wrote a simple Thumb dissasembler using
[Capstone](https://www.capstone-engine.org/) as an additional test.
