from api_server import app

if __name__ == '__main__':
    # Run single process without Flask reloader to ensure consistent behavior
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
