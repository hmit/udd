import sys
import os

if __name__ == '__main__':
  if os.system("python sources_gatherer.py " + " ".join(sys.argv[1:])) == 0:
    os.system("python packages_gatherer.py " + " ".join(sys.argv[1:]))
