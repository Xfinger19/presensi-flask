// Main application JavaScript
class PresensiApp {
    constructor() {
        this.init();
    }

    init() {
        this.initEventListeners();
        this.loadDashboardStats();
        this.initCharts();
    }

    initEventListeners() {
        // Auto-update time every second
        this.updateCurrentTime();
        setInterval(() => this.updateCurrentTime(), 1000);

        // Notification handler
        this.setupNotifications();
    }

    updateCurrentTime() {
        const now = new Date();
        const timeElement = document.getElementById('currentTime');
        const dateElement = document.getElementById('currentDate');
        
        if (timeElement) {
            timeElement.textContent = now.toLocaleTimeString('id-ID');
        }
        
        if (dateElement) {
            dateElement.textContent = now.toLocaleDateString('id-ID', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        }
    }

    setupNotifications() {
        // Check if there are any flash messages from Flask
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            this.showNotification(message.textContent, 'info');
            setTimeout(() => {
                message.remove();
            }, 5000);
        });
    }

    async loadDashboardStats() {
        try {
            const response = await fetch('/api/dashboard/stats');
            if (response.ok) {
                const stats = await response.json();
                this.updateStatsDisplay(stats);
            }
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        const elements = {
            'totalKaryawan': stats.total_karyawan,
            'hadirHariIni': stats.hadir_hari_ini,
            'totalPresensi': stats.total_presensi,
            'rataKehadiran': stats.rata_kehadiran + '%'
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) {
                this.animateCounter(element, value);
            }
        }
    }

    animateCounter(element, target) {
        const duration = 2000;
        const steps = 60;
        const step = target / steps;
        let current = 0;

        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, duration / steps);
    }

    initCharts() {
        // Initialize any global charts here
        const ctx = document.getElementById('globalAttendanceChart');
        if (ctx) {
            this.createGlobalChart(ctx);
        }
    }

    createGlobalChart(ctx) {
        const chart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'],
                datasets: [{
                    label: 'Kehadiran Minggu Ini',
                    data: [65, 59, 80, 81, 56, 55, 40],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });
    }

    // Utility functions
    formatDate(date) {
        return new Date(date).toLocaleDateString('id-ID');
    }

    formatTime(time) {
        if (!time) return '-';
        return new Date(`1970-01-01T${time}`).toLocaleTimeString('id-ID', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Notification System
class NotificationSystem {
    static show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${this.getIcon(type)}"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add styles if not exists
        if (!document.getElementById('notification-styles')) {
            this.injectStyles();
        }

        document.body.appendChild(notification);

        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);

        return notification;
    }

    static getIcon(type) {
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };
        return icons[type] || 'fa-info-circle';
    }

    static injectStyles() {
        const styles = `
            <style>
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    min-width: 300px;
                    max-width: 500px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    border-left: 4px solid #3498db;
                    animation: slideInRight 0.3s ease;
                }

                .notification-success {
                    border-left-color: #27ae60;
                }

                .notification-error {
                    border-left-color: #e74c3c;
                }

                .notification-warning {
                    border-left-color: #f39c12;
                }

                .notification-info {
                    border-left-color: #3498db;
                }

                .notification-content {
                    padding: 16px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .notification-content i:first-child {
                    font-size: 1.2em;
                }

                .notification-content span {
                    flex: 1;
                    font-weight: 500;
                }

                .notification-content button {
                    background: none;
                    border: none;
                    cursor: pointer;
                    opacity: 0.7;
                    padding: 4px;
                }

                .notification-content button:hover {
                    opacity: 1;
                }

                @keyframes slideInRight {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', styles);
    }
}

// API Service Class
class ApiService {
    static async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    static async get(url) {
        try {
            const response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
}

// Presensi Handler Class
class PresensiHandler {
    constructor() {
        this.selectedKaryawanId = null;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const selectKaryawan = document.getElementById('selectKaryawan');
        if (selectKaryawan) {
            selectKaryawan.addEventListener('change', (e) => {
                this.selectedKaryawanId = e.target.value;
                if (this.selectedKaryawanId) {
                    this.loadRecentPresensi(this.selectedKaryawanId);
                }
            });
        }

        // Enter key support for forms
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const activeElement = document.activeElement;
                if (activeElement.form && activeElement.type !== 'textarea') {
                    e.preventDefault();
                }
            }
        });
    }

    async checkIn() {
        if (!this.validateSelection()) return;

        const data = {
            karyawan_id: this.selectedKaryawanId,
            status: document.getElementById('selectStatus').value,
            keterangan: document.getElementById('inputKeterangan').value,
            lokasi: this.getUserLocation()
        };

        try {
            this.showLoading('checkin-btn', 'Mencatat...');
            const result = await ApiService.post('/api/checkin', data);

            if (result.success) {
                NotificationSystem.show('Check-in berhasil dicatat!', 'success');
                this.clearForm();
                this.loadRecentPresensi(this.selectedKaryawanId);
                this.updateDashboardIfExists();
            } else {
                NotificationSystem.show(result.message, 'error');
            }
        } catch (error) {
            NotificationSystem.show('Terjadi kesalahan saat check-in', 'error');
        } finally {
            this.hideLoading('checkin-btn', 'Check In');
        }
    }

    async checkOut() {
        if (!this.validateSelection()) return;

        const data = {
            karyawan_id: this.selectedKaryawanId
        };

        try {
            this.showLoading('checkout-btn', 'Mencatat...');
            const result = await ApiService.post('/api/checkout', data);

            if (result.success) {
                NotificationSystem.show('Check-out berhasil dicatat!', 'success');
                this.loadRecentPresensi(this.selectedKaryawanId);
                this.updateDashboardIfExists();
            } else {
                NotificationSystem.show(result.message, 'error');
            }
        } catch (error) {
            NotificationSystem.show('Terjadi kesalahan saat check-out', 'error');
        } finally {
            this.hideLoading('checkout-btn', 'Check Out');
        }
    }

    validateSelection() {
        if (!this.selectedKaryawanId) {
            NotificationSystem.show('Pilih karyawan terlebih dahulu!', 'warning');
            return false;
        }
        return true;
    }

    async loadRecentPresensi(karyawanId) {
        try {
            const data = await ApiService.get(`/api/presensi/${karyawanId}`);
            this.renderRecentPresensi(data);
        } catch (error) {
            console.error('Error loading presensi:', error);
            document.getElementById('recentPresensi').innerHTML = 
                '<p class="text-red-500">Gagal memuat riwayat presensi</p>';
        }
    }

    renderRecentPresensi(data) {
        const container = document.getElementById('recentPresensi');
        
        if (!data || data.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">Belum ada riwayat presensi.</p>';
            return;
        }

        const html = `
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white rounded-lg overflow-hidden">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tanggal</th>
                            <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Masuk</th>
                            <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Keluar</th>
                            <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Durasi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        ${data.map(item => `
                            <tr class="hover:bg-gray-50 transition duration-150">
                                <td class="py-3 px-4 whitespace-nowrap">${this.formatDate(item.tanggal)}</td>
                                <td class="py-3 px-4 whitespace-nowrap">${this.formatTime(item.waktu_masuk)}</td>
                                <td class="py-3 px-4 whitespace-nowrap">${this.formatTime(item.waktu_keluar)}</td>
                                <td class="py-3 px-4 whitespace-nowrap">
                                    <span class="px-2 py-1 rounded-full text-xs font-medium ${this.getStatusClass(item.status)}">
                                        ${item.status}
                                    </span>
                                </td>
                                <td class="py-3 px-4 whitespace-nowrap">${this.calculateDuration(item.waktu_masuk, item.waktu_keluar)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;
    }

    getStatusClass(status) {
        const classes = {
            'Hadir': 'bg-green-100 text-green-800',
            'Izin': 'bg-blue-100 text-blue-800',
            'Sakit': 'bg-orange-100 text-orange-800',
            'Cuti': 'bg-purple-100 text-purple-800'
        };
        return classes[status] || 'bg-gray-100 text-gray-800';
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('id-ID', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    formatTime(timeString) {
        if (!timeString) return '-';
        return new Date(`1970-01-01T${timeString}`).toLocaleTimeString('id-ID', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    calculateDuration(masuk, keluar) {
        if (!masuk || !keluar) return '-';
        
        const start = new Date(`1970-01-01T${masuk}`);
        const end = new Date(`1970-01-01T${keluar}`);
        const diff = end - start;
        
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        
        return `${hours}j ${minutes}m`;
    }

    getUserLocation() {
        // In a real app, you might get this from GPS or IP
        return 'Kantor Pusat';
    }

    clearForm() {
        document.getElementById('inputKeterangan').value = '';
    }

    showLoading(buttonId, text) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${text}`;
            button.disabled = true;
        }
    }

    hideLoading(buttonId, originalText) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    async updateDashboardIfExists() {
        // If we're on dashboard page, refresh the data
        if (window.location.pathname === '/dashboard') {
            // You can trigger a page refresh or update specific elements
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    }
}

// Dashboard Chart Manager
class DashboardCharts {
    static init() {
        this.initAttendanceChart();
        this.initDivisionChart();
        this.initWeeklyTrend();
    }

    static initAttendanceChart() {
        const ctx = document.getElementById('attendanceChart');
        if (!ctx) return;

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'],
                datasets: [{
                    label: 'Jumlah Hadir',
                    data: [18, 19, 16, 17, 15, 8],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Kehadiran Minggu Ini'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 5
                        }
                    }
                }
            }
        });
    }

    static initDivisionChart() {
        const ctx = document.getElementById('divisionChart');
        if (!ctx) return;

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['IT', 'HR', 'Marketing', 'Finance', 'Operations'],
                datasets: [{
                    data: [25, 15, 20, 18, 22],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'Distribusi Karyawan per Divisi'
                    }
                }
            }
        });
    }

    static initWeeklyTrend() {
        const ctx = document.getElementById('weeklyTrend');
        if (!ctx) return;

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Minggu 1', 'Minggu 2', 'Minggu 3', 'Minggu 4'],
                datasets: [{
                    label: 'Tingkat Kehadiran (%)',
                    data: [85, 88, 92, 90],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tren Kehadiran Bulan Ini'
                    }
                },
                scales: {
                    y: {
                        min: 80,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize main app
    window.presensiApp = new PresensiApp();
    
    // Initialize presensi handler if on presensi page
    if (window.location.pathname === '/presensi' || window.location.pathname === '/') {
        window.presensiHandler = new PresensiHandler();
    }
    
    // Initialize charts if on dashboard page
    if (window.location.pathname === '/dashboard') {
        DashboardCharts.init();
    }

    // Add current time display to all pages
    const addCurrentTime = () => {
        const now = new Date();
        const timeElements = document.querySelectorAll('.current-time');
        timeElements.forEach(element => {
            element.textContent = now.toLocaleTimeString('id-ID');
        });
    };

    // Update time every second
    setInterval(addCurrentTime, 1000);
    addCurrentTime();
});

// Global functions for HTML onclick attributes
function checkIn() {
    if (window.presensiHandler) {
        window.presensiHandler.checkIn();
    }
}

function checkOut() {
    if (window.presensiHandler) {
        window.presensiHandler.checkOut();
    }
}

// Utility function for showing notifications globally
function showNotification(message, type = 'info') {
    NotificationSystem.show(message, type);
}

// Export for module usage (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PresensiApp, PresensiHandler, ApiService, NotificationSystem };
}