document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.fluent-main-content');
    const sidebarLogo = document.querySelector('.sidebar-logo');

    if (sidebarToggle && sidebar && mainContent) {
        sidebarToggle.addEventListener('click', function() {
            // Toggle sidebar width
            if (sidebar.classList.contains('sidebar-collapsed')) {
                // Expand sidebar
                sidebar.classList.remove('sidebar-collapsed');
                sidebar.style.width = '280px';
                mainContent.style.width = 'calc(100% - 280px)';
                mainContent.style.marginLeft = '0';
                if (sidebarLogo) {
                    sidebarLogo.style.transform = 'translateX(0)';
                    sidebarLogo.style.opacity = '1';
                }
            } else {
                // Collapse sidebar
                sidebar.classList.add('sidebar-collapsed');
                sidebar.style.width = '60px';
                mainContent.style.width = 'calc(100% - 60px)';
                mainContent.style.marginLeft = '0';
                if (sidebarLogo) {
                    sidebarLogo.style.transform = 'translateX(-100%)';
                    sidebarLogo.style.opacity = '0';
                }
            }
        });
    }
});
