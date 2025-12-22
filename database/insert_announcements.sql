-- Insert Announcements Data
-- Announcement 1: System Launch
INSERT INTO public.announcements (title, content, category, created_by, created_at, updated_at)
VALUES (
    '🎉 Launching Dashboard Chatbot System',
    'Kami dengan bangga mengumumkan peluncuran resmi Dashboard Chatbot System yang mengintegrasikan berbagai layanan AI canggih. Sistem ini dilengkapi dengan tiga layanan utama: Object Detection untuk analisis gambar otomatis, Chatbot AI untuk interaksi cerdas, dan Domain Generator untuk crawling dan analisis domain secara real-time. 

Fitur-fitur unggulan:
• Real-time Service Health Monitoring - Pantau status semua layanan AI setiap 10 detik
• Advanced Data Table - Pencarian, filtering, sorting, dan pagination yang powerful
• Admin Panel - Kelola users, konfigurasi sistem, dan monitoring resource
• Interactive Chatbot - Tanya jawab tentang data hasil pemrosesan
• Responsive Design - Akses dari desktop, tablet, atau mobile dengan tampilan optimal

Sistem ini telah melalui tahap testing menyeluruh dan siap digunakan untuk production. Silakan login menggunakan kredensial yang telah diberikan dan jelajahi semua fitur yang tersedia. Untuk bantuan atau pertanyaan, hubungi tim administrator.

Selamat menggunakan Dashboard Chatbot System!',
    'announcement',
    'administrator',
    '2025-12-21 08:00:00+00',
    '2025-12-21 08:00:00+00'
);

-- Announcement 2: System Update
INSERT INTO public.announcements (title, content, category, created_by, created_at, updated_at)
VALUES (
    '🚀 Update Sistem v1.2.0 - Peningkatan Performa & Fitur Baru',
    'Kami telah merilis update sistem versi 1.2.0 dengan berbagai peningkatan performa dan fitur baru yang signifikan.

Apa yang Baru:
• Performance Optimization - Response time API berkurang hingga 40% dengan implementasi caching strategy
• Enhanced Security - Penambahan rate limiting dan improved JWT token validation
• Real-time Notifications - Sistem notifikasi real-time untuk update status layanan
• Bulk Operations - Fitur bulk delete dan export data dalam format CSV/Excel
• Advanced Filtering - Filter data berdasarkan multiple criteria dengan date range picker
• Audit Logs Export - Export audit logs untuk compliance dan reporting
• Dark Mode Support - Tema gelap untuk kenyamanan mata saat bekerja malam hari
• Mobile Responsive - Perbaikan tampilan untuk pengalaman mobile yang lebih baik

Bug Fixes:
• Fixed: Image display issue pada Detail Modal
• Fixed: Duplicate key errors pada Data Table
• Fixed: CORS issue saat memanggil RunPod API
• Fixed: Service status count tidak akurat

Database Changes:
• Migrasi kolom image_final_path ke TEXT type untuk support base64 encoding
• Penambahan index pada kolom yang sering di-query untuk performa optimal

Update ini akan diterapkan pada tanggal 21 Desember 2025 pukul 02:00 WIB. Sistem akan mengalami downtime sekitar 15 menit selama proses update. Mohon simpan pekerjaan Anda sebelum waktu tersebut.

Terima kasih atas pengertiannya!',
    'update',
    'administrator',
    '2025-12-20 10:30:00+00',
    '2025-12-20 10:30:00+00'
);
