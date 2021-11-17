# Angela Kerlin
# CSC 482
# Fall 2021
# Creates a chatbot that runs on an IRC server

from ctypes import c_char
import socket
import sys
import time
import os
import random
import re
from enum import Enum
from ytInter import YT

from timerInterrupt import Timer

class mode(Enum):
    INIT = 0
    REC_GREET = 1
    GREET1 = 2
    GREET2 = 3
    GREET_REPLIED = 4
    INQUIRY1 = 5
    INQUIRY1_REPLY = 6
    INQUIRY2 = 7
    INQUIRY2_REPLY = 8
    END = 9
    GIVEUP = 10

class IRC:
 
    irc = socket.socket()
  
    def __init__(self):
        # Define the socket
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def command(self,msg):
        self.irc.send(bytes(msg + "\n", "UTF-8"))
 
    def send(self, channel, msg):
        # Transfer data
        if "die!" not in msg:
            # Just a failsafe to prevent killing
            self.command("PRIVMSG " + channel + " " + ":" + msg)
 
    def connect(self, server, port, channel, botnick, botpass, botnickpass):
        # Connect to the server
        print("Connecting to: " + server)
        self.irc.connect((server, port))

        # Perform user authentication
        self.command("USER " + botnick + " " + botnick +" " + botnick + " :python")
        self.command("NICK " + botnick)
        #self.irc.send(bytes("NICKSERV IDENTIFY " + botnickpass + " " + botpass + "\n", "UTF-8"))
        time.sleep(5)

        # join the channel
        self.command("JOIN " + channel)
 
    def get_response(self):
        time.sleep(1)
        # Get the response
        resp = self.irc.recv(2040).decode("UTF-8")
 
        if resp.find('PING') != -1:
           self.command('PONG ' + resp.split()[1]  + '\r') 
 
        return resp
    
    def getNames(self, channel, botname):
        print("REQUESTING NAMES...")
        self.command("NAMES " + channel)
        time.sleep(1)
        print("RECV NAMES...")
        resp = self.get_response()
        print(f"NAMES RESP: \n'''{resp}'''\n")
        for line in resp.split("\n"):
            m = re.search(r"^:.+:(.+)", line)
            if botname in line and m:
                names = [x.strip().strip("@") for x in m[1].split(" ") if len(x) > 0]
                print("NAMES ==> " + " ".join(names))
                return names
        return []

class Chatbot:

    def __init__(self, irc, botnick, channel):
        self.irc = irc
        self.channel = channel
        self.botnick = botnick
        self.convos = dict([]) # ongoing list of conversations indexed by the target username
        self.maxConvos = 1
        self.yt = YT()
    
    def initConversation(self, recip, text=""):
        """
        Initialize a conversation with the specified recipient. If max number of
        conversations would be exceeded, respond accordingly and do not init conversation
        """
        if len(self.convos) > self.maxConvos:
            self.irc.send(self.channel, recip + ": " + "Too many conversations!")
            return
        
        if text == "":
            # bot is initiating
            convo = Conversation(self, self.irc, self.channel, recip)
            self.convos[recip] = convo
            convo.greet()
        else:
            # someone else is initiating
            convo = Conversation(self, self.irc, self.channel, recip, mode.GREET1)
            self.convos[recip] = convo
            convo.respond(text)
    
    def convoOngoing(self):
        """
        Returns True if this bot has at least one ongoing conversation, False if
        it does not
        """
        return len(self.convos) > 0
    
    def existingConvo(self, sender):
        return sender in self.convos
    
    def getConvo(self, sender):
        return self.convos[sender]
    
    def setTimeout(self, sender):
        """
        Set a timer waiting on specified sender
        """
        pass

    def killAllConvos(self):
        recips = [recip for recip in self.convos]
        for recip in recips:
            self.killConvo(recip)

    def killConvo(self, recip):
        """
        Removes a conversation from the convos list
        """
        if recip in self.convos:
            convo = self.convos.pop(recip)
            if convo.timer != None:
                convo.timer.cancel()

