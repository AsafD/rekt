import re
import os
import logging
import requests
import socket
import fcntl
import struct
import time
from sh import nmcli

wifi_re = re.compile(r'\s+wpa-ssid \"(.+)\"')


def iterfile(filename, offset):
    with open(filename, 'rb') as f:
        f.seek(offset)
        _attempts = 0

        while True:
            where = f.tell()
            d = f.read()

            if len(d) != 0:
                _attempts = 0
                yield d
            else:
                f.seek(where)

                if _attempts > 5:
                    logging.info('iterfile %s 0 new bytes after %d attempts, it is done', filename, _attempts)
                    break
                
                time.sleep(1)
                _attempts += 1 


def get_wifi_name(work_dir):
    for l in open(os.path.join(work_dir, 'config/wifi')).readlines():
        r = wifi_re.search(l)

        if r:
            return r.group(1)


def is_connected():
    try:
        return requests.get('http://mimosabox.com', timeout=0.5).status_code == 200
    except Exception:
        logging.exception('is connected')
        return False



def get_local_ip():
    for interface in 'wlan0', 'en0', 'lo0':
        try:
            return get_ip_address('wlan0')
        except IOError:
            pass
        

def get_username(work_dir):
    return open(os.path.join(work_dir, 'config/username')).read().strip()


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def scrolling_text(text, chars):
    while True:
        if len(text) <= chars:
            yield text
        else:
            yield text[:chars-1]
            text = text[1:] + text[0]


def get_session_and_ext(f):
	session_id, ext = os.path.splitext(f)

	return session_id, ext[1:]

def get_next_id():
    f = '/opt/rekt/_id'

    _id = int(open(f).read().strip())
    open(f, 'w').write(str(_id + 1))

    return _id


def get_connected_wifi():
    for device in nmcli('d'):
        if ' connected' in device.strip():
            return device.split()[3]
    else:
        return False


def connect_to_wifi(ssid, password):
    if get_connected_wifi():
        return

    try:
        nmcli('c', 'delete', ssid)
    except Exception:
        pass

    nmcli('d', 'wifi', 'connect', ssid, 'password', password)

def mkdir_if_not_exists(d):
    if not os.path.isdir(d):
        os.mkdir(d)

