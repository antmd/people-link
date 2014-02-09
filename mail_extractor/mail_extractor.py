#!/usr/bin/python3

import email
import sys
import os
import argparse
from email.header import decode_header
from email.parser import BytesParser
from lxml import etree

class Person:
  def __init__(self, name, email):
    self.emails = set()
    self.addEmail(email)
    self.name = name
    self.relations = set()

  def knows(self, p):
    self.relations.add(p)

  def addEmail(self, email):
    self.emails.add(email.lower())

  def to_schema(self):
    # Boolean attribute without value are forbidden in XML, so we use the "empty string" syntax.
    root = etree.Element("div", itemscope="", itemtype="http://schema.org/Person")
    etree.SubElement(root, "span", itemprop="name").text = self.name

    for mail in self.emails:
      etree.SubElement(root, "span", itemprop="email").text = mail
    return root

  def to_string_schema(self):
    return str(etree.tostring(self.to_schema(), method="html", encoding="utf-8", pretty_print=True), encoding="utf-8")

  def merge(self, p):
    self.emails = self.emails.union(p.emails)
    # TODO try to find the better name.
    self.relations = self.relations.union(p.relations)
    return self

def relateTwoPersons(p1, p2):
  p1.knows(p2)
  p2.knows(p1)

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
  if p1 == None:
    return p2
  elif p2 == None:
    return p1
  else:
    return p1.merge(p2)

def find_person(person_db, p):
  for email in p.emails:
    if email in person_db:
      return person_db[email]
  return None

def update_db(person_db, p):
  for email in p.emails:
    if not email in person_db:
      person_db[email] = p

def get_info_from_mail_field(field):
  (realname, mailAddr) = email.utils.parseaddr(field)
  realname = make_utf8_str(realname)
  mailAddr = make_utf8_str(mailAddr.lower())
  if not realname:
    realname = guess_name_from_mail_addr(mailAddr)
  return (realname, mailAddr)

def make_person_schema(mailFile, outputDir, person_db):
  msg = BytesParser().parse(mailFile)
  # Retrieve the from person.
  (realname, mailAddr) = get_info_from_mail_field(msg['from'])
  person = Person(realname, mailAddr)

  # Add it to the database.
  if mailAddr in person_db:
    person_db[mailAddr] = merge_person(person, person_db[mailAddr])
  else:
    person_db[mailAddr] = person

  # Find ourself
  (my_name, my_email) = get_info_from_mail_field(msg['Delivered-To'])
  me = Person(my_name, my_email)

  def addToMyEmailAddr(field_name):
    (_, my_email_addr) = get_info_from_mail_field(msg[field_name])
    if my_email_addr:
      me.addEmail(my_email_addr)

  addToMyEmailAddr('X-Original-To')
  addToMyEmailAddr('Resent-From')

  myself = find_person(person_db, me)
  myself = merge_person(myself, me)
  update_db(person_db, myself)

  # Find cc and to relation (excluding ourself)


def mails2schema(mailDir, outputDir):
  person_db = {}
  for mail in os.listdir(mailDir):
    mailFilename = mailDir + "/" + mail
    print(mailFilename)
    if(os.path.isfile(mailFilename)):
      with open(mailFilename, 'r+b') as mailFile:
        make_person_schema(mailFile, outputDir, person_db)
  # Create all the files from the db
  for p in person_db.values():
    schemaFilename = "%s/%s.html" % (outputDir, next(iter(p.emails)))
    with open(schemaFilename, 'w', encoding='utf8') as schemaFile:
      schemaFile.write(p.to_string_schema())

def main():
  parser = argparse.ArgumentParser(description='Mail to schema')
  parser.add_argument('-d', required=True, help='Directory containing mail files (.eml).')
  parser.add_argument('-o', required=True, help='Output directory for the schema.')
  args = parser.parse_args()
  if not os.path.isdir(args.d):
    print('%s is not a directory (option -d).', args.d)
  elif not os.path.isdir(args.o):
    print('%s is not a directory (option -o).', args.o)
  else:
    mails2schema(args.d, args.o)

if __name__ == "__main__":
  main()
