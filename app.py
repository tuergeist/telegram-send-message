import cherrypy
import os
import psycopg2
import requests
import _thread, time
from jinja2 import Environment, FileSystemLoader

DATABASE_URL = os.environ['DATABASE_URL']
TELEGRAM_BOT = os.environ['TELEGRAM_BOT']
CALLBACK_URL = os.environ['CALLBACK_URL']

env = Environment(loader=FileSystemLoader('html'))
conn = psycopg2.connect(DATABASE_URL, sslmode='require')


def telegram_request(endpoint, params=None):
    url = 'https://api.telegram.org/' + TELEGRAM_BOT + '/' + endpoint
    r = requests.get(url, params=params)
    return r


class User(object):
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id integer PRIMARY KEY,
            username text
        )
        """)
        self.conn.commit()

    def create(self, user_id, user_name):
        try:
            query = """
                INSERT INTO users (id, username) VALUES ({}, '{}')
            """.format(user_id, user_name)
            # print(query)
            self.cur.execute(query)
            self.conn.commit()
        except Exception as e:
            print('Error ', e)

    def get_all(self):
        """

        :return: [(id, username),()]
        """
        all = []
        query = """SELECT * FROM  users"""
        self.cur.execute(query)
        for r in self.cur:
            all.append(r)
        return all

    def delete(self, user_id):
        query = """
        DELETE FROM users WHERE id={}
        """.format(user_id)
        print(query)
        self.cur.execute(query)
        conn.commit()


class MessageSender(object):
    def __init__(self, user):
        self.user = user

    @cherrypy.expose
    def index(self):
        data_to_show = []
        for r in self.user.get_all():
            data_to_show.append("{} ({})".format(r[1], r[0]))

        tmpl = env.get_template('index.html')
        return tmpl.render(data=data_to_show)

    @cherrypy.expose
    def test(self):
        r = telegram_request('getWebhookinfo')
        print(r.text)

    @cherrypy.expose
    def send(self, user_id, message):
        if message is None:
            raise cherrypy.HTTPError(400, message="need a message as parameter")
        r = telegram_request('sendMessage', {'chat_id': user_id, 'text': message})
        print(r.text)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def callback(self):
        data = cherrypy.request.json
        print('CALLBACK')
        print(data)

        text = data['message']['text']
        user_id = data['message']['from']['id']
        if text == '/list':
            msg = "Registered users:\n"
            for r in self.user.get_all():
                print(r)
                msg += " * {} ({})\n".format(r[1], r[0])
            self.send(user_id, msg)

        if text == '/subscribe':
            user_name = data['message']['from']['first_name'] + ' ' + data['message']['from']['last_name']
            self.user.create(user_id, user_name)
            self.send(user_id, "Welcome " + user_name)

        if text == '/unsubscribe':
            self.user.delete(user_id)
            self.send(user_id, "Bye bye ")


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


def _register_webhook():
    time.sleep(15)
    url = 'https://api.telegram.org/' + TELEGRAM_BOT + '/setWebhook'
    r= requests.get(url,  data={'url': CALLBACK_URL})
    print(r.status_code, r.headers['content-type'], r.encoding)
    print(r.text)


def register_webhook():
    _thread.start_new_thread(_register_webhook, ())


register_webhook()
cherrypy.quickstart(MessageSender(User(conn)), config=config)
