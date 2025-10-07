DROP TYPE IF EXISTS public.cputypes CASCADE;
CREATE TYPE public.cputypes AS ENUM (
	'CORTEX',
	'KRYO',
	'EXPYNOS',
	'MEDIATEC'
);
DROP TYPE IF EXISTS public.gpumodels CASCADE;
CREATE TYPE public.gpumodels AS ENUM (
	'MALI',
	'ADRENO'
);
DROP TYPE IF EXISTS public.devstatus CASCADE;
CREATE TYPE public.devstatus AS ENUM (
	'UNKNOWN',
	'AVAILABLE',
	'DISCONTINUED'
);
DROP TYPE IF EXISTS public.imgtypes CASCADE;
CREATE TYPE public.imgtypes AS ENUM (
	'ELF64',
	'MBR',
	'BOOT',
	'DATA',
	'AVB0',
	'MSDOS',
	'SD',
	'DTB',
	'VNDRBOOT',
	'UNKNOWN'
);
DROP TYPE IF EXISTS public.filesystems CASCADE;
CREATE TYPE public.filesystems AS ENUM (
	'EXT2',
	'EXT3',
	'EXT4'
);
DROP TYPE IF EXISTS public.bintypes CASCADE;
CREATE TYPE public.bintypes AS ENUM (
	'ELF64',
	'MBR',
	'BOOT',
	'DATA',
	'AVB0',
	'MSDOS',
	'SD',
	'DTB',
	'GPU',
	'WIFI',
	'FINGERPRINT',
	'VNDRBOOT',
	'CAMERA',
	'RTPSTREAM',
	'CONFIG',
	'FIRMWARE',
	'FIRMWARE1',
	'FIRMWARE2',
	'FIRMWARE3',
	'NFC',
	'USB',
	'FIRMWARE5',
	'FIRMWARE6',
	'FIRMWARE7',
	'FIRMWARE8',
	'FIRMWARE9',
	'FIRMWARE10',
	'VIBRATION',
	'AUDIOAMP',
	'SECURITY',
	'SHADER',
	'BLUETOOTH',
	'WIFI_GPS_BLUETOOTH',
	'WIFI_BLUETOOTH',
	'AUDIO',
	'MEDIA',
	'ISOLATION',
	'OLED',
	'TOUCH',
	'GRAPHIC',
	'UNKNOWN',
	'TOUCHSCREEN',
	'TOUCHSCREEN1',
	'TOUCHSCREEN2',
	'TOUCHSCREEN3',
	'TOUCHSCREEN4',
	'TOUCHSCREEN5',
	'TOUCHSCREEN6',
	'CODEC',
	'CERT',
	'PROXIMITY',
	'STORAGE',
	'AI',
	'FASTCHG',
	'ESIM'
);
DROP TYPE IF EXISTS public.archtypes CASCADE;
CREATE TYPE public.archtypes AS ENUM (
	'UNKNOWN',
	'ARM64',
	'AARCH64',
	'RISCV',
	'WE32100',
	'XTENSA',
	'MIPS',
	'DSP'
);
DROP TYPE IF EXISTS public.celltypes CASCADE;
CREATE TYPE public.celltypes AS ENUM (
	'UNKNOWN',
	'GSM',
	'CDMA',
	'HSPA',
	'EVDO',
	'LTE',
	'FiveG'
);
DROP TYPE IF EXISTS public.nettypes CASCADE;
CREATE TYPE public.nettypes AS ENUM (
	'UNKNOWN',
	'TWOG',
	'THREEG',
	'FOURG',
	'FIVEG'
);
DROP TYPE IF EXISTS public.wifitypes CASCADE;
CREATE TYPE public.wifitypes AS ENUM (
	'UNKNOWN',
	'A',
	'B',
	'BE',
	'G',
	'N',
	'AC',
	'AX'
);
DROP TYPE IF EXISTS public.filetypes CASCADE;
CREATE TYPE public.filetypes AS ENUM (
	'BASH',
	'JAR',
	'APK',
	'LIBRARY',
	'TEXT',
	'KEY'
);
DROP TYPE IF EXISTS public.blobtypes CASCADE;
CREATE TYPE public.blobtypes AS ENUM (
	'DATA',
	'HEX',
	'LIBRARY'
);
