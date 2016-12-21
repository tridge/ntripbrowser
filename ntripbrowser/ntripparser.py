import re
from geopy.distance import vincenty
from urllib2 import urlopen

def get_nearest_point(obs_point, base_point):
    return vincenty(obs_point, base_point).kilometers

def read_data_from_url(url, port, timeout):
    if url.find("http") == -1:
        url = 'http://{}'.format(url)
    url = '{}:{}'.format(url, port)
    try:
        data = urlopen(url, timeout=timeout)
        sourcetable = data.read()
        data.close()
    except IOError:
        print "Socket error. Connection refused"
    else:
        return sourcetable

def get_mountpoints(url, port=2101, base_point=(0, 0), timeout=None):
    tables = NTRIP(read_data_from_url(url, port, timeout))
    for mountpoint in tables.str_data:
        mountpoint.distance = get_nearest_point(mountpoint.point, base_point)

    return tables.str_data

def get_table(url, port=2101, timeout=None, **kwargs):
    pass

class STR(object):

    def __init__(self, str_lines):

        self.STR_headers = ["Mountpoint", "ID", "Format", "Format Details",
            "Carrier", "Nav System", "Network", "Country", "Latitude",
            "Longitude", "NMEA", "Solution", "Generator", "Compr-Encrp",
            "Authentication", "Fee", "Bitrate", "Site"]

        self.data = dict(zip(self.STR_headers, str_lines))
        self.distance = None

    def __getitem__(self, value):
        try:
            return self.data[value]
        except KeyError:
            return ''

    def __str__(self):
        return str(self.data)

    @property
    def point(self):
        return (float(self.data["Latitude"]), 
            float(self.data["Longitude"]))

    @property
    def distance(self):
        return self.data["Distance"]
    
    @distance.setter
    def distance(self, value):
       self.data["Distance"] = value

    @property
    def table(self):
        return self.data

class CAS(object):

    def __init__(self, cas_lines):

        self.CAS_headers = ["Host","Port", "ID", "Operator",
            "NMEA", "Country", "Latitude", "Longitude",
            "Fallback Host", "Fallback Port", "Site"]
        
        if len(cas_lines) == 9:
            self.CAS_headers.pop(8)
            self.CAS_headers.pop(8)
        self.data = dict(zip(self.CAS_headers, cas_lines))
        print self.data

    def __str__(self):
        return str(self.data)

    def __getitem__(self, value):
        try:
            return self.data[value]
        except KeyError:
            return ''

class NET(object):

    def __init__(self, net_data):
        self.NET_headers = ["ID", "Operator", "Authentication",
            "Fee", "Web Net", "Web Str", "Web Reg",""]
        self.data = dict(zip(self.NET_headers, net_data))

    def __str__(self):
        return str(self.data)

    def __getitem__(self, value):
        try:
            return self.data[value]
        except KeyError:
            return ''

class NTRIPError(Exception):
    pass

class NTRIP(object):

    def __init__(self, sourcetable):

        self.sourcetable = None
        self.str_data = []
        self.cas_data = []
        self.net_data = []

        self.check_page_status(sourcetable)
        self.crop_sourcetable(sourcetable)
        self.parce_sourcetable()

    def check_page_status(self, sourcetable):
        status = re.search("(?<=SOURCETABLE )[0-9]+",sourcetable, re.MULTILINE).group(0)
        if status != '200':
            raise NTRIPError("Bad sourcetable")

    def crop_sourcetable(self, sourcetable):

        #TODO: refactoring
        CAS = sourcetable.find('CAS')
        NET = sourcetable.find('NET')
        STR = sourcetable.find('STR')
        first = CAS if (CAS != -1) else (NET if NET != -1 else STR)
        last = sourcetable.find('ENDSOURCETABLE')
        self.sourcetable = sourcetable[first:last]

    def parce_sourcetable(self):
        for NTRIP_data in self.sourcetable.split('\n'):
            NTRIP_data_list = NTRIP_data.split(';')
            if NTRIP_data_list[0] == 'STR':
                self.str_data.append(STR(NTRIP_data_list[1:]))
            if NTRIP_data_list[0] == 'CAS':
                self.cas_data.append(CAS(NTRIP_data_list[1:]))
            if NTRIP_data_list[0] == 'NET':
                self.net_data.append(NET(NTRIP_data_list[1:]))

if __name__ == '__main__':
    b = sorted(get_mountpoints("ntrip.emlid.com", base_point=(59.96032293, 30.33409)), key=lambda mnt: mnt.distance)
    for mnt in b:
        print("{:10} ({}): {:.4f} km".format(mnt["Mountpoint"], mnt['Format'], mnt.distance))
