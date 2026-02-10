# Other Firmware

There are multiple subsystems on a device for the touchscreen, audio
support, and a varity of sensors. Not all of these have loadable
firmware. Some appear to only be data files. This is just a short list
identifying them, more reverse engineering would be required to really
know. These files are in the *vendor/firmware* directory.

## Driver Support

There is driver support for the various other subsystems in the
Qualcomm free software release, which is located here:
sm7635-modules/qcom/opensource/. 

* audio-kernel
* bt-kernel
* camera-kernel
* dsp-kernel
* eva-kernel
* graphics-kernel
* mm-sys-kernel
* securemsm-kernel
* spu-kernel
* synx-kernel

## Adreno GPU

This is the GPU that is used wiht the SnapDragon SoC. lf ve

* gen80300_sqe.fw
	* AARCH64 executable
* gen80300_gmu.bin
	* data file
* gen80300_zap.mbn
	* DSP5 Hexagon certificates

## Touchscreen

The FP6 uses an ESWIN EPH86XX for touchscreen support which appears to
have an embedded RISCV according to the datasheet.

* EPH86XX_fw.bin
	* This appears to be a data file.

## Camera

* CAMERA_ICP.b[0-9][0-9]
	* Tensilica Xtensa certificates  
* CAMERA_ICP.mbn
	* Tensilica Xtensa certificates

## Audio Amp

* aw882xx_acf.bin
	* Digital amp and codec

## Trusted Computing Platform

* vpu20_2v.mbn
	* Xtensa 32 Bit executable with certs for Trusted Boot

## Realtime Transport Protocol(RTP) Transport

This is used to stream audio and video, and appear to ber data files.

* haptic_ram.bin
* haptic_rtp_auto_sin.bin
* haptic_rtp.bin
