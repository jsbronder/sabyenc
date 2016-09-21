import _yenc
import sabyenc
import re
import time
import binascii
import sys

###################
# SUPPORT FUNCTIONS
###################

def yCheck(data):
    ybegin = None
    ypart = None
    yend = None

    # Check head
    for i in xrange(min(40, len(data))):
        try:
            if data[i].startswith('=ybegin '):
                splits = 3
                if data[i].find(' part=') > 0:
                    splits += 1
                if data[i].find(' total=') > 0:
                    splits += 1

                ybegin = ySplit(data[i], splits)

                if data[i + 1].startswith('=ypart '):
                    ypart = ySplit(data[i + 1])
                    data = data[i + 2:]
                    break
                else:
                    data = data[i + 1:]
                    break
        except IndexError:
            break

    # Check tail
    for i in xrange(-1, -11, -1):
        try:
            if data[i].startswith('=yend '):
                yend = ySplit(data[i])
                data = data[:i]
                break
        except IndexError:
            break

    return ((ybegin, ypart, yend), data)

# Example: =ybegin part=1 line=128 size=123 name=-=DUMMY=- abc.par
YSPLIT_RE = re.compile(r'([a-zA-Z0-9]+)=')
def ySplit(line, splits=None):
    fields = {}

    if splits:
        parts = YSPLIT_RE.split(line, splits)[1:]
    else:
        parts = YSPLIT_RE.split(line)[1:]

    if len(parts) % 2:
        return fields

    for i in range(0, len(parts), 2):
        key, value = parts[i], parts[i + 1]
        fields[key] = value.strip()

    return fields




###################
# Real test
###################

nr_runs = 2000
data_raw = open("test_noheader_n.txt", "rb").read()



###################
# YENC C - NEW
###################

# Time it!
time1_new = time.clock()
timet_new = 0.0
for i in xrange(nr_runs):
    time2 = time.clock()


    timet_new += time.clock()-time2

    # Different from homemade
    decoded_data_new, output_filename, crc, crc_yenc, crc_correct = sabyenc.decode_string_usenet(data_raw)


print "---"
time1_new_disp = 1000*(time.clock()-time1_new)
timet_new_disp = 1000*timet_new
print "%15s  took  %3d ms" % ("yEnc C New", time1_new_disp)
print "%15s  took  %3d ms = %d%%" % ("Base Python", timet_new_disp, 100*timet_new_disp/time1_new_disp)
print "---"




###################
# YENC C - Old
###################

# Time it!
time1 = time.clock()
timet = 0.0
for i in xrange(nr_runs):
    time2=time.clock()
    data = data_raw

    new_lines = data.split('\r\n')
    for i in xrange(len(new_lines)):
        if new_lines[i][:2] == '..':
            new_lines[i] = new_lines[i][1:]
    if new_lines[-1] == '.':
        new_lines = new_lines[1:-1]
    data = new_lines

    # Filter out empty ones
    data = filter(None, data)
    yenc, data = yCheck(data)
    ybegin, ypart, yend = yenc

    timet += time.clock()-time2

    # Different from homemade
    decoded_data, crc = _yenc.decode_string(''.join(data))[:2]
    partcrc = '%08X' % ((crc ^ -1) & 2 ** 32L - 1)

    if ypart:
        crcname = 'pcrc32'
    else:
        crcname = 'crc32'

    if crcname in yend:

        _partcrc = '0' * (8 - len(yend[crcname])) + yend[crcname].upper()
        #print _partcrc
    else:
        _partcrc = None
        print "Corrupt header detected => yend: %s" % yend
    if not _partcrc == partcrc:
        print 'shit'


print decoded_data_new == decoded_data
print len(decoded_data_new)


time1_disp = 1000*(time.clock()-time1)
timet_disp = 1000*timet
print "%15s  took  %3d ms   Diff %3d ms (%d%%)" % ("yEnc C Old", time1_disp, time1_disp-time1_new_disp, 100*(time1_disp-time1_new_disp)/time1_disp)
print "%15s  took  %3d ms   Diff %3d ms" % ("Base Python", timet_disp, timet_disp-timet_new_disp)
print "---"








###################
# YENC PYTHON
###################

# Time it!
time1 = time.clock()

YDEC_TRANS = ''.join([chr((i + 256 - 42) % 256) for i in xrange(256)])
for i in xrange(nr_runs):
    data = data_raw
    new_lines = data.split('\r\n')
    for i in xrange(len(new_lines)):
        if new_lines[i][:2] == '..':
            new_lines[i] = new_lines[i][1:]
    if new_lines[-1] == '.':
        new_lines = new_lines[1:-1]

    data = new_lines

    # Filter out empty ones
    data = filter(None, data)
    yenc, data = yCheck(data)
    ybegin, ypart, yend = yenc

    # Different from homemade
    data = ''.join(data)
    for i in (0, 9, 10, 13, 27, 32, 46, 61):
        j = '=%c' % (i + 64)
        data = data.replace(j, chr(i))
    decoded_data = data.translate(YDEC_TRANS)
    crc = binascii.crc32(decoded_data)
    partcrc = '%08X' % (crc & 2 ** 32L - 1)

    if ypart:
        crcname = 'pcrc32'
    else:
        crcname = 'crc32'

    if crcname in yend:
        _partcrc = '0' * (8 - len(yend[crcname])) + yend[crcname].upper()
    else:
        _partcrc = None
        print "Corrupt header detected => yend: %s" % yend

print "%15s took %d ms" % ("yEnc Python", 1000*(time.clock()-time1))

sys.exit()
###################
# YENC PYTHON 2
###################

# Time it!
time1 = time.clock()


for i in xrange(nr_runs*10):
    data = data_raw
    print data[-3:] == '.\r\n'

print "%15s took %d ms" % ("Python1", 1000*(time.clock()-time1))

for i in xrange(nr_runs*10):
    data = data_raw
    l = 0
    while 1:
        if data[l:l+2] == '\r\n':
            break
        l += 1

print "%15s took %d ms" % ("Python2", 1000*(time.clock()-time1))


