from ._module import _module
import re
import logging
import urllib.request
from hurry.filesize import size as filesize
import html.parser
import threading

class WorkerThread(threading.Thread):
    def __init__(self, module, target, url):
        super().__init__()
        self.module = module
        self.target = target
        self.url = url
    def run(self):
        r = urllib.request.urlopen(self.url)
        if not 'Content-Type' in r.headers:
            return
        content_type_header = [x.strip() for x in r.headers['Content-Type'].split(';')]
        mime_type = content_type_header[0]
        encoding = None
        for param in content_type_header[1:]:
            if param.startswith('charset='):
                encoding = param[param.index('=')+1:]
        try:
            logging.debug(mime_type)
            if mime_type == 'text/html':
                logging.debug(encoding)
                content = r.read(1024).decode(encoding or 'ascii')
                while not re.search('</title>', content, re.I):
                    _ = r.read(1024)
                    if not _:
                        break
                    content += _.decode(encoding or 'ascii')
                title = re.search(r'<title>(.+)</title>', content, re.S | re.I)
                if title:
                    title = title.groups(1)[0].strip()
                    h = html.parser.HTMLParser()
                    title = h.unescape(title)
                    self.module.privmsg(self.target, 'Title: {}'.format(title))
            elif mime_type.startswith('image/'):
                try:
                    size = get_image_size2(int(r.headers['Content-Length']), r)
                    self.module.privmsg(self.target, 'Image [{}]: dimensions {} x {}'.format(mime_type.split('/')[1], size[0], size[1]))
                except Exception as e:
                    print(e.msg)
            else:
                self.module.privmsg(self.target, 'Content type: {}, size: {}'.format(r.headers['Content-Type'], filesize(int(r.headers['Content-Length']))))
        except:
            logging.exception('Errorrr')
        finally:
            r.close()
        

class url_scanner(_module):
    def on_privmsg(self, source, target, message):
        m = re.search(r'(https?://\S+)', message)
        if m:
            url = m.groups(1)[0]
            self.privmsg(target, 'URL detected: {}'.format(url))
            WorkerThread(self, target, url).start()


# thank you https://github.com/scardine/image_size :)

import os
import struct

FILE_UNKNOWN = "Sorry, don't know how to get size for this file."

class UnknownImageFormat(Exception):
    pass

def get_image_size(file_path):
    """
    Return (width, height) for a given img file content - no external
    dependencies except the os and struct builtin modules
    """
    size = os.path.getsize(file_path)

    with open(file_path) as input:
        return get_image_size2(size, input)

def get_image_size2(size, input):
    height = -1
    width = -1
    msg = " raised while trying to decode as JPEG."

    data = input.read(2)
    if data.startswith(b'\377\330'):
        # JPEG
        b = input.read(1)
        try:
            while (b and ord(b) != 0xDA):
                while (ord(b) != 0xFF): b = input.read(1)
                while (ord(b) == 0xFF): b = input.read(1)
                if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                    input.read(3)
                    h, w = struct.unpack(">HH", input.read(4))
                    break
                else:
                    input.read(int(struct.unpack(">H", input.read(2))[0])-2)
                b = input.read(1)
            width = int(w)
            height = int(h)
        except struct.error:
            raise UnknownImageFormat("StructError" + msg)
        except ValueError:
            raise UnknownImageFormat("ValueError" + msg)
        except Exception as e:
            raise UnknownImageFormat(e.__class__.__name__ + msg)
        return width, height

    data += input.read(23)

    if (size >= 10) and data[:6] in (b'GIF87a', b'GIF89a'):
        # GIFs
        w, h = struct.unpack("<HH", data[6:10])
        width = int(w)
        height = int(h)
    elif ((size >= 24) and data.startswith(b'\211PNG\r\n\032\n')
          and (data[12:16] == b'IHDR')):
        # PNGs
        w, h = struct.unpack(">LL", data[16:24])
        width = int(w)
        height = int(h)
    elif (size >= 16) and data.startswith(b'\211PNG\r\n\032\n'):
        # older PNGs
        w, h = struct.unpack(">LL", data[8:16])
        width = int(w)
        height = int(h)
    else:
        raise UnknownImageFormat(FILE_UNKNOWN)

    return width, height