class Conversation:

    def __init__(self, parentBot, irc, channel, recip, init=0):
        self.parentBot = parentBot
        self.irc = irc
        self.channel = channel
        self.recip = recip
        self.init = init
        self.initGreeting = False
        self.mode = mode.INIT
        # TODO: investigate options other than hard coding these sets (wordnet greetings?)
        self.greetSet = ["good morning", "good afternoon", "good evening", "hello", "hi", "hey", "howdy", "hullo"]
        self.greetRespIndex = 3
        self.byeSet = ["Goodbye!", "bye", "Farewell.", "It was nice talking to you! Bye!"]
        self.inqSet1 = ["How are you?", "what's happening?"]
        self.inqRepSet = ["I'm good", "I'm alright", "I'm okay", "I'm fine"]
        self.inqRepEndSet = [", thanks for asking"]
        self.inqSet2 = ["How about you?", "And yourself?"]
        self.upSet = ["Whatever.", "I'm done. Bye I guess", "I give up", "Fine. Don't answer", "Whatever man"]
        self.timer = None

        self.songWords = ["song", "track"]
        self.artistWords = ["artist", "author", "by"]
        self.requestWords = ["what", "whats", "what's", "get"]
        self.topCharts = ["top", "charts", "songs", "popular"]

        print(f"NEW CONVERSATION WITH {recip}")
    
    def sendToRecip(self, message):
        """
        Send specified message to recipient
        """
        # wait for some variable amount of time before sending
        time.sleep(random.choice([x / 2 for x in range(2, 8)]))
        exactText = self.recip + ": " + message
        print(f"SENDING ==> '''{exactText}'''")
        self.irc.send(self.channel, self.recip + ": " + message)
    
    def handleTimeout(self):
        """
        30 seconds have passed while waiting for a response. Based on the current
        state, perform valid actions in response
        """
        print("Time's up!")
        if self.mode == mode.GREET1:
            self.sendToRecip("...hello? Anyone there?")
            self.mode = mode.GREET2
            self.timer = Timer(30, self.handleTimeout)
            self.timer.start()
        else:
            print(f"GIVE UP ==> {self.mode}")
            self.sendToRecip(random.choice(self.upSet))
            self.parentBot.killConvo(self.recip)
        # otherwise, the mode is fine, shouldn't have a timer
 
    def greet(self):
        """
        Sends a greeting to the recipient
        """
        g = random.choice(self.greetSet[self.greetRespIndex:])
        self.sendToRecip(g)
        self.initGreeting = True
        if self.mode == mode.INIT:
            # initial 'empty' state -> greet completed one time
            self.mode = mode.GREET1
        elif self.mode == mode.REC_GREET:
            # recieved greeting -> greeting replied
            self.mode = mode.GREET_REPLIED
        self.timer = Timer(30, self.handleTimeout)
        self.timer.start()
    
    def respond(self, text):
        """
        Given text directed at botbot, return a reasonable response
        """
        if self.mode in [mode.GREET1, mode.GREET2, mode.INQUIRY1,
            mode.INQUIRY1_REPLY, mode.INQUIRY2, mode.INQUIRY2_REPLY]:
            # if a timer was set, cancel it
            if self.timer is not None:
                self.timer.cancel()

        tokText = text.lower().split()

        if "get usernames" in text.lower():
            names = self.irc.getNames(self.channel, self.parentBot.botnick)
            self.sendToRecip(" ".join(names))

        if not self.initGreeting:
            # greeting not yet complete, assume this was a greeting and respond
            if inSet(self.greetSet, text):
                self.greet()
                self.mode = mode.INQUIRY1 # next, they'll ask a question
            else:
                # First message and no hello -> ignore that, cancel conversation
                self.parentBot.killConvo(self.recip)
        
        elif self.mode in [mode.GREET1, mode.GREET2]:
            # they replied to bot's greeting with a greeting, time to inquire
            resp = random.choice(self.inqSet1)
            self.sendToRecip(resp)
            self.mode = mode.INQUIRY1_REPLY
            self.timer = Timer(30, self.handleTimeout)
            self.timer.start()

        elif self.mode == mode.INQUIRY1:
            # bot expects them to ask question, need to reply to question then
            # follow up with inquiry 2
            resp = random.choice(self.inqRepSet) + ("" if random.random() < 0.5 else random.choice(self.inqRepEndSet))
            self.sendToRecip(resp)
            inq = random.choice(self.inqSet2)
            self.sendToRecip(inq)
            self.mode = mode.INQUIRY2_REPLY
            self.timer = Timer(30, self.handleTimeout)
            self.timer.start()

        
        elif self.mode == mode.INQUIRY1_REPLY:
            # bot is expecting an answer to inquiry
            # they should reply to that inquiry here, then follow up with inqiry 2
            self.mode = mode.INQUIRY2
            self.timer = Timer(30, self.handleTimeout)
            self.timer.start()
        
        elif self.mode == mode.INQUIRY2:
            # bot is expecting a question, need to reply to it
            resp = random.choice(self.inqRepSet) + ("" if random.random() < 0.5 else random.choice(self.inqRepEndSet))
            self.sendToRecip(resp)
            self.mode = mode.END
            # resp = random.choice(self.byeSet)
            # self.sendToRecip(resp)
            # self.parentBot.killConvo(self.recip)

        elif self.mode == mode.INQUIRY2_REPLY:
            # bot is expecting an answer, need to end now
            self.mode = mode.END
            # resp = random.choice(self.byeSet)
            # self.sendToRecip(resp)
            # self.parentBot.killConvo(self.recip)
        
        elif self.mode == mode.END and inSet(self.requestWords, text) and inSet(self.topCharts, text):
            # TODO: get top charts
            for line in self.parentBot.yt.topChartsQuery(5):
                self.sendToRecip(line)

        elif self.mode == mode.END and "random" in text and inSet(self.requestWords, text) and\
            (inSet(self.artistWords, text) or inSet(self.songWords, text)):
            # TODO: give me a random song by x author
            filterOut(["random"] + self.songWords + self.artistWords + self.requestWords, tokText)
            query = " ".join(tokText)
            for line in self.parentBot.yt.randomSongQuery(query):
                self.sendToRecip(line)


        elif self.mode == mode.END and inSet(self.requestWords, text) and\
            (inSet(self.artistWords, text) or inSet(self.songWords, text)):
            # get information on a given song
            filterOut(self.songWords + self.artistWords + self.requestWords, tokText)
            query = " ".join(tokText)
            for line in self.parentBot.yt.generalQuery(query):
                self.sendToRecip(line)

        # TODO: get information on a given artist
        # TODO: get information on a given album
        # TODO: what can you do? --> list functionality

        else:
            # It should never actually reach this
            defaultStatement = "Sorry, I don't understand!"
            self.sendToRecip(defaultStatement)

