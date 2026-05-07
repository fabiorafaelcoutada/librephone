# Copy Engine

The CopyEngine is used to configure the data exchange between the
device driver and the blob. It is a bi-directional channel between the
host and target. The default configuration values are defined in the 
__ce_assignment.h__ header file, which is in the
**sm7635-modules/qcom/opensource/wlan/qca-wifi-host-cmn/hif/src/ce**
directory. This appears to be hardware, not software, as it uses
registers and can trigger interupts. This is only used for control
messages.

This is not used for the high throughput data exchange, that's in the
__HIF__ layer. This does configure how that high throughput data
exchange works by setting up the addresses used for DMA.

## Data Pipes

The WCN6750 supports 9 **pipes** used to configure the data
exchange. Other chipset variations support more or less pipes specific
to that hardware but work the same. The pipes are configuring using
two data structures, __host_ce_config_wlan_qca6750[]__ and
__target_ce_config_wlan_qca6750[]__. These are parsed into an array 
**pipe_info** that contains both.

For the WCN6750, here are the pipes:

* Pipe 0 - Host->Target HTC control + raw
* Pipe 1 - Target->Host HTT + HTC control
* Pipe 2 - Target->Host WMI
* Pipe 3 - Host->Target WMI (mac0)
* Pipe 4 - Host->Target HTT
* Pipe 5 - Pktlog/memcpy
* Pipe 6 - Pktlog/memcpy
* Pipe 7 - Pktlog/memcpy
* Pipe 8 - Pktlog/memcpy

## Configuration Process

The process of updating the configuration is as follows.

* Write command to the Control Register
* Lock the set of registers
* Write the two addresses
* Unlock the set of registers

The command packet is 16 bits, and starts with the how much memory is
to be allowcated, followed by the source address in the SoC, then
followed by the destiation address. This enables the executable in the
blob to utilize memory. There are then 2 bits that set the byte order. 
This also supports assigning pages of memory in a single
operation. The next 2 bits specifies whether to increment or decrement
the address for each page.
