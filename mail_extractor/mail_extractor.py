#!/usr/bin/python3

import email
import sys
import os
import argparse
import textwrap
from email.header import decode_header
from email.parser import BytesParser

class Person:
  def __init__(self, name, email):
    self.email = email
    self.name = name

  def to_schema(self):
    schema = """\
    <div itemscope itemtype="http://schema.org/Person">
      <span itemprop="name">%s</span>
      <span itemprop="email">%s</span>
    </div>""" % (self.name, self.email)
    return textwrap.dedent(schema)

def make_utf8_str(s):
  res = ""
  for (data, encoding) in decode_header(s):
    if data != None and encoding != None:
      res += str(data.decode(encoding).encode("utf-8"), "utf-8")
    else:
      res += data
  return res

def guess_name_from_mail_addr(mailAddr):
  return mailAddr.partition('@')[0]

def merge_person(p1, p2):
  return p2

def make_person_schema(mailFile, outputDir, person_db):
  msg = BytesParser().parse(mailFile)
  (realname, mailAddr) = email.utils.parseaddr(msg['from'])
  mailAddr = make_utf8_str(mailAddr)
  realname = make_utf8_str(realname)
  if not realname:
    realname = guess_name_from_mail_addr(mailAddr)
  person = Person(realname, mailAddr)

  if mailAddr in person_db:
    person_db[mailAddr] = merge_person(person, person_db[mailAddr])
  else:
    person_db[mailAddr] = person

  person = person_db[mailAddr]
  # Write the new person schema to file.
  schemaFilename = "%s/%s.html" % (outputDir, mailAddr)
  with open(schemaFilename, 'w', encoding='utf8') as schemaFile:
    schemaFile.write(person.to_schema())

def mails2schema(mailDir, outputDir):
  person_db = {}
  for mail in os.listdir(mailDir):
    mailFilename = mailDir + "/" + mail
    print(mailFilename)
    if(os.path.isfile(mailFilename)):
      with open(mailFilename, 'r+b') as mailFile:
        make_person_schema(mailFile, outputDir, person_db)

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
