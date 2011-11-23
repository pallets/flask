"""Starts a project with directories such as templates/ and static/ inside an application directory specified as the first argument.

Also, adds some stuff to .gitignore in case you want to you use git.

Example:

python flask_start.py myapp

This creates a myapp/ directory, with the following structure:

myapp/
---- .gitignore
---- templates/
	--- index.html
---- static/
	---- index.css
---- myapp.py"""

import os
import sys

def create_app_dir(appname):
    if not os.path.isdir(appname):
        os.makedirs(appname)
        
        f = open(appname + "/" + appname + ".py", "w+")
        f = open(appname + "/.gitignore", "w+")
        f.write("*.pyc")
        
        print "Created application directory."
        return True
    else:
        return False

def create_temp_dir(appname):
    p = appname + "/templates"

    if not os.path.isdir(p):
        os.makedirs(p)
        f = open(p + "/index.html", "w+")

        print "Created templates directory."
        return True

    else:
        return False   

def create_stat_dir(appname):
    p = appname + "/static"

    if not os.path.isdir(p):
        os.makedirs(p)
        f = open(p + "/index.css", "w+")
        
        print "Created static directory."
        return True
 
    else:
        return False

def main():
    if(len(sys.argv) != 2):
        print "Usage: flask_start.py appname"
        return

    an = sys.argv[1]
    if not create_app_dir(an):
        print "Couldn't create directory for application!"
        return

    if not create_temp_dir(an):
        print "Couldn't create template directory!"
        return
    
    if not create_stat_dir(an):
        print "Couldn't create static directory!"
        return
       
if __name__ == "__main__":
    main()
