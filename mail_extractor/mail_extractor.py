#!/usr/bin/python3

import email
import sys
import os
import argparse
import textwrap
from email.header import decode_header
from email.parser import BytesParser

def make_utf8_str(s):
  res = ""
  for (data, encoding) in decode_header(s):
    if data != None and encoding != None:
      res += str(data.decode(encoding).encode("utf-8"), "utf-8")
    else:
      res += data
  return res

def make_person_schema(mailFile, schemaFile):
  msg = BytesParser().parse(mailFile)
  (realname, mailAddr) = email.utils.parseaddr(msg['from'])
  realname = make_utf8_str(realname)
  mailAddr = make_utf8_str(mailAddr)
  schema = """\
  <div itemscope itemtype="http://schema.org/Person">
    <span itemprop="name">%s</span>
    <span itemprop="email">%s</span>
  </div>""" % (realname, mailAddr)
  schemaFile.write(textwrap.dedent(schema))

def mails2schema(mailDir, outputDir):
  i = 0
  for mail in os.listdir(mailDir):
    mailFilename = mailDir + "/" + mail
    print(mailFilename)
    if(os.path.isfile(mailFilename)):
      schemaFilename = "%s/person%d.html" % (outputDir,i)
      i = i + 1
      with open(mailFilename, 'r+b') as mailFile, open(schemaFilename, 'w', encoding='utf8') as schemaFile:
        make_person_schema(mailFile, schemaFile)

def main():
  parser = argparse.ArgumentParser(description='Mail to schema')
  parser.add_argument('-d', required=True, help='Directory containing mail files (.eml).')
  parser.add_argument('-o', required=True, help='Output directory for the schemas.')
  args = parser.parse_args()
  if not os.path.isdir(args.d):
    print('%s is not a directory (option -d).', args.d)
  elif not os.path.isdir(args.o):
    print('%s is not a directory (option -o).', args.o)
  else:
    mails2schema(args.d, args.o)

if __name__ == "__main__":
  main()
