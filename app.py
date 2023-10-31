from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import csv

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

total_urls = 0
checked_urls = 0
url_results = []
abort_signal = False

# Funzione per verificare robots.txt
def check_robots_txt(url):
    parsed_url = urlparse(url)
    is_allowed = True
    robots_txt_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    try:
        response = requests.get(robots_txt_url, timeout=5)
        if response.status_code == 200:
            disallowed_paths = []
            for line in response.text.splitlines():
                if line.startswith("Disallow:"):
                    disallowed_paths.append(line.split(":")[1].strip())
            is_allowed = all(not parsed_url.path.startswith(path) for path in disallowed_paths)
    except Exception as e:
        pass
    return is_allowed

# Funzione per controllare il tag canonical
def check_canonical_tag(soup):
    canonical_tag = soup.find("link", {"rel": "canonical"})
    return canonical_tag["href"] if canonical_tag else None

# Funzione per analizzare i meta tag (titolo e descrizione)
def analyze_meta_tags(soup):
    title_tag = soup.find("title")
    meta_desc_tag = soup.find("meta", {"name": "description"})
    title = title_tag.string if title_tag else None
    meta_desc = meta_desc_tag["content"] if meta_desc_tag else None
    return title, meta_desc

# Funzione per controllare i tag hreflang
def check_hreflang_tags(soup):
    hreflang_tags = soup.find_all("link", {"rel": "alternate", "hreflang": True})
    hreflangs = [tag["hreflang"] for tag in hreflang_tags]
    return hreflangs

@app.route("/", methods=["GET", "POST"])
def index():
    global total_urls, checked_urls, url_results, abort_signal
    
    if request.method == "POST":
        urls = request.form.get("urls").splitlines()
        rate = request.form.get("rate")
        total_urls = len(urls)
        checked_urls = 0
        url_results = []
        abort_signal = False

        for url in urls:
            if abort_signal:
                break

            result = process_url(url, rate)  # Pass 'url' and 'rate' to process_url
            url_results.append(result)
            socketio.emit('progress', {'results': [result]})
            time.sleep(60 / int(rate))
            
        return jsonify({"message": "Elaborazione degli URL", "results": url_results})

    return render_template("index.html")

# Helper Functions

def process_url(url, rate):
    result = {"url": url}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.3'}

    try:
        response = requests.get(url, headers=headers, timeout=5, verify=False, allow_redirects=False)
        result = process_response(result, response, url, headers)  # Pass 'url' and 'headers' to process_response
        
    except requests.exceptions.SSLError:
        result["status_code"] = "Error"
        result["final_url"] = "Error"
        result["ssl_valid"] = "No"
    except Exception as e:
        app.logger.error(f"Si è verificata un'eccezione: {e}")
        result["status_code"] = "Error"
        result["final_url"] = "Error"
        result["ssl_valid"] = "Impossibile Verificare"

    return result

def process_response(result, response, url, headers):
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
    result["redirect_chain_length"] = len(redirect_chain) if redirect_chain else '0'
    result["ssl_valid"] = "Yes" if response.url.startswith("https") else "N/A"

    soup = BeautifulSoup(response.text, 'html.parser')
    result['robots_txt_check'] = check_robots_txt(url)
    result['canonical_tag'] = check_canonical_tag(soup)
    title, meta_desc = analyze_meta_tags(soup)
    result['meta_title'] = title
    result['meta_description'] = meta_desc
    result['hreflangs'] = check_hreflang_tags(soup)

    return result


@app.route("/abort", methods=["POST"])
def abort_process():
    global abort_signal
    abort_signal = True
    return jsonify({"message": "Abortito"})

@app.route("/download_csv", methods=["GET"])
def download_csv():
    if len(url_results) == 0:
        return jsonify({"message": "Nessun risultato disponibile."})

    # Define the file path
    file_path = "checked_urls.csv"

    # Define the header for the CSV file
    fieldnames = ["url", "status_code", "final_url", "redirect_chain", "redirect_chain_length", 
                  "ssl_valid", "robots_txt_check", "canonical_tag", "meta_title", 
                  "meta_description", "hreflangs"]

    # Write the results to the CSV file
    with open(file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(url_results)

    return jsonify({"message": "CSV generato con successo.", "file_path": file_path})





if __name__ == "__main__":
    socketio.run(app, debug=True)
