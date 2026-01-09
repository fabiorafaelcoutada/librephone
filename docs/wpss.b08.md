# wpss.b08

This file contains no data, but appears to be a legit 32bit ELF
file, supposedly for an x86,  but I think this is mis-identified. The
only symbols in the ELF are these:

* 4ff40000 D _binary_padded_pcss_m3_tx_rx_bin_end
* 00040000 A _binary_padded_pcss_m3_tx_rx_bin_size
* 4ff00000 D _binary_padded_pcss_m3_tx_rx_bin_start
* 00000401 A _start

I think this is just a data file that is initially empty, but gets
populated by the code at runtime. Usually if I see __tx_rx__ in a
symbol it's something used for exchanging data. Since I know there is
a CE shared memory channel used to communicate between the driver and
the blob, I assume this is that buffer. That would also explain why it
contains no data.

## The ELF Header

	Magic:   7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00 
	Class:                             ELF32
	Data:                              2's complement, little endian
	Version:                           1 (current)
	OS/ABI:                            UNIX - System V
	ABI Version:                       0
	Type:                              EXEC (Executable file)
	Machine:                           Intel 80386
	Version:                           0x1
	Entry point address:               0x401
	Start of program headers:          52 (bytes into file)
	Start of section headers:          266484 (bytes into file)
	Flags:                             0x0
	Size of this header:               52 (bytes)
	Size of program headers:           32 (bytes)
	Number of program headers:         1
	Size of section headers:           40 (bytes)
	Number of section headers:         5
	Section header string table index: 2
	
