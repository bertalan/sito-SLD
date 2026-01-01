/**
 * Protezione email anti-scraping
 * Decodifica le email codificate in base64 solo su interazione utente
 * I bot che non eseguono JS o non interagiscono non vedranno mai le email reali
 */
document.addEventListener('DOMContentLoaded', function() {
    // Trova tutti gli elementi con data-email (codificata in base64)
    document.querySelectorAll('[data-email]').forEach(function(el) {
        // Decodifica solo al click
        el.addEventListener('click', function(e) {
            e.preventDefault();
            try {
                const encodedEmail = el.getAttribute('data-email');
                const decodedEmail = atob(encodedEmail);
                
                // Apri il client email
                window.location.href = 'mailto:' + decodedEmail;
            } catch (err) {
                console.error('Errore decodifica email:', err);
            }
        });
        
        // Mostra l'email al passaggio del mouse (hover)
        el.addEventListener('mouseenter', function() {
            if (!el.dataset.decoded) {
                try {
                    const encodedEmail = el.getAttribute('data-email');
                    const decodedEmail = atob(encodedEmail);
                    
                    // Se ha data-show-email, mostra l'email nel contenuto
                    if (el.hasAttribute('data-show-email')) {
                        el.textContent = decodedEmail;
                        el.dataset.decoded = 'true';
                    }
                } catch (err) {
                    console.error('Errore decodifica email:', err);
                }
            }
        });
        
        // Imposta cursor pointer per indicare che è cliccabile
        el.style.cursor = 'pointer';
    });
});

/**
 * Helper per generare email codificate (per sviluppatori)
 * Usare in console: encodeEmail('info@studiolegaledonofrio.it')
 */
function encodeEmail(email) {
    return btoa(email);
}
