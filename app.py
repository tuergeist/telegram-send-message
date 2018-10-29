import cherrypy
import os
import psycopg2
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('html'))

DATABASE_URL = os.environ['DATABASE_URL']
TELEGRAM_BOT = os.environ['TELEGRAM_BOT']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id integer PRIMARY KEY,
    username text
)
""")
conn.commit()


class MessageSender(object):
    @cherrypy.expose
    def index(self):
        data_to_show = ['Hello', 'world']
        tmpl = env.get_template('index.html')
        return tmpl.render(data=data_to_show)

    @cherrypy.expose
    def test(self):
        return 'test'

    @cherrypy.expose
    def send(self, message=None):
        if message is None:
            raise cherrypy.HTTPError(400, message="need a message as parameter")

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

cherrypy.quickstart(MessageSender(), config=config)
