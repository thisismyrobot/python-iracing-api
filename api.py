import mmap
import struct
import yaml # Requires PyYAML


MEMMAPFILE = 'Local\\IRSDKMemMapFileName'

HEADER_LEN = 144

# How far into a header the name sits, and it's max length
TELEM_NAME_OFFSET = 16
TELEM_NAME_MAX_LEN = 32

# There appears to be triple-buffering of data
VAL_BUFFERS = 3

# The mapping between the type integer in memory mapped file and Python's struct
TYPEMAP = ['c', '?', 'i', 'I', 'f', 'd']

class API(object):

    def __init__(self):
        self._var_types = None
        self._buffer_offsets = None
        self._sizes = None
        self._mmp = None
        self._var_offsets = None
        self._names = None

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

    def _get(self, position, type):
        """ Gets a value from the mmp, based on a position and struct var type.
        """
        size = struct.calcsize(type)
        self.mmp.seek(position)
        data = self.mmp.read(size)
        return struct.unpack(type, data)[0]

    @property
    def mmp(self):
        """ Create a memory map as big as allowed.
        """
        if self._mmp is None:
            size = 500000
            while True:
                try:
                    self._mmp = mmap.mmap(0, size, MEMMAPFILE)
                    size += 1
                except:
                    break
        return self._mmp

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
            self._buffer_offsets = [self._get(52 + (i * 16), 'i')
                                    for i
                                    in range(VAL_BUFFERS)]
        return self._buffer_offsets

    @property
    def names(self):
        """ The names of the telemetry variables, in order, cached.
            TODO: Make less clunky...
        """
        if self._names is None:
            self._names = []
            self.mmp.seek(self._telemetry_header_start)
            while True:
                pos = self.mmp.tell() + TELEM_NAME_OFFSET
                start = TELEM_NAME_OFFSET
                end = TELEM_NAME_OFFSET + TELEM_NAME_MAX_LEN
                header = self.mmp.read(HEADER_LEN)
                name = header[start:end].replace('\x00','')
                if name == '':
                    break
                self._names.append(name)
        return self._names

    @property
    def var_types(self):
        """ Set up the type map based on the headers, cache the results.
        """
        if self._var_types is None:
            self._var_types = {}
            for i, name in enumerate(self.names):
                type_loc = self._telemetry_header_start + (i * HEADER_LEN)
                self._var_types[name] = TYPEMAP[int(self._get(type_loc, 'i'))]
        return self._var_types

    @property
    def var_offsets(self):
        """ Find the offsets between the variables - used to find values in real
            time. Results are cached.
        """
        if self._var_offsets is None:
            self._var_offsets = {}
            offsets_seek = self._get(28, 'i')
            for i, name in enumerate(self.names):
                offset = self._get(offsets_seek + (i * HEADER_LEN) + 4, 'i')
                self._var_offsets[name] = offset
        return self._var_offsets

    def telemetry(self, key):
        """ Return the data for a telemetry key.
        """
        value_offset = self.var_offsets[key]
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