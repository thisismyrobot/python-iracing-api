import mmap
import struct
import yaml # Requires PyYAML


MEMMAPFILE = 'Local\\IRSDKMemMapFileName'
MEMMAPFILESIZE = 798720 # Hopefully this is fairly static...

HEADER_LEN = 144

# How far into a header the name sits, and its max length
TELEM_NAME_OFFSET = 16
TELEM_NAME_MAX_LEN = 32

# There appears to be triple-buffering of data
VAL_BUFFERS = 3

# The mapping between the type integer in memory mapped file and Python's struct
TYPEMAP = ['c', '?', 'i', 'I', 'f', 'd']

class API(object):
    """ A basic read-only iRacing Session and Telemetry API client.
    """
    def __init__(self):
        """ Sets up a lot of internal variables, they are populated when first
            accessed by their non underscore-prepended versions. This makes the
            first access to a method like telemetry() slower, but massively
            tidies up the codebase.
        """
        self._var_types = None
        self._buffer_offsets = None
        self._sizes = None
        self._mmp = None
        self._var_offsets = None
        self._names = None
        self._telemetry_header_start = None
        self._yaml_end = None

    @property
    def telemetry_header_start(self):
        """ Returns the index of the telemetry header, searching from the end of
            the yaml. Cached.
        """
        if self._telemetry_header_start is None:
            self.mmp.seek(self.yaml_end)
            dat = '\x00'
            while dat.strip() == '\x00':
                dat = self.mmp.read(1)
            self._telemetry_header_start = self.mmp.tell() - 1
        return self._telemetry_header_start

    @property
    def yaml_end(self):
        """ Returns the index of the end of the YAML in memory, cached.
        """
        if self._yaml_end is None:
            self.mmp.seek(0)
            offset = 0
            headers = self.mmp.readline()
            while True:
                line = self.mmp.readline()
                if line.strip() == '...':
                    break
                else:
                    offset += len(line)
            self._yaml_end = offset + len(headers) + 4
        return self._yaml_end


    @property
    def mmp(self):
        """ Create the memory map.
        """
        if self._mmp is None:
            self._mmp = mmap.mmap(0, MEMMAPFILESIZE, MEMMAPFILE,
                                  access=mmap.ACCESS_READ)
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
            self.mmp.seek(self.telemetry_header_start)
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
                type_loc = self.telemetry_header_start + (i * HEADER_LEN)
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

    def _get(self, position, type):
        """ Gets a value from the mmp, based on a position and struct var type.
        """
        size = struct.calcsize(type)
        val = struct.unpack(type, self.mmp[position:position + size])[0]
        if val is None:
            val = 0
        return val

    def telemetry(self, key):
        """ Return the data for a telemetry key. There are three buffers and
            this returns the first one with a valid value.

            TODO: Use the "tick" indicator to show which one to use instead of
            this brute-force method.
        """
        val_o = self.var_offsets[key]
        for buf_o in self.buffer_offsets:
            data = self.mmp[val_o + buf_o: val_o + buf_o + self.sizes[key]]
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

    def splat(self):
        """ Helper method to dump all the fast and slow data as a dict.
        """
        yamldict = self.yaml
        for name in self.names:
            yamldict[name] = self.telemetry(name)
        return yamldict


if __name__ == '__main__':
    """ Simple test usage.
    """
    api = API()
    print api.splat()
