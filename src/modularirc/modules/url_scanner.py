import re
import logging
from hurry.filesize import size as filesize
import html.parser
import threading
import requests

from modularirc import BaseModule


class WorkerThread(threading.Thread):
    def __init__(self, module, source, target, url):
        super().__init__()
        self.module = module
        self.source = source
        self.target = target
        self.url = url
    def run(self):
        try:
            r = requests.get(self.url, stream=True)
        except:
            logging.exception('Exception in url_scanner')
            return

        mime_type = None
        encoding = None
        if 'Content-Type' in r.headers:
            content_type_header = [x.strip() for x in r.headers['Content-Type'].split(';')]
            mime_type = content_type_header[0]
            for param in content_type_header[1:]:
                if param.startswith('charset='):
                    encoding = param[param.index('=')+1:]
        else:
            mime_type = 'unknown/unknown'

        try:
            logging.debug(mime_type)
            if mime_type == 'text/html':
                logging.debug(encoding)
                response_content = ''
                for content in r.iter_content(1024):
                    response_content += content.decode(encoding or 'ascii', errors='ignore')
                    if '</title>' in response_content:
                        break
                    elif '</head>' in response_content: # don't bother going on when <head> ends
                        break
                title = re.search(r'<title>(.+)</title>', response_content, re.S | re.I)
                if title:
                    title = title.groups(1)[0].strip()
                    h = html.parser.HTMLParser()
                    title = h.unescape(title)
                    self.reply('Title: {}'.format(title))
                else:
                    self.reply('No title found on page...')
            elif mime_type.startswith('image/'):
                try:
                    size = get_image_size2(int(r.headers['Content-Length']), r.raw)
                    self.reply('Image [{}]: dimensions {} x {}'.format(mime_type.split('/')[1], size[0], size[1]))
                except Exception as e:
                    self.reply('Image [{}]: unknown size'.format(mime_type))
                    logging.exception('Failed to determine image size')
            else:
                self.reply('Content type: "{}", size: "{}"'.format(r.headers['Content-Type'], filesize(int(r.headers['Content-Length']))))
        except:
            self.reply('Exception in reading response content.')
            logging.exception('Exception in reading response content')
        finally:
            r.close()
    def reply(self, message):
        self.module.notice(self.target, '{}: {}'.format(self.source, message))


class Module(BaseModule):
    def on_privmsg(self, source, target, message):
        m = re.search(r'(https?://\S+)', message)
        if m:
            url = m.groups(1)[0]
            #self.notice(target, 'URL detected: {}'.format(url))
            WorkerThread(self, source, target, url).start()


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