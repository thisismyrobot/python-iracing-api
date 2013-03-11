import mmap
import struct
import yaml # Requires PyYAML


MEMMAPFILE = 'Local\\IRSDKMemMapFileName'

TELEM_HEADER_LEN = 144
TELEM_HEADER_SIZE = 28

# How far into a header the name sits, and it's max length
TELEM_NAME_OFFSET = 16
TELEM_NAME_MAX_LEN = 32

VAL_BUFFERS = 3

TYPEMAP = ['c', '?', 'i', 'I', 'f', 'd']

VALOFFSETS = {
    'SessionTime':0,
    'SessionNum':8,
    'SessionState':12,
    'SessionUniqueID':16,
    'SessionFlags':20,
    'SessionTimeRemain':24,
    'SessionLapsRemain':32,
    'RadioTransmitCarIdx':36,
    'DriverMarker':40,
    'IsReplayPlaying':41,
    'ReplayFrameNum':42,
    'ReplayFrameNumEnd':46,
    'CarIdxLap':50,
    'CarIdxLapDistPct':306,
    'CarIdxTrackSurface':562,
    'CarIdxOnPitRoad':818,
    'OnPitRoad':882,
    'CarIdxSteer':883,
    'CarIdxRPM':1139,
    'CarIdxGear':1395,
    'SteeringWheelAngle':1651,
    'Throttle':1655,
    'Brake':1659,
    'Clutch':1663,
    'Gear':1667,
    'RPM':1671,
    'Lap':1675,
    'LapDist':1679,
    'LapDistPct':1683,
    'RaceLaps':1687,
    'LapBestLap':1691,
    'LapBestLapTime':1695,
    'LapLastLapTime':1699,
    'LapCurrentLapTime':1703,
    'LapDeltaToBestLap':1707,
    'LapDeltaToBestLap_DD':1711,
    'LapDeltaToBestLap_OK':1715,
    'LapDeltaToOptimalLap':1716,
    'LapDeltaToOptimalLap_DD':1720,
    'LapDeltaToOptimalLap_OK':1724,
    'LapDeltaToSessionBestLap':1725,
    'LapDeltaToSessionBestLap_DD':1729,
    'LapDeltaToSessionBestLap_OK':1733,
    'LapDeltaToSessionOptimalLap':1734,
    'LapDeltaToSessionOptimalLap_DD':1738,
    'LapDeltaToSessionOptimalLap_OK':1742,
    'LongAccel':1743,
    'LatAccel':1747,
    'VertAccel':1751,
    'RollRate':1755,
    'PitchRate':1759,
    'YawRate':1763,
    'Speed':1767,
    'VelocityX':1771,
    'VelocityY':1775,
    'VelocityZ':1779,
    'Yaw':1783,
    'Pitch':1787,
    'Roll':1791,
    'PitRepairLeft':1795,
    'PitOptRepairLeft':1799,
    'CamCarIdx':1803,
    'CamCameraNumber':1807,
    'CamGroupNumber':1811,
    'CamCameraState':1815,
    'IsOnTrack':1819,
    'IsInGarage':1820,
    'SteeringWheelTorque':1821,
    'SteeringWheelPctTorque':1825,
    'ShiftIndicatorPct':1829,
    'ShiftPowerPct':1833,
    'ShiftGrindRPM':1837,
    'EngineWarnings':1841,
    'FuelLevel':1845,
    'FuelLevelPct':1849,
    'ReplayPlaySpeed':1853,
    'ReplayPlaySlowMotion':1857,
    'ReplaySessionTime':1858,
    'ReplaySessionNum':1866,
    'WaterTemp':1870,
    'WaterLevel':1874,
    'FuelPress':1878,
    'OilTemp':1882,
    'OilPress':1886,
    'OilLevel':1890,
    'Voltage':1894,
    'ManifoldPress':1898,
    'RRshockDefl':1902,
    'LRshockDefl':1906,
    'RFshockDefl':1910,
    'LFshockDefl':1914,
}


class API(object):

    def __init__(self):
        self._var_types = self._buffer_offsets = self._sizes = None

        # Find max memory map size
        size = 500000
        while True:
            try:
                self.mmp = mmap.mmap(0, size, MEMMAPFILE)
                size += 1
            except:
                break

    @property
    def _telemetry_header_start(self):
        """ Returns the index of the telemetry header, searching from the end of
            the yaml.
        """
        self.mmp.seek(self._yaml_end)
        dat = '\x00'
        while dat.strip() == '\x00':
            dat = self.mmp.read(1)
        return self.mmp.tell() - 1

    @property
    def _yaml_end(self):
        """ Returns the index of the end of the YAML in memory.
        """
        self.mmp.seek(0)
        offset = 0
        headers = self.mmp.readline()
        while True:
            line = self.mmp.readline()
            if line.strip() == '...':
                break
            else:
                offset += len(line)
        return offset + len(headers) + 4

    @property
    def sizes(self):
        """ Find the size for each variable, cache the results.
        """
        if self._sizes is None:
            self._sizes = {}
            for key, var_type in self.var_types.items():
                self._sizes[key] = struct.calcsize(var_type)
        return self._sizes

    @property
    def buffer_offsets(self):
        """ Find the offsets for the value array(s), cache the result.
        """
        if self._buffer_offsets is None:
            self._buffer_offsets = []
            for i in range(VAL_BUFFERS):
                seek = 52 + (i * 16)
                self.mmp.seek(seek)
                data = self.mmp.read(4)
                offset = struct.unpack('i', data)[0]
                self._buffer_offsets.append(offset)
        return self._buffer_offsets

    @property
    def var_types(self):
        """ Set up the type map based on the headers, cache the results.
        """
        if self._var_types is None:
            self._var_types = {}
            self.mmp.seek(self._telemetry_header_start)
            while True:
                pos = self.mmp.tell() + TELEM_NAME_OFFSET
                start = TELEM_NAME_OFFSET
                end = TELEM_NAME_OFFSET + TELEM_NAME_MAX_LEN
                header = self.mmp.read(TELEM_HEADER_LEN)
                name = header[start:end].replace('\x00','')
                if name == '':
                    break
                var_type = TYPEMAP[int(struct.unpack('i', header[0:4])[0])]
                self._var_types[name] = var_type
        return self._var_types

    def telemetry(self, key):
        """ Return the data for a telemetry key.
        """
        value_offset = VALOFFSETS[key]
        for buffer_offset in self.buffer_offsets:
            self.mmp.seek(value_offset + buffer_offset)
            data = self.mmp.read(self.sizes[key])
            if len(data.replace('\x00','')) != 0:
                return struct.unpack(self.var_types[key], data)[0]

    @property
    def yaml(self):
        """ Returns the YAML as a nested Python dict.
            TODO: flatten dict, provide key-based accessor method.
        """
        ymltxt = ''
        self.mmp.seek(0)
        headers = self.mmp.readline()
        while True:
            line = self.mmp.readline()
            if line.strip() == '...':
                break
            else:
                ymltxt += line
        return yaml.load(ymltxt, Loader=yaml.CLoader)


if __name__ == '__main__':
    """ Simple test harness.
    """
    import time
    api = API()
    
    while True:
        print '{0} Gear, {1} m/s, {2} m/s/s'.format(api.telemetry('Gear'),
                                                    api.telemetry('Speed'),
                                                    api.telemetry('LatAccel'))
        time.sleep(1)