# -*- coding: utf-8 -*-print type(title)
import os, sys
import time, random
import urllib2
import cookielib
import zipfile 
import lxml.html

class Page:
  def __init__(self, url = None, fname = None, title = None, index = 0):
    self.url  = url
    self.fname  = fname
    self.title  = title
    self.imgUrl = []
    self.fsize  = 0
    self.status = False
    self.index  = index

  def parse(self):
    h = lxml.html.parse(self.url)
    
    try:
      attr = h.xpath('//iframe[last()]/following::div[1]/text()')[0].replace(' ','').strip().split('::')
      self.fname = attr[0]
      self.fsize = int(float(attr[2].rstrip('KB')))
      self.imgUrl = h.xpath('//iframe[1]/following::img[@style]/@src')[0]
    except:
      print 'parse url error'
     
  def download(self):
    print "Download p%d: %s " % (self.index+1, self.fname),

    try:
      abs_filename = self.title + os.sep + self.fname
      u = openRawStream(self.imgUrl, self.url)
      data = u.read()

      file = open( abs_filename ,'w+b')
      file.write(data)
      file.close()

      if abs( os.path.getsize(abs_filename)/1024 - self.fsize) > 5:
        os.remove(abs_filename)
        raise ValueError
      else:  
        print "Done"
        self.statue = True
        return 0

    except KeyboardInterrupt:
      exit(0)
    except ValueError:
      print "509 bandwidth exceeded"
      exit(0)
      time.sleep( random.uniform(5, 10))
      return 509
    except:
      print "unknown exception"
      return 999

  def checkStatus(self):
    if os.path.exists(self.title + os.sep + self.fname):
      self.status = True
    
    return self.status


  def run(self):
    if self.checkStatus():
      return 0

    self.parse()
    return self.download()

class Title:
  def __init__(self, url = None):
    self.url   = url
    self.pages = []
    self.title = []
    self.numPages = 0
    self.status = False
    self.logFilename = 'link.html'

  def parse(self):
    # parse thumbnail gallery for all page links and filename
    url_parse = self.url.lstrip('http://').lstrip('g.e-hentai.org/g/').split('/')
    thumbnailUrl = 'http://g.e-hentai.org/codegen.php?gid='+url_parse[0]+'&t='+url_parse[1]+'&s=1-m-y&type=html'
    h = lxml.html.parse(thumbnailUrl)

    all_links = h.xpath('//table[last()]//a/@href')
    all_filenames = h.xpath('//table[last()]//a/img/@alt')

    self.numPages = len(all_links)

    # parse title page for possible Chinese/Japanese title
    u = openStream(self.url)
    aa = lxml.html.fromstring(u)
    if len( aa.xpath('//h1[@id="gj"]/text()') ) > 0:
      t = aa.xpath('//h1[@id="gj"]/text()')[0] 
    else:
      t = aa.xpath('//h1[@id="gn"]/text()')[0] 

    # substitute all restriced filename
    subs = ['\\', '/', '?', '%', '*', ':', '|', '"', '<', '>', '.']
    for char in subs:
      t = t.replace(char, '-')

    self.title = t

    for i in range(self.numPages):
      self.pages.append(Page(all_links[i], all_filenames[i], self.title, i))

  def checkStatus(self):
    if os.path.exists(self.title + '.zip'):
      self.status = True
    
    return self.status

  def download(self):
    print ' '

    try:
      print self.title + '  p' + str(self.numPages)
    except:
      print "Title can't be display in console"

    if self.checkStatus():
      print 'already downloaded and compressed'
    else:
      if not os.path.isdir(self.title):
         os.mkdir(self.title)
        
      numFailPages = 0
      for i in range(self.numPages):
        HttpResponse = self.pages[i].run()
        if HttpResponse > 0:
          numFailPages += 1

      # if download error, write log and original link
      if numFailPages == 0:
        self.compressTitle()
        self.status = True
      else:
        self.writeLog()

  def run(self):
    self.parse()
    self.download()

  def compressTitle(self):
    print 'Download complete, Compressing...',

    if os.path.exists(self.title + os.sep + self.logFilename):
      os.remove(self.title + os.sep + self.logFilename)

    zz = zipfile.ZipFile(self.title + '.zip', mode='w', compression = zipfile.ZIP_DEFLATED)
    for file in os.listdir(self.title):
      zz.write(self.title + os.sep + file)
    zz.close()

    for file in os.listdir(self.title):
      os.remove(self.title + os.sep + file)
    os.rmdir(self.title)

    print 'Done'

  def writeLog(self):
    fp = open( self.title + os.sep + self.logFilename, 'w')
    fp.write('<html><head><title>Download Failed Links</title></head><body>\n')
    for i in range(self.numPages):
      if self.pages[i].status == False:
        fp.write('<a href=\"' + self.pages[i].url + '\">' + self.pages[i].url + '</a><br/>\n')
    fp.write('</body></html>')
    fp.close()

# ungzip raw stream
def ungzip(data):
  from io import BytesIO
  import gzip

  buf = BytesIO( data )
  unziped = gzip.GzipFile('whatever',mode='rb', fileobj=buf)
  return unziped.read()

# urlopen here, many need spoof 
def openRawStream(url, upper_url = None):
  Cookies = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(Cookies))
  opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11')]

  # cheat .php
  if upper_url != None:
    opener.addheaders = [('Referer', upper_url )]

  u = opener.open(url)
  opener.close()
  return u

# open text stream
def openStream(url):
  u = openRawStream(url)
  data = u.read()
  charset = u.info().getparam('charset')

  # only if html is gziped u.info() has Content-Encoding attributte
  try:
    encode = u.info()['Content-Encoding']
  except KeyError:
    encode = None

  if encode == 'gzip':
    data = ungzip(data)

  u.close()

  return data.decode(charset)

# test if file exist, HTML may mistake .jpg to .png
# so test all tree common format
def file_exist(title, filename):
  exts = ['.jpg', '.png', '.gif']
  original = '.' + filename.split('.')[-1]
  
  for ext in exts:
    if os.path.exists(title + os.sep + filename.replace(original,ext)):
      return True

  return False

if __name__=='__main__':
  if not len(sys.argv) == 2:
    print 'EHDL [URL]  or   EHDL [filename], each line in [filename] is comic URL'
  else:
    if 'http://' in sys.argv[1]:
      title = Title(sys.argv[1])
      title.run()
    else:
      while True:
        titles = []         # list of title object
        numFailTitles = 0

        fp = open(sys.argv[1], 'r')
        titleUrls = fp.read().splitlines()
        fp.close()

        for url in titleUrls:
          url = url.split('#')[0].rstrip()  # extract title URL
          titles.append(Title(url))

        for i in range(len(titles)):
          titles[i].run()

        fp = open(sys.argv[1], 'w')
        for i in range(len(titles)):
          if titles[i].status == False:
            numFailTitles += 1
            fp.write(titles[i].url+' # ' + titles[i].title + '\n')
        fp.close()

        if numFailTitles == 0:
          break
