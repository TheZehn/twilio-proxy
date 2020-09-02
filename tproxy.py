import re

from flask import Flask, request,send_from_directory
from twilio.twiml.voice_response import Gather, VoiceResponse, Dial, Play
from twilio.twiml.messaging_response import Message, MessagingResponse

# Behavior is separate between the private caller and an incoming caller
from config import PRIVATE_NUMBER, TWILIO_NUMBER

app = Flask(__name__)

#For incoming sms: text messages, format NUM: MSG
def encode_message(msg, number):
	return "{}: {}".format(number, msg)

#for outgoing sms, accept NUM: MSG and split for sending
def decode_message(msg):
	pattern = re.compile("^\+\d*")
	number = pattern.match(msg).group()
	body = msg[len(number) + 2:]
	return body, number

# Intro music path
@app.route("/music/<path:filename>")
def get_music(filename):
	return send_from_directory("music/",filename)

# how SMS messages are handled
@app.route('/sms', methods=['POST'])
def sms():
	from_number = request.form['From']
	msg_body = request.form['Body']
	
	if from_number == PRIVATE_NUMBER:
		msg, to_number = decode_message(msg_body)
		return send_message(msg, to_number)
	else:
		msg = encode_message(msg_body, from_number)
		return send_message(msg, PRIVATE_NUMBER)

#how calls ar ehandled
@app.route("/call", methods=['GET', 'POST'])
def call():
	from_number = request.form['From']
	if from_number != PRIVATE_NUMBER:
		return perform_call(PRIVATE_NUMBER)
	else:
		response = VoiceResponse()
		g = Gather(action="/aliasing", finish_on_key="#", method="POST")
		g.say("Dial the number you want to call followed by the pound sign")
		response.append(g)
		return str(response)

@app.route("/aliasing", methods=['GET', 'POST'])
def aliasing():
	number = request.values.get("Digits")
	if number:
		return perform_call(number, TWILIO_NUMBER)
	return "Aliasing failed."

@app.route("/callscreen", methods=["GET","POST"])
def callscreen():
	r = VoiceResponse()
	r.say("Call through Vanity Number")
	return str(r)
	

def send_message(msg, number):
	response = MessagingResponse()
	response.message(msg, to=number, from_=TWILIO_NUMBER)
	return str(response)

def perform_call(number, caller_id=None):
	response = VoiceResponse()
	d = Dial()
	if number == PRIVATE_NUMBER:	
		p = Play("http://phone.ehnerd.com/music/intro.wav")
		response.append(p)
		d.number(number,url="/callscreen")
	else:
		d.number(number)
	response.append(d)
	return str(response)

if __name__ == '__main__':
	app.run(port=7070, host="127.0.0.1", debug=False)
