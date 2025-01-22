document.addEventListener('DOMContentLoaded', function() {
    const cyclingTextElement = document.getElementById('cyclingText');
    const cyclingWords = [
        'De Données',
        'De Bilans', 
        'De Rapports', 
        'De Processus', 
        'D\'Informations'
    ];
    
    let currentIndex = 0;

    function cycleText() {
        // Slide out current text
        cyclingTextElement.classList.add('slide-out');
        
        setTimeout(() => {
            // Change text
            currentIndex = (currentIndex + 1) % cyclingWords.length;
            cyclingTextElement.textContent = cyclingWords[currentIndex];
            
            // Remove slide-out class
            cyclingTextElement.classList.remove('slide-out');
            
            // Slide in new text
            cyclingTextElement.classList.add('slide-in');
            
            // Remove slide-in class after animation
            setTimeout(() => {
                cyclingTextElement.classList.remove('slide-in');
            }, 500);
        }, 500);
    }

    // Initial cycle setup
    setInterval(cycleText, 2200);
});
