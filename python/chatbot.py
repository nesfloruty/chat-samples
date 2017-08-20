# coding=utf-8
'''
Copyright 2017 Amazon.com, Inc. or its affiliates and nesfloruty. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
'''

import sys
import irc.bot
import requests
from pypubg import core
import time

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel,pubg_api_key):
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel
        print 'Get API PUBG'
        self.api_pubg = core.PUBGAPI(pubg_api_key)
        print 'Ok'
        # Get the channel id, we will need this for v5 API calls
        url = 'https://api.twitch.tv/kraken/users?login=' + channel
        headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        self.channel_id = r['users'][0]['_id']
        
        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        print 'Connecting to ' + server + ' on port ' + str(port) + '...'
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+token)], username, username)
        
        
        print 'Connect Done'

    def on_welcome(self, c, e):
        print 'Joining ' + self.channel

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

    def on_pubmsg(self, c, e):
        # If a chat message starts with an exclamation point, try to run it as a command
        #Define some variables
        player_name = "error"
        game_mode = "solo"
        if e.arguments[0][:1] == '!':
            cmd = e.arguments[0].split(' ')[0][1:]
            if cmd == 'stat':
                try:
                    game_mode = e.arguments[0].split(' ')[1]
                    player_name = e.arguments[0].split(' ')[2]
                except IndexError:
                    print 'Typpo mistake'
                print 'Received player name: ' + player_name
            print 'Received command: ' + cmd
            self.do_command(e, cmd, player_name, game_mode)
        return

    def do_command(self, e, cmd, player_name, game_mode):
        c = self.connection
        # Poll the API to get current game.
        if cmd == "game":
            
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            time.sleep(1)
            c.privmsg(self.channel, r['display_name'] + ' is currently playing ' + r['game'])

        elif cmd == 'stat':
            try:
                dict_pubg = self.api_pubg.player_skill(player_name, game_mode=game_mode)
                message = u'Игрок '+player_name+u' имеет рейтинг: '+''.join('{} - {} points * '.format(key.upper(), val) for key, val in sorted(dict_pubg.items()))
                c.privmsg(self.channel, message)
            except KeyError:
                time.sleep(1)
                message = u"Игрока с ником " + player_name + u" нет в PUBG." 
                c.privmsg(self.channel, message)
        # Poll the API the get the current status of the stream
        elif cmd == "title":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            time.sleep(1)
            c.privmsg(self.channel, r['display_name'] + ' channel title is currently ' + r['status'])

        # Provide basic information to viewers for specific commands
        elif cmd == "raffle":
            time.sleep(1)
            message = "raffle"
            c.privmsg(self.channel, message)
        elif cmd == "nes":
            time.sleep(1)
            message = u'Просмотр рейтинга в PUBG: !stat <solo или duo или squad> <игровое имя in PUBG>' 
            #u'If you want to see rating: ?stat <solo or duo or squad> <player name in PUBG>'
            c.privmsg(self.channel, message)

        # The command was not recognized
        #else:
        #    c.privmsg(self.channel, "Did not understand command: " + cmd)

def main():
    if len(sys.argv) != 6:
        print("Usage: twitchbot <username> <client id> <token> <channel> <pubg_api_key>")
        sys.exit(1)

    username  = sys.argv[1]
    client_id = sys.argv[2]
    token     = sys.argv[3]
    channel   = sys.argv[4]
    pubg_api_key = sys.argv[5]

    
    bot = TwitchBot(username, client_id, token, channel,pubg_api_key)
    bot.start()


if __name__ == "__main__":
    main()
