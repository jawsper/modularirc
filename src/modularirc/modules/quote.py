import glob
import os
import logging
import random

from modularirc import BaseModule


class Module(BaseModule):
    def cmd_quote(self, **kwargs):
        """!quote: to get a random quote"""
        quote = self.random_quote()
        if quote:
            return [quote]

    def random_quote(self):
        """Read a quote from a text file"""
        try:
            quote_dir = self.get_config('path')
        except:
            return 'Error: path not set'
        try:
            files = glob.glob(os.path.join(quote_dir, '*.txt'))
            quotes = []
            for filename in files:
                with open(filename, 'rt', encoding='utf-8') as f:
                    quotes.extend(f.readlines())
            return random.choice(quotes)
        except IOError as e:
            logging.exception('Quote IOError')
            return 'Error: quote file not found: {}'.format(e)
        except:
            logging.exception('Quote Exception')
            return 'Error: no quote file defined'
