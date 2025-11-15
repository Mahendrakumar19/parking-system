// Navigation Component
function createNavbar(activePage = 'dashboard') {
    const user = JSON.parse(localStorage.getItem('currentUser') || localStorage.getItem('user') || '{}');
    
    const navbar = `
        <nav class="navbar">
            <div class="nav-container">
                <a href="index.html" class="nav-brand">
                    🅿️ Parking System
                </a>
                
                <ul class="nav-menu">
                    <li class="nav-item">
                        <a href="index.html" class="nav-link ${activePage === 'home' ? 'active' : ''}">
                            🏠 Home
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="index.html#dashboard" class="nav-link ${activePage === 'dashboard' ? 'active' : ''}">
                            � Dashboard
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="scanner.html" class="nav-link ${activePage === 'scanner' ? 'active' : ''}">
                            � Scanner
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="scan-history.html" class="nav-link ${activePage === 'scan-history' ? 'active' : ''}">
                            � Scan History
                        </a>
                    </li>
                </ul>
                
                <div class="nav-user">
                    <span class="user-name">👤 ${user.name || user.email || 'Guest'}</span>
                    <button class="nav-logout" onclick="logout()">Logout</button>
                </div>
            </div>
        </nav>
    `;
    
    return navbar;
}

function logout() {
    localStorage.removeItem('user');
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}

// Auto-inject navbar if navbarContainer exists
document.addEventListener('DOMContentLoaded', () => {
    const navbarContainer = document.getElementById('navbarContainer');
    if (navbarContainer) {
        const activePage = navbarContainer.dataset.page || 'dashboard';
        navbarContainer.innerHTML = createNavbar(activePage);
    }
});
