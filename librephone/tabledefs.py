
import logging
from datetime import datetime
import librephone.typedefs
from shapely.geometry import Point, LineString, Polygon

log = logging.getLogger(__name__)

        
class DevicesTable(object):
    def __init__(self,
            version: float = None, vendor: str = None, model: str = None, build: str = None, blobs: dict = None, available: bool = False, builds: bool = False, extracts: bool = False, soc: str = None, released: int = None):
            self.data = {'version': version, 'vendor': vendor, 'model': model, 'build': build, 'blobs': blobs, 'available': available, 'builds': builds, 'extracts': extracts, 'soc': soc, 'released': released}

class SpecsTable(object):
    def __init__(self,
            release: datetime = '2025-09-23 13:45:00.570667', soc: str = None, cpus: str = None, peripherals: str = None, bluetooth: str = None, build: str = None, gpu: str = None, kernel: float = None):
            self.data = {'release': release, 'arch': arch, 'soc': soc, 'cpus': cpus, 'peripherals': peripherals, 'bluetooth': bluetooth, 'wifi': wifi, 'build': build, 'gpu': gpu, 'network': network, 'kernel': kernel}

class GsmarenaTable(object):
    def __init__(self,
            vendor: str = None, model: str = None, annnounced: str = None, chipset: str = None, cpu: str = None, sensors: str = None, wlan: str = None):
            self.data = {'vendor': vendor, 'model': model, 'annnounced': annnounced, 'chipset': chipset, 'cpu': cpu, 'sensors': sensors, 'wlan': wlan, 'status': status}
