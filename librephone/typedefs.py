import logging
from enum import Enum
class Cputypes(Enum):
	CORTEX = 'CORTEX'
	KRYO = 'KRYO'
	EXPYNOS = 'EXPYNOS'
	MEDIATEC = 'MEDIATEC'

class Gpumodels(Enum):
	MALI = 'MALI'
	ADRENO = 'ADRENO'

class Devstatus(Enum):
	AVAILABLE = 'AVAILABLE'
	DISCONTINUED = 'DISCONTINUED'

class Imgtypes(Enum):
	ELF64 = 'ELF64'
	MBR = 'MBR'
	BOOT = 'BOOT'
	DATA = 'DATA'
	AVB0 = 'AVB0'
	MSDOS = 'MSDOS'
	SD = 'SD'
	DTB = 'DTB'
	VNDRBOOT = 'VNDRBOOT'
	UNKNOWN = 'UNKNOWN'

class Filesystems(Enum):
	EXT2 = 'EXT2'
	EXT3 = 'EXT3'
	EXT4 = 'EXT4'

class Bintypes(Enum):
	CAMERA = 'CAMERA'
	RTPSTREAM = 'RTPSTREAM'
	CONFIG = 'CONFIG'
	FIRMWARE = 'FIRMWARE'
	FIRMWARE1 = 'FIRMWARE1'
	FIRMWARE2 = 'FIRMWARE2'
	FIRMWARE3 = 'FIRMWARE3'
	FIRMWARE4 = 'FIRMWARE4'
	FIRMWARE5 = 'FIRMWARE5'
	FIRMWARE6 = 'FIRMWARE6'
	FIRMWARE7 = 'FIRMWARE7'
	FIRMWARE8 = 'FIRMWARE8'
	FIRMWARE9 = 'FIRMWARE9'
	FIRMWARE10 = 'FIRMWARE10'

class Archtypes(Enum):
	ARM64 = 'ARM64'
	AARCH64 = 'AARCH64'
	RISCV = 'RISCV'
	WE32100 = 'WE32100'
	XTENSA = 'XTENSA'
	MIPS = 'MIPS'
	DSP = 'DSP'

class Celltypes(Enum):
	GSM = 'GSM'
	CDMA = 'CDMA'
	HSPA = 'HSPA'
	EVDO = 'EVDO'
	LTE = 'LTE'
	FiveG = 'FiveG'

class Nettypes(Enum):
	TWOG = 'TWOG'
	THREEG = 'THREEG'
	FOURG = 'FOURG'
	FIVEG = 'FIVEG'

class Wifitypes(Enum):
	A = 'A'
	B = 'B'
	BE = 'BE'
	G = 'G'
	N = 'N'
	AC = 'AC'
	AX = 'AX'

class Filetypes(Enum):
	BASH = 'BASH'
	JAR = 'JAR'
	APK = 'APK'
	LIBRARY = 'LIBRARY'
	TEXT = 'TEXT'
	KEY = 'KEY'

class Blobtypes(Enum):
	DATA = 'DATA'
	HEX = 'HEX'
	LIBRARY = 'LIBRARY'