def main():
    ## IRC Config
    server, port, channel, botnick, botpass, botnickpass = initSetup()
    irc = IRC()
    irc.connect(server, port, channel, botnick, botpass, botnickpass)
    time.sleep(3)
    text = irc.get_response() # eat the initial junk
    print("RECEIVED ==> ",text)
    text = irc.get_response() # eat the initial junk
    print("RECEIVED ==> ",text)
    text = irc.get_response() # eat the initial junk
    print("RECEIVED ==> ",text)

    running = True
    while running:
        state = Chatbot(irc, botnick, channel) # make a fresh state each time, enables "forgetting"
        running = mainLoop(irc, channel, botnick, state)

    irc.command("QUIT")
    sys.exit()


def mainLoop(irc, channel, botnick, chatbot):
    """
    This is the primary loop of the state machine. Returns False when dead,
    returns True when forgets
    """
    startConvo(irc, channel, botnick, chatbot)
    while True:
        text = irc.get_response()
        for line in text.split("\n"):
            print("RECEIVED ==> ",line)

            m = re.search(r"PRIVMSG.*" + channel + " :(.*)", line)
            if "PRIVMSG" in line and channel in line and (m[1].find(botnick + ":") == 0):
                # Bot is direcly mentioned, must respond
                sender = line[line.find(":") + 1:line.find("!")]
                msg = m[1][len(botnick) + 1:]
                print(f"\tSENDER ==> {sender}\n\tMESSAGE ==> {msg}")

                if "die!" in msg:
                    irc.send(channel, "*dies*")
                    return False
                elif "forget!" in msg:
                    irc.send(channel, "...")
                    chatbot.killAllConvos()
                    return True
                elif chatbot.existingConvo(sender):
                    # continuing existing conversation
                    chatbot.getConvo(sender).respond(msg)
                else:
                    # new person is contacting bot for the first time, new conversation
                    chatbot.initConversation(sender, msg)

def startConvo(irc, channel, botnick, chatbot):
    rawnames = irc.getNames(channel, botnick)
    names =[x for x in rawnames if x != botnick]
    if len(names) == 0:
        return False
    name = random.choice(names)
    chatbot.initConversation(name)
    return True


def initSetup():
    server = "irc.libera.chat" 	# Provide a valid server IP/Hostname
    port = 6667
    channel = "#CSC482"
    # botnick = "rando-bot"+str(random.randint(0,1000))
    botnick = "bot-bot"
    botnickpass = ""		# in case you have a registered nickname
    botpass = ""			# in case you have a registered bot
    return server, port, channel, botnick, botpass, botnickpass

def inSet(s, text):
    """
    Basic function that checks if anything in the set s occurs in the string text
    """
    lowText = text.lower()
    for i in s:
        if i in lowText:
            return True
    return False

def filterOut(s, tokText):
    """
    Removes the words in s (a set or list) found in tokText (a list)
    """
    for w in s:
        if w in tokText:
            tokText.remove(w)

if __name__ == "__main__":
    main()