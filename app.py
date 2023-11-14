from flask import Flask, render_template, request, jsonify
import openai
import re
import json
import asyncio

app = Flask(__name__)

with open('openapi_key.json', 'r') as file:
    data = json.load(file)

# Access the API key
api_key = data['api_key']

openai.api_key = api_key

async def async_openai_request(prompt):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, openai.ChatCompletion.create, {
        "model": "text-davinci-003",  # You can use a different model if needed
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096
    })

def extract_chapters(json_response):
    if not isinstance(json_response, str):
        # Convert to string if it's not already
        json_response = str(json_response)

    chapters = re.findall(r'(\d+) - ([^\n]+)', json_response)
    return [{'chapter': chapter, 'timestamp': f'{int(timestamp)//3600:02d}:{(int(timestamp)//60)%60:02d}:{int(timestamp)%60:02d}'}
            for timestamp, chapter in chapters]

@app.route('/')
def index():
    return render_template('index.html')

async def get_timeline_async(prompt):
    try:
        completion = openai.ChatCompletion.create(
            model="ft:gpt-3.5-turbo-0613:leadsift::8KXQY7Yj",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        json_response = completion.choices[0].message
        openai_json = json.dumps(json_response)

        data = json.loads(openai_json)
        content = data['content']

        chapters = [{"timestamp": timestamp.strip(), "chapter": chapter.strip()} for timestamp, chapter in
                    (entry.split('-', 1) for entry in content.split('\n'))]

        return chapters
    except Exception as e:
        app.logger.error("An error occurred: %s", str(e))
        return None

@app.route('/get_timeline', methods=['POST'])
async def get_timeline_route():
    try:
        prompt = request.form['prompt']

        task = asyncio.create_task(get_timeline_async(prompt))
        chapters = await task

        if chapters is not None:
            return render_template('timeline.html', chapters=chapters)
        else:
            return "An error occurred. Please try again later.", 500
    except Exception as e:
        app.logger.error("An error occurred: %s", str(e))
        return "An error occurred. Please try again later.", 500

if __name__ == '__main__':
    app.run(debug=True)
