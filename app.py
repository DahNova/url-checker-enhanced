from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO
import requests
from urllib3.exceptions import InsecureRequestWarning
import threading
import ssl
import time

# Suppress only the single InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize global variables
total_urls = 0
checked_urls = 0
url_results = []
abort_signal = False

# Route for index
@app.route("/", methods=["GET", "POST"])
def index():
    global total_urls, checked_urls, url_results, abort_signal
    if request.method == "POST":
        urls = request.form.get("urls")
        if not urls:
            return jsonify({"error": "URLs cannot be empty"}), 400

        urls = urls.splitlines()
        rate = request.form.get("rate")
        if not rate:
            return jsonify({"error": "Rate cannot be empty"}), 400

        rate = int(rate)

        # Reset globals
        total_urls = len(urls)
        checked_urls = 0
        url_results = []
        abort_signal = False

        def check_urls():
            app.logger.info("Starting to check URLs")
            global checked_urls, abort_signal
            for url in urls:
                if abort_signal:
                    break
                
                result = {"url": url}
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.3'}
                    response = requests.get(url, headers=headers, timeout=5, verify=False, allow_redirects=False)
                    redirect_chain = []
                    status_code = str(response.status_code)
                    while response.is_redirect:
                        redirect_url = response.headers['Location']
                        redirect_chain.append(redirect_url)
                        response = requests.get(redirect_url, headers=headers, timeout=5, verify=False, allow_redirects=False)
                        status_code = str(response.status_code)
                    result["status_code"] = status_code
                    result["final_url"] = response.url
                    result["redirect_chain"] = ' -> '.join(redirect_chain) if redirect_chain else 'N/A'
                    result["redirect_chain_length"] = len(redirect_chain) if redirect_chain  else '0'
                    result["ssl_valid"] = "Yes" if response.url.startswith("https") else "N/A"

                except requests.exceptions.SSLError:
                    result["status_code"] = "Error"
                    result["final_url"] = "Error"
                    result["ssl_valid"] = "No"
                except Exception as e:
                    app.logger.error(f"Exception occurred: {e}")
                    result["status_code"] = "Error"
                    result["final_url"] = "Error"
                    result["ssl_valid"] = "Can't Check"

                url_results.append(result)
                checked_urls += 1
                socketio.emit("progress", {"total": total_urls, "checked": checked_urls, "results": url_results})
                time.sleep(60 / rate)

        thread = threading.Thread(target=check_urls)
        thread.start()

        return jsonify({"message": "Processing URLs"})

    return render_template("index.html")


# Route to stop the URL checking process
@app.route("/abort", methods=["POST"])
def abort_process():
    global abort_signal
    abort_signal = True
    return jsonify({"message": "Aborted"})


# Main function to run the app
if __name__ == "__main__":
    socketio.run(app, debug=True)