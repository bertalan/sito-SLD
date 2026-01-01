/**
 * Protezione email anti-scraping
 * Decodifica le email codificate in base64 a runtime
 */
document.addEventListener('DOMContentLoaded', function() {
    // Trova tutti gli elementi con data-email (codificata in base64)
    document.querySelectorAll('[data-email]').forEach(function(el) {
        try {
            const encodedEmail = el.getAttribute('data-email');
            const decodedEmail = atob(encodedEmail);
            
            // Se è un link, imposta href mailto:
            if (el.tagName === 'A') {
                el.href = 'mailto:' + decodedEmail;
            }
            
            // Se ha data-show-email, mostra l'email nel contenuto
            if (el.hasAttribute('data-show-email')) {
                el.textContent = decodedEmail;
            }
        } catch (e) {
            console.error('Errore decodifica email:', e);
        }
    });
});

/**
 * Helper per generare email codificate (per sviluppatori)
 * Usare in console: encodeEmail('info@studiolegaledonofrio.it')
 */
function encodeEmail(email) {
    return btoa(email);
}
