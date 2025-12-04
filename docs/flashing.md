# Installing Lineage

If you've unlocked the bootloader, 

## Reboot into the bootloader

To install anything you first have to reboot into *fastboot* mode. 

	adb reboot bootloader

Once in fastboot mode, if you've built Lineage from source, execute
this at the top level of the source tree. This is the most efficient
way to update your ROM when you have to do this frequently.

	fastboot flashall

When this completes it'll automatically reboot.

## Recovery Mode

If you are installing from a zip file, then you need to boot into
recovery mode from fastboot mode.

	fastboot reboot recovery

Once in recovery mode you  get presented with a menu, choose *Apply
Update*, and then *Apply from ADB*.

	adb sideload [zipfile]

When this is completed, it'll drop you back to the recovery menu, and
select *Reboot*.
