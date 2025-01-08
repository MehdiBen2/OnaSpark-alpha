document.addEventListener('DOMContentLoaded', () => {
    const logoSlider = document.querySelector('.logo-slider');
    
    logoSlider.addEventListener('mouseover', () => {
        logoSlider.style.animationPlayState = 'paused';
    });
    
    logoSlider.addEventListener('mouseout', () => {
        logoSlider.style.animationPlayState = 'running';
    });

    const orbitCircles = document.querySelectorAll('.orbit-circle');
    
    // Optional: Add interactive hover effects
    orbitCircles.forEach(circle => {
        circle.addEventListener('mouseenter', () => {
            circle.style.transform = 'scale(1.1)';
        });
        
        circle.addEventListener('mouseleave', () => {
            circle.style.transform = 'scale(1)';
        });
    });

    // Optional: Add subtle rotation on page load
    window.addEventListener('load', () => {
        orbitCircles.forEach((circle, index) => {
            circle.style.animationDelay = `${index * 0.2}s`;
        });
    });
});
