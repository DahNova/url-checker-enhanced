// Connette il socket al server
const socket = io.connect('http://' + document.domain + ':' + location.port);

// When the user clicks the 'Check URLs' button
document.getElementById('checkButton').addEventListener('click', function(e) {
    e.preventDefault();
    
    // Show loading state
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = '<div class="alert alert-info" role="alert">Checking URLs...</div>';
    
    // Create an object FormData with the form data
    const formData = new FormData(urlForm);
    // Send a POST request to the server with the form data
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Log the response from the server
        console.log(data);

        // Hide loading state
        alertContainer.innerHTML = '';

        // Add visual feedback for successful check
        alertContainer.innerHTML = '<div class="alert alert-success" role="alert">URLs checked successfully.</div>';
        setTimeout(() => {
            alertContainer.innerHTML = ''; // Clear the feedback after a few seconds
        }, 3000); // Adjust the timeout duration as needed

        // Per ogni risultato nel dato ricevuto
        const resultsElement = document.getElementById('results');
        data.results.forEach(result => {
            const tableRow = document.createElement('tr');
            // ... (rest of your code for creating table rows)
            resultsElement.appendChild(tableRow); 
        });
    })
    .catch(error => {
        console.error('Error:', error);

        // Hide loading state
        alertContainer.innerHTML = '';

        // Add visual feedback for error
        alertContainer.innerHTML = '<div class="alert alert-danger" role="alert">Error checking URLs. Please try again.</div>';
    });
});

// Quando riceve un evento 'progress' dal server
socket.on('progress', function(data) {
    const resultsElement = document.getElementById('results');
    // Per ogni risultato nel dato ricevuto
    data.results.forEach(result => {
        const tableRow = document.createElement('tr');

        // Crea una cella per l'URL e assegna il testo
        const urlCell = document.createElement('td');
        urlCell.textContent = result.url;
        tableRow.appendChild(urlCell);

        // Crea una cella per lo status code e assegna il testo
        const statusCodeCell = document.createElement('td');
        statusCodeCell.textContent = result.status_code;
        tableRow.appendChild(statusCodeCell);

        // Crea una cella per l'URL finale e assegna il testo
        const finalUrlCell = document.createElement('td');
        finalUrlCell.textContent = result.final_url;
        tableRow.appendChild(finalUrlCell);

        // Crea una cella per la validità SSL e assegna il testo
        const sslValidCell = document.createElement('td');
        sslValidCell.textContent = result.ssl_valid;
        tableRow.appendChild(sslValidCell);

        // Crea una cella per la catena di reindirizzamenti e assegna il testo, se non disponibile mette 'N/A'
        const redirectChainCell = document.createElement('td');
        redirectChainCell.textContent = result.redirect_chain || 'N/A';
        tableRow.appendChild(redirectChainCell);

        // Crea una cella per la lunghezza della catena di reindirizzamenti e assegna il testo, se non disponibile mette '0'
        const redirectChainLengthCell = document.createElement('td');
        redirectChainLengthCell.textContent = result.redirect_chain_length || '0';
        tableRow.appendChild(redirectChainLengthCell);

        // Crea una cella per la verifica di robots.txt e assegna il testo
        const robotsTxtCell = document.createElement('td');
        robotsTxtCell.textContent = result.robots_txt_check;
        tableRow.appendChild(robotsTxtCell);

        // Crea una cella per il tag canonico e assegna il testo
        const canonicalTagCell = document.createElement('td');
        canonicalTagCell.textContent = result.canonical_tag;
        tableRow.appendChild(canonicalTagCell);

        // Crea una cella per il titolo meta e assegna il testo
        const metaTitleCell = document.createElement('td');
        metaTitleCell.textContent = result.meta_title;
        tableRow.appendChild(metaTitleCell);

        // Crea una cella per la descrizione meta e assegna il testo
        const metaDescCell = document.createElement('td');
        metaDescCell.textContent = result.meta_description;
        tableRow.appendChild(metaDescCell);

        // Crea una cella per gli hreflangs e assegna il testo (congiunto da virgole)
        const hreflangsCell = document.createElement('td');
        hreflangsCell.textContent = result.hreflangs.join(', ');
        tableRow.appendChild(hreflangsCell);

        // Aggiunge la riga alla tabella dei risultati
        resultsElement.appendChild(tableRow); 
    });
});
