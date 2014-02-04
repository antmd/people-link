import email
import sys
import os
import argparse
import textwrap

def make_person_schema(msg, schemaFile):
  schema = """\
  <div itemscope itemtype="http://schema.org/Person">
    <span itemprop="email">%s</span>
  </div>""" % msg['from']
  schemaFile.write(textwrap.dedent(schema))

def mails2schema(mailDir, outputDir):
  i = 0
  for mail in os.listdir(mailDir):
    mailFilename = mailDir + "/" + mail
    if(os.path.isfile(mailFilename)):
      schemaFilename = "%s/person%d.html" % (outputDir,i)
      i = i + 1
      with open(mailFilename, 'r') as mailFile, open(schemaFilename, 'w') as schemaFile:
        make_person_schema(email.message_from_file(mailFile), schemaFile)

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
