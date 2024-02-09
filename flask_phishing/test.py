from flask import Flask, request, make_response

app = Flask(__name__)

@app.route('/')
def index():
    # Your response content
    response_content = "Hello, world!"
    
    # Create a response with the desired content
    response = make_response(response_content)
    
    # Set the custom header
    response.headers['ngrok-skip-browser-warning'] = 'true'
    
    return response

if __name__ == '__main__':
    app.run(debug=True)
