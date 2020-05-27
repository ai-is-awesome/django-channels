import re
import os
import json
from decouple import Config, RepositoryEnv
from redis import StrictRedis

room_to_chatbot_user = {
    # Contains a mapping from the room names to the Chatbot Users
    # We need to populate this from the User DB, but for now, we'll put some sample values
    'lobby': 'Susan',
    'default': 'Gerald',
}

DOTENV_FILE = os.path.join(os.getcwd(), 'livechat', '.env')
env_config = Config(RepositoryEnv(DOTENV_FILE))

HOST = env_config.get('REDIS_SERVER_HOST')
PASSWORD = env_config.get('REDIS_SERVER_PASSWORD')
PORT = env_config.get('REDIS_SERVER_PORT')

class ChatBotUser():
    def __init__(self, chatbot_user, template):
        self.name = chatbot_user
        self.content = self.process_template(template)
        self.state = 1
        self.redis_connection = StrictRedis(host=HOST, password=PASSWORD, port=PORT)
        self.waiting = False
        self.has_options = False
    
    def process_template(self, template_json):
        # We'll process the template JSON and put it into a Database
        file_obj = open(template_json, 'rb')
        content = json.load(file_obj)
        file_obj.close()
        return content
    

    def insert_placeholders(self, message, has_options):
        # Hello {username} => Hello {redis_connection.get('username')}
        pattern = r"\{([A-Za-z0-9_]+)\}"
        encoding = 'utf-8'
        def replace_function(match):
            # Strip away the '{' and '}' from the match string
            match = match.group()[1:-1]
            # Redis gives us a byte string. Decode that to 'utf-8' and convert to a string
            return str(self.redis_connection.get(match).decode(encoding))
        message = re.sub(pattern, replace_function, message)
        if has_options is True:
            message += '\n'
            for idx, option in enumerate(self.options):
                message += str(idx) + '. ' + option + '\n'
        return message


    def process_message(self, message, initial_state):
        # We'll process the message here. Important stuff can be cached using redis
        # NOTE: We're assuming that all states from [1 .. N] are available, and in order
        self.state = initial_state

        print(f"Currently at state {self.state}")

        node = self.content['node'][initial_state - 1]

        if self.waiting is True:
            self.waiting = False
            self.state = node['trigger']
            print(self.state, type(self.state))
            if isinstance(self.state, list):
                # We must go to the state, based on the option / response
                if 'options' in node:
                    # Option
                    # Take it based on the message
                    msg_option = int(message)
                    print(f"Selected option {msg_option}")
                    return self.process_message(message, self.state[msg_option]), self.state[msg_option]
            else:
                return self.process_message(message, self.state), self.state

        try:
            key = node['store']
            self.redis_connection.set(key, message)
        except KeyError:
            pass

        try:
            if node['options'] is not None:
                self.has_options = True
                self.options = node['options']
            else:
                self.has_options = False
        except KeyError:
            self.has_options = False
        
        try:
            if node['end'] is True:
                # Last state. Close chat
                self.state = -1
                msg = self.insert_placeholders(node['message'], self.has_options) + "\n" + "Thank you for your time. Hope to see you again!"
                return msg, self.state
        except KeyError:
            # Move to the next state
            try:
                self.state = node['trigger']
            except KeyError:
                raise ValueError("This shouldn't happen. We must have either a trigger or an end")
            try:
                return self.insert_placeholders(node['message'], self.has_options), self.state
            except KeyError:
                # Return the message of the next state
                if 'user' in node:
                    self.waiting = True
                    msg = self.content['node'][self.state - 1]['message']
                    msg = self.insert_placeholders(msg, self.has_options)
                    next_state = node['trigger']
                    print(f'user => next_state = {next_state}')
                    if isinstance(next_state, list):
                        # We must go to the state, based on the option / response
                        if self.has_options is True:
                            # Option
                            # Take it based on the message
                            msg_option = int(message)
                            print(f"Selected option {msg_option}")
                            return self.process_message(message, self.state[msg_option]), self.state[msg_option]
                        else:
                            raise ValueError('Has no options???')
                    return self.process_message(msg, node['trigger']), self.state
                return self.process_message(message, node['trigger']), self.state