from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize global variables
total_urls = 0
checked_urls = 0
url_results = []
abort_signal = False

# Function to check robots.txt
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

# Function to check canonical tag
def check_canonical_tag(soup):
    canonical_tag = soup.find("link", {"rel": "canonical"})
    return canonical_tag["href"] if canonical_tag else None

# Function to analyze meta tags (title and description)
def analyze_meta_tags(soup):
    title_tag = soup.find("title")
    meta_desc_tag = soup.find("meta", {"name": "description"})
    title = title_tag.string if title_tag else None
    meta_desc = meta_desc_tag["content"] if meta_desc_tag else None
    return title, meta_desc

# Function to check hreflang tags
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
                result["redirect_chain_length"] = len(redirect_chain) if redirect_chain else '0'
                result["ssl_valid"] = "Yes" if response.url.startswith("https") else "N/A"

                # Robots.txt Verification
                result['robots_txt_check'] = check_robots_txt(url)

                # Use response.text for BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Canonical Tag Check
                result['canonical_tag'] = check_canonical_tag(soup)

                # Meta Tag Analysis
                title, meta_desc = analyze_meta_tags(soup)
                result['meta_title'] = title
                result['meta_description'] = meta_desc

                # Hreflang Tag Check
                result['hreflangs'] = check_hreflang_tags(soup)

                # Add result to url_results
                url_results.append(result)

            except requests.exceptions.SSLError:
                result["status_code"] = "Error"
                result["final_url"] = "Error"
                result["ssl_valid"] = "No"
            except Exception as e:
                app.logger.error(f"Exception occurred: {e}")
                result["status_code"] = "Error"
                result["final_url"] = "Error"
                result["ssl_valid"] = "Can't Check"



    #    url_results.append(result)
        socketio.emit('progress', {'results': url_results})
        
        return jsonify({"message": "Processing URLs", "results": url_results})

    return render_template("index.html")

@app.route("/abort", methods=["POST"])
def abort_process():
    global abort_signal
    abort_signal = True
    return jsonify({"message": "Aborted"})

if __name__ == "__main__":
    socketio.run(app, debug=True)
