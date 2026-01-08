# Reverse Engineering Tools

I use several different tools when analyzing binary blobs. If you know
the architecture of the blob, it's a little easier since you can be
confident the disassembly is good. If you need to use a tool to
identify the architecture, the generated assembly code could just be
garbage that looks like assembly code.

## Disassembling Binary Blobs

It is possible to disasemble the binary blobs what are executables
into assembly code. For a modern mobile device the architecture is
usually limited to an SnapsDragon SoC (AARCH64 & AARCH32). Other
support chips for the radio functionality may contain an ATMel
mico-controller or RISCV32. The AARCH architecture has 3 different
instruction sets, the 64 bit one for an AARCH64, and two for the
AARCH32. The AARCH32 is an older Armv7 core and supports both a 16 bit
instruction set called called Thumb (T32), and a 32 bit instruction
set (A32). If you have an unidentified blob that you're pretty sure is
an ARM chip, you can try all 3 of the above.

If the disassembly is garbage you usually see multiple *invalid*
instructions. That means the disassembly tool has no idea what it's
actually analyzing. Another common thing is a weird code flow. A
classic example is several lines loading a register into itsef
repeatedly. Unfortunately beyond these two obvious examples, you have
to be able to read assembly code to know if it's valid.

You also need to validate that it's an executable file. I usually
first try to see if it's a sparse file system, or a compressed
image. As far as I can tell, none of the blobs we're interested in
are either. Data files may also look like an executable, so if
repeated attempts with multiple tools fails to generate clean asembly,
it's probably a binary data file that gets loaded directly into
memory.

## Command Line Tools

## [OD](https://en.wikipedia.org/wiki/Od_(Unix))

I actually use the old Unix utility heavily, which I've used for many
decades. This can dump out a binary blob in multiple ways. While the
output is only text, you can have it dump ASCII strings, different bit
sizes, etc.. It's very useful for quick and dirty analysis. The other
fun is you can then use other tools like grep to look for patterns.

## [GNU Binutils](https://www.gnu.org/software/binutils/)

The GNU Binutils is the backend of the GNU Toolchain, which supports
almost all the processors since it's often the cross compiler used by
the manufacturers. The binutils aren't reverse engineering tools, but
do contain several programs that are very useful. Many of the higher
level reverse engineering tools use the binutils as part of their
backend.

The main tool I use is *objdump*, and sometimes *objcopy*. On occasion
I'll use *nm* to list symbols (most blobs have no symbols), or
*strings* to look for ASCII strings in the blob. If objdump doesn't
recognize the architecture it's probably a data file. You do have to
specify that the input format is a binary, and which output format you
want. It's also possible the output format you specify is wrong.

What I do is use objdump to copy the binary into an ELF file, and see
if objdump can recognize the architecture when attempting to
dissasemble it. Then try all 3 ARM variants, 16 bit, 32, and 64 as a
test. If these all fails, it's probably a data file. One file I used
*strings* on, turned out to just be a table of error messages, that
got loaded in the DSP6.

## [Radre2](https://rada.re/advent/09.html)

This tool is more focused on reverse engineering than the binutils, so
has additional features like decompiling and code analysis. One nice
feature is you can dynamically change the architecture, cpu, and bit
size, do a disassembly, and see if the generated code looks good. This
is a quick method for attempting to idenify what the blob is. It has
some simple graphics for code tracing that works in a terminal.

## [Binwalk](https://github.com/ReFirmLabs/binwalk)

Binwalk is good for unpacking blobs that are mix of multiple files of
varying formats. It doesn't always identify architectures very well,
but the unpacking is useful as some blobs are actually a collection of
things so you can get to the part you want.

# Graphical Tools

Most people these days don't work on the command line, so graphical
tools have been created. These often build on top of the command line
tools and are useful as they often combine multiple steps into a
single command.

## [Cutter](https://cutter.re/)

Cutter-re uses radre2 as it's backend, so much of the functionality is
the same. It's reasonably good at identifying the architecture. It has
a command line window so you can manually type in commands like you
would using radre2. It improves the graphing of the code execution
making it much easier to follow the code when it jumps to an
address. I find this useful when trying to determine if the generated
code is legit assembly.

Another useful feature is it optionally supports several
decompilers. Decompiling the assembly into pseudo code can be useful
to get an understanding of the code if you aren't super experienced
with the instruction set.

## [Ghidra](https://ghidra-sre.org/)

Ghidra is maintained by the US National Security Agency (NSA) and
supports many useful features for reerse engineering like decompiling
binaries. Unfortunately it isn't as good at identify the probable
architecture of the blob. For things like an ARM Cortex, ATMel AVR8,
etc... it fails to identify the file. There is a menu that lets you
specify the architecture when importing a file, but you need to have a
clue exactly what that probably is.

## Hexedit & Hexdump

These are simple graphical tools that look like a GUI on top of the
*od* utility. I don't often use either since I just use od.
