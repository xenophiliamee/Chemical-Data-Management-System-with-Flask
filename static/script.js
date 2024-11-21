// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');
    const resultsDiv = document.getElementById('results');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            resultsDiv.innerHTML = '';
            data.forEach(item => {
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item ' + (item.status.includes('inserted') ? 'inserted' : 'existing');
                resultItem.textContent = `${item.status} (DOI: ${item.doi})`;
                resultsDiv.appendChild(resultItem);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerHTML = '<p>An error occurred while processing the file.</p>';
        });
    });
});