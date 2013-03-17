""" Benchmarker.

    Current results on my (mid performance) machine:

        Press any key to begin telemetry access benchmark...
        Setting up...
        Attempting to read current all telemetry keys 10000 times each... Done!
        10000 reads of all keys executed in 6.1890001297 seconds
        Read rate for all 91 telementry values is: 1615.7698805 Hz
        Read rate for a single telementry value is: 147035.059126 Hz

"""

import api
import time


ITER = 10000

print "Press any key to begin telemetry access benchmark...",
raw_input()

print "Setting up..."

client = api.API()
client['Speed']
keys = client._telemetry_names

print "Attempting to read current all telemetry keys {0} times each...".format(ITER),

start = time.time()

for i in range(ITER):
    for k in keys:
        _ = client[k]

end = time.time()
duration = end - start

all_telem_hz = 1 / (duration / ITER)
telem_hz = all_telem_hz * len(keys)

print "Done!"
print "{0} reads of all keys executed in {1} seconds".format(ITER, duration)
print "Read rate for all {0} telementry values is: {1} Hz".format(len(keys),
                                                                  all_telem_hz)
print "Read rate for a single telementry value is: {0} Hz".format(telem_hz)