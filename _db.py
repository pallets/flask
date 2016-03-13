import sqlite3

conn=sqlite3.connect('mytest.db')
cursor=conn.cursor()
sql='''create table students (
            name text,
			username text,
			id int)'''
cursor.execute(sql)
cursor.close()