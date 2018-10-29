import cherrypy
import os
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('html'))

import psycopg2
DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
cur.execute("""
CREATE TABLE users(
    id integer PRIMARY KEY,
    username text
)
""")
conn.commit()


class HelloWorld(object):
    @cherrypy.expose
    def index(self):
        data_to_show = ['Hello', 'world']
        tmpl = env.get_template('index.html')
        return tmpl.render(data=data_to_show)

config = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(os.environ.get('PORT', 5000)),
    },
    '/assets': {
        'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
        'tools.staticdir.on': True,
        'tools.staticdir.dir': 'assets',
    }
}

cherrypy.quickstart(HelloWorld(), '/', config=config)
