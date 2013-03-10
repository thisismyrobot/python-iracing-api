import mmap
import yaml # Requires PyYAML


MEMMAPFILE = 'Local\\IRSDKMemMapFileName'

TELEM_HEADER_LEN = 144
TELEM_HEADER_SIZE = 28

# How far into a header the name sits, and it's max length
TELEM_NAME_OFFSET = 16
TELEM_NAME_MAX_LEN = 32

def session_data():
    ymltxt = ''
    mmp = mmap.mmap(0, 10000, MEMMAPFILE)
    headers = mmp.readline()
    while True:
        line = mmp.readline()
        if line.strip() == '...':
            break
        else:
            ymltxt += line
    return (yaml.load(ymltxt, Loader=yaml.CLoader),
            len(ymltxt) + len(headers) + 4)


def telemetry(offset):
    mmp = mmap.mmap(0, 200000, MEMMAPFILE)
    mmp.seek(offset)

    dat = '\x00'
    while dat.strip() == '\x00':
        dat = mmp.read(1)

    # The actual start of the headers
    mmp.seek(mmp.tell() - 1)

    while True:
        line = mmp.read(TELEM_HEADER_LEN)
        name = line[TELEM_NAME_OFFSET:TELEM_NAME_OFFSET + TELEM_NAME_MAX_LEN].replace('\x00','')
        if name == '':
            break
        print name


if __name__ == '__main__':
    
    data, offset = session_data()
#    print data
    print offset

    telemetry(offset)

#    import pdb; pdb.set_trace()
    