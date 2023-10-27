const socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('progress', function(data) {
    const resultsElement = document.getElementById('results');
    resultsElement.innerHTML = '';
    data.results.forEach(result => {
        const tableRow = document.createElement('tr');

        const urlCell = document.createElement('td');
        urlCell.textContent = result.url;
        tableRow.appendChild(urlCell);

        const statusCodeCell = document.createElement('td');
        statusCodeCell.textContent = result.status_code;
        tableRow.appendChild(statusCodeCell);

        const finalUrlCell = document.createElement('td');
        finalUrlCell.textContent = result.final_url;
        tableRow.appendChild(finalUrlCell);

        const sslValidCell = document.createElement('td');
        sslValidCell.textContent = result.ssl_valid;
        tableRow.appendChild(sslValidCell);

        const redirectChainCell = document.createElement('td');
        redirectChainCell.textContent = result.redirect_chain || 'N/A';
        tableRow.appendChild(redirectChainCell);

        const redirectChainLenghtCell = document.createElement('td');
        redirectChainLenghtCell.textContent = result.redirect_chain || '0';
        tableRow.appendChild(redirectChainLenghtCell);

        resultsElement.appendChild(tableRow);
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const urlForm = document.getElementById('urlForm');
    urlForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(urlForm);
        fetch('/', {
            method: 'POST',
            body: formData
        }).then(response => response.json()).then(data => console.log(data));
    });

    const abortBtn = document.getElementById('abortBtn');
    abortBtn.addEventListener('click', function() {
        socket.emit('abort', {});
        fetch('/abort', {
            method: 'POST'
        }).then(response => response.json()).then(data => console.log(data));
    });
});
