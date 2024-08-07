import requests
from flask import Flask, render_template, redirect, url_for, request
import openai


OPEN_AI_KEY = 'key'

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("test.html")

def generate_prompt(animal):
    return """Suggest three names for an animal that is a superhero.
Animal: Cat
Names: Captain Sharpclaw, Agent Fluffball, The Incredible Feline
Animal: Dog
Names: Ruff the Protector, Wonder Canine, Sir Barks-a-Lot
Animal: {}
Names:""".format(animal.capitalize())

response = openai.Completion.create(
model="text-davinci-003",
prompt=generate_prompt('Horse'),
temperature=0.6
)

print(response)

if __name__ == '__main__':
    app.run(debug=True)
