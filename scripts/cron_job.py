import sys, os
import fcntl
import sqlite3 as lite
import pdb

"""
This script is executed every few minutes to check if any new user registered
on the website. If any did, then the convnet.py script is launched and do
a learning phase for that user

If the script is still executing the previous cron call, then it should raise an exception
using a file lock: the lock should be released when the previous call finished
"""


if __name__ == "__main__":
  f = open('lock', 'w')
  try:
    fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
  except IOError, e:
    print "busy"
    sys.exit(-1)
  
  # Look for a user to learn and call convnet
  
  # get all email:
  sqlpath = "/home/frochet/C-Cure/canvasauth/db.sqlite3"
  basepath = "/home/frochet/C-Cure/canvasauth/script/"
  
  connection = lite.connect(sqlpath)
  c = connection.cursor()
  c.execute('SELECT email, authc_computer.id FROM auth_user, authc_computer\
             WHERE authc_computer.user_id_id = auth_user.id')
  results= c.fetchall()
  firstemailok = ""
  badcomps = []
  with open(basepath+"wrongcomplist", "r") as wrongcomps:
    for line in wrongcomps:
        badcomps.append(int(line[:-1])) #remove \n
  for (email, compid) in results:
    filepath = basepath+"models/{0}compid{1}.h5".format(email.replace("@", "").replace(".",""), compid)
    if not os.path.isfile(filepath) and compid not in badcomps:
      firstemailok = email
      break
  c.close()
  #we do the learning on firstemailok
  print "Learning for {0}".format(firstemailok)
  retvalue = ""
  if firstemailok != "":
      retvalue = os.system("python convnet.py --db {0} --email {1} --compid {2} --max_epoch 100 --store --filepath_model models --filepath_hist history".format(sqlpath, firstemailok, compid)) >> 8
  print retvalue
  if retvalue == 255: # convnet exit(-1)
      with open(basepath+"wrongcomplist", "a") as badcomps:
          badcomps.write("{0}\n".format(compid))

  f.close()
  sys.exit(0)
