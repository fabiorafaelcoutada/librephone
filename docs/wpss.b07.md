# wpss.b07

This file seems to be a RISCV32, several tools identify it as
such. One tool claims it's FPU code. The *objdump* program does
dissasemble it. Some of the generated code looks like good RISCV
assembly, but it has blocks that look like total garbage. It's
possible those blocks are data. Once objdump identifies it as a
RISCV32 binary, once dissasembly starts it can't differentiate between
the actual code and embedded data.

