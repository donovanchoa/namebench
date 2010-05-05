# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Class used for connecting to the results site."""

import os
import platform
import sys
import tempfile
import urllib
import zlib

# external dependencies (from third_party)
try:
  import third_party
except ImportError:
  pass

import httplib2
import simplejson

class SiteConnector(object):
  
  def __init__(self, config):
    self.config = config
    
  def GetGeoIPData(self, ip):
    h = httplib2.Http(tempfile.gettempdir(), timeout=10)
    post_data = dict(ip=ip)
    resp, content = h.request(url, 'POST', urllib.urlencode(post_data))
    return simplejson.loads(content)

  def GetIndexHosts(self):
    url = self.config.site_url + '/index_hosts'
    h = httplib2.Http(tempfile.gettempdir(), timeout=10)
    content = None
    try:
      resp, content = h.request(url, 'GET')
      hosts = []
      for record_type, host in simplejson.loads(content):
        hosts.append((str(record_type), str(host)))
      return hosts
    except (IndexError, AttributeError):
      print '* Unable to fetch %s' % url
      return []
    except simplejson.decoder.JSONDecodeError:
      print '* Failed to decode: "%s"' % content
      return []

  def UploadJsonResults(self, json_data):
    """Data is generated by reporter.CreateJsonData"""
    
    url = self.config.site_url + '/submit'
    if not url or not url.startswith('http'):
      return False
    h = httplib2.Http()
    post_data = dict(duplicate_check=self._CalculateDuplicateCheckId(), data=json_data)
    try:
      resp, content = h.request(url, 'POST', urllib.urlencode(post_data))
      print "RESPONSE: [%s]: %s" % (resp, content)
      return True
    # See http://code.google.com/p/httplib2/issues/detail?id=62
    except AttributeError:
      print "%s refused connection" % url
    return False

  def _CalculateDuplicateCheckId(self):
    """This is so that we can detect duplicate submissions from a particular host.

    Returns:
      checksum: integer
    """
    # From http://docs.python.org/release/2.5.2/lib/module-zlib.html
    # "not suitable for use as a general hash algorithm."
    #
    # We are only using it as a temporary way to detect duplicate runs on the
    # same host in a short time period, so it's accuracy is not important.
    return zlib.crc32(platform.platform() + sys.version + platform.node() +
                      os.getenv('HOME', '') + os.getenv('USERPROFILE', ''))