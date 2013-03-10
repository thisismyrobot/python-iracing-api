import mmap
import yaml # Requires PyYAML


MEMMAPFILE = 'Local\\IRSDKMemMapFileName'

TELEM_HEADER_LEN = 144
TELEM_HEADER_SIZE = 28

# How far into a header the name sits, and it's max length
TELEM_NAME_OFFSET = 16
TELEM_NAME_MAX_LEN = 32

class API(object):

    def __init__(self):
        self.mmp = mmap.mmap(0, 200000, MEMMAPFILE)
        self._telem_map, self._headers_offset = self.setup_telemetry()

    def telemetry(self, key):
        """ Return the data for a telemetry key.
        """
        self.mmp.seek(self._telem_map[key])
        return self.mmp.read(5)

    @property
    def yaml(self):
        """ Returns the YAML as a nested Python dict.
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

    def yaml_end(self):
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

    def setup_telemetry(self):
        telem_map = {}
        self.mmp.seek(self.yaml_end())

        dat = '\x00'
        while dat.strip() == '\x00':
            dat = self.mmp.read(1)

        # The actual start of the headers
        self.mmp.seek(self.mmp.tell() - 1)
        headers_offset = self.mmp.tell()

        while True:
            pos = self.mmp.tell() + TELEM_NAME_OFFSET
            line = self.mmp.read(TELEM_HEADER_LEN)
            name = line[TELEM_NAME_OFFSET:TELEM_NAME_OFFSET + TELEM_NAME_MAX_LEN].replace('\x00','')
            if name == '':
                break
            telem_map[name] = pos
        return telem_map, headers_offset


if __name__ == '__main__':
    
    api = API()
#    data, offset = session_data()
#    print data
#    print offset

#    telemetry(offset)

    import pdb; pdb.set_trace()
    