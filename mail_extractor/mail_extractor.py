#!/usr/bin/python3

import email
import sys
import os
import argparse
from email.header import decode_header
from email.parser import BytesParser
from lxml import etree

# TODO use a "real email" (first encountered) and "alternative emails" field.
class Person:
  def __init__(self, name, email):
    self.emails = set()
    self.addEmail(email)
    self.name = name
    self.relations = {}

  def knows(self, p):
    for m in p.emails:
      self.relations[m] = p
      break

  def addEmail(self, email):
    self.emails.add(email.lower())

  def to_schema(self):
    # Boolean attribute without value are forbidden in XML, so we use the "empty string" syntax.
    root = etree.Element("div", itemscope="", itemtype="http://schema.org/Person")
    etree.SubElement(root, "span", itemprop="name").text = self.name

    for mail in self.emails:
      etree.SubElement(root, "span", itemprop="email").text = mail

    for relation in self.relations.values():
      relation_filename = make_person_filename(relation)
      etree.SubElement(root, "a", href=relation_filename, itemprop="knows").text = relation.name
    return root

  def to_string_schema(self):
    return str(etree.tostring(self.to_schema(), method="html", encoding="utf-8", pretty_print=True), encoding="utf-8")

  def merge(self, p):
    self.emails = self.emails.union(p.emails)
    # TODO try to find the better name.
    self.relations.update(p.relations)
    return self

def relateTwoPersons(p1, p2):
  if p1 and p2:
    p1.knows(p2)
    p2.knows(p1)

def make_person_filename(p):
   return next(iter(p.emails)) + ".html"

def make_utf8_str(s):
  res = ""
  for (data, encoding) in decode_header(s):
    if data != None and encoding != None:
      res += str(data.decode(encoding).encode("utf-8"), "utf-8")
    else:
      res += str(data)
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

def update_db(person_db, person):
  for email in person.emails:
    if email in person_db:
      person = merge_person(person, person_db[email])
  for email in person.emails:
    person_db[email] = person

def mail_info(realname, mailAddr):
  realname = make_utf8_str(realname)
  mailAddr = make_utf8_str(mailAddr.lower())
  if not realname:
    realname = guess_name_from_mail_addr(mailAddr)
  return (realname, mailAddr)

def get_info_from_mail_field(field):
  (realname, mailAddr) = email.utils.parseaddr(field)
  return mail_info(realname, mailAddr)

def link_people(person_db, myself, contacts_field):
  contacts_field = email.utils.getaddresses(contacts_field)
  if contacts_field:
    people = set()
    for (name, email_addr) in contacts_field:
      (name, email_addr) = mail_info(name, email_addr)
      if email_addr not in person_db or person_db[email_addr] != myself:
        update_db(person_db, Person(name, email_addr))
        people.add(email_addr)
    for mail in people:
      relateTwoPersons(person_db[mail], myself)

def make_person_schema(mailFile, outputDir, person_db):
  msg = BytesParser().parse(mailFile)
  # Retrieve the from person.
  (realname, mailAddr) = get_info_from_mail_field(msg['from'])
  person = Person(realname, mailAddr)

  # Add it to the database.
  update_db(person_db, person)

  # Find ourself
  (my_name, my_email) = get_info_from_mail_field(msg['Delivered-To'])
  me = Person(my_name, my_email)

  def addToMyEmailAddr(field_name):
    (_, my_email_addr) = get_info_from_mail_field(msg[field_name])
    if my_email_addr:
      me.addEmail(my_email_addr)

  addToMyEmailAddr('X-Original-To')
  addToMyEmailAddr('Resent-From')

  update_db(person_db, me)

  # Find cc and to relation (excluding ourself)
  link_people(person_db, me, msg.get_all('to', []))
  link_people(person_db, me, msg.get_all('cc', []))


def mails2schema(mailDir, outputDir):
  person_db = {}
  for mail in os.listdir(mailDir):
    mailFilename = mailDir + "/" + mail
    # print(mailFilename)
    if(os.path.isfile(mailFilename)):
      with open(mailFilename, 'r+b') as mailFile:
        make_person_schema(mailFile, outputDir, person_db)
  # Create all the files from the db
  for p in person_db.values():
    schemaFilename = "%s/%s" % (outputDir, make_person_filename(p))
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
