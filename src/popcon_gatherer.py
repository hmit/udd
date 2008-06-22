import aux
import sys
import gzip

def main():
  if len(sys.argv) != 3:
    print 'Usage: %s <config-file> <source>' % sys.argv[0]
    sys.exit(1)

  config = aux.load_config(open(sys.argv[1]).read())
  source = sys.argv[2]

  try:
    my_config = config[source]
  except:
    raise

  if not 'path' in my_config:
    raise aux.ConfigException, "path not configured for source " % source

  conn = aux.open_connection(config)

  cur = conn.cursor()

  cur.execute("PREPARE pop_insert AS INSERT INTO popcon (name, vote, olde, recent, nofiles) VALUES ($1, $2, $3, $4, $5)")

  popcon = gzip.open(my_config['path'])

  for line in popcon.readlines():
    name, data = line.split(None, 1)
    if name == "Submissions:":
      cur.execute("INSERT INTO popcon (name, vote) VALUES ('_submissions', %s)" % (data))
    try:
      (name, vote, old, recent, nofiles) = data.split()
      cur.execute("EXECUTE pop_insert('%s', %s, %s, %s, %s)" %\
	  (name, vote, old, recent, nofiles))
    except ValueError:
      continue

  cur.execute("DEALLOCATE pop_insert")
  conn.commit()

if __name__ == '__main__':
  main()
