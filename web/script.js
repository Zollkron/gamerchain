// OS Detection and Auto-Download
function detectOS() {
    const userAgent = window.navigator.userAgent.toLowerCase();
    const platform = window.navigator.platform.toLowerCase();
    
    if (platform.includes('win')) {
        return 'windows';
    } else if (platform.includes('mac')) {
        return 'macos';
    } else if (platform.includes('linux')) {
        return 'linux';
    }
    
    // Fallback detection
    if (userAgent.includes('win')) {
        return 'windows';
    } else if (userAgent.includes('mac')) {
        return 'macos';
    } else if (userAgent.includes('linux') || userAgent.includes('x11')) {
        return 'linux';
    }
    
    return 'windows'; // Default fallback
}

// Update download button based on detected OS
function updateDownloadButton() {
    const detectedOS = detectOS();
    const downloadBtn = document.getElementById('downloadBtn');
    const downloadText = document.getElementById('downloadText');
    const downloadOS = document.getElementById('downloadOS');
    
    const osNames = {
        'windows': 'Windows',
        'macos': 'macOS',
        'linux': 'Linux'
    };
    
    downloadOS.textContent = `para ${osNames[detectedOS]}`;
    
    // Highlight the recommended download card
    const downloadCards = document.querySelectorAll('.download-card');
    downloadCards.forEach(card => {
        if (card.dataset.os === detectedOS) {
            card.classList.add('recommended');
        }
    });
    
    // Set click handler for main download button
    downloadBtn.onclick = () => downloadWallet(detectedOS);
}

// Download wallet function
function downloadWallet(os) {
    // URLs for wallet downloads (these would be actual download links in production)
    const downloadURLs = {
        'windows': '/downloads/PlayerGold-Setup-Windows.exe',
        'macos': '/downloads/PlayerGold-Setup-macOS.dmg',
        'linux': '/downloads/PlayerGold-Setup-Linux.AppImage'
    };
    
    const url = downloadURLs[os];
    
    // In production, this would trigger the actual download
    console.log(`Downloading PlayerGold wallet for ${os} from ${url}`);
    
    // Show download notification
    showNotification(`Iniciando descarga para ${os}...`);
    
    // In a real implementation, you would trigger the download:
    // window.location.href = url;
    // or use a more sophisticated download mechanism
}

// Show notification
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Smooth scrolling for navigation links
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Navbar scroll effect
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.style.background = 'rgba(15, 23, 42, 0.95)';
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
        } else {
            navbar.style.background = 'rgba(15, 23, 42, 0.8)';
            navbar.style.boxShadow = 'none';
        }
        
        lastScroll = currentScroll;
    });
}

// Intersection Observer for animations
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all feature cards and tech items
    document.querySelectorAll('.feature-card, .tech-item, .pillar, .download-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(el);
    });
}

// Add CSS animations
function addAnimations() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    updateDownloadButton();
    initSmoothScroll();
    initNavbarScroll();
    initScrollAnimations();
    addAnimations();
    
    console.log('PlayerGold landing page initialized');
    console.log('Detected OS:', detectOS());
});

// Handle window resize
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        console.log('Window resized');
    }, 250);
});
