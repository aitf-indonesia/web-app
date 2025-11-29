# PRD Analyst Dashboard v2

Dashboard analisis untuk review dan triage hasil deteksi konten. Dibangun dengan arsitektur full-stack menggunakan **Next.js** (App Router) + **FastAPI** backend, dengan integrasi database PostgreSQL dan AI assistant powered by Google Gemini.

## 📋 Tech Stack

### **Frontend**
- Next.js 16 (App Router) + React 19 + TypeScript
- TailwindCSS v4 + Radix UI + Lucide Icons
- SWR untuk data fetching
- Recharts untuk visualisasi

### **Backend**
- FastAPI (Python) + SQLAlchemy
- PostgreSQL Database
- Google Gemini API
- Uvicorn (ASGI Server)

## 🛠️ Setup & Installation

### **Prerequisites**
- VPS dengan Ubuntu 20.04+
- Conda (Miniconda/Anaconda) sudah terinstall
- Minimal 2GB RAM, 10GB disk space

### **Quick Start**

```bash
# 1. Clone repository
cd /home/ubuntu
git clone <repository-url> tim6_prd_workdir
cd tim6_prd_workdir

# 2. Run setup script (requires sudo)
sudo bash setup-native-vps.sh

# 3. Configure environment
nano .env  # Update GEMINI_API_KEY dan konfigurasi lainnya
```

Setup script akan menginstall:
- ✅ Conda environment `prd6` dengan Python 3.11
- ✅ Node.js 20 + pnpm
- ✅ PostgreSQL 14
- ✅ Chrome + ChromeDriver
- ✅ Semua dependencies dan database schema

## 🎯 Menjalankan Aplikasi

### **Start Application**

```bash
# Development mode (default)
./start-app.sh

# atau
./start-app.sh dev

# Production mode
./start-app.sh prod
```

Script akan:
- ✅ Mengaktifkan conda environment `prd6`
- ✅ Membersihkan port yang sudah digunakan (3000, 8000)
- ✅ Menjalankan backend (FastAPI) di port 8000
- ✅ Menjalankan frontend (Next.js) di port 3000
- ✅ Menampilkan informasi PID dan lokasi log

### **Stop Application**

```bash
./stop-app.sh
```

Script akan:
- ✅ Menghentikan frontend (port 3000)
- ✅ Menghentikan backend (port 8000)
- ✅ Memverifikasi semua proses sudah berhenti

### **View Logs**

```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log

# Follow both logs
tail -f /tmp/backend.log /tmp/frontend.log
```

## 📁 Struktur Project

```
tim6_prd_workdir/
├── backend/                    # FastAPI backend
│   ├── main.py                # Entry point
│   ├── db.py                  # Database connection
│   ├── routes/                # API endpoints
│   ├── database/schema.sql    # Database schema
│   └── requirements.txt
├── frontend/                   # Next.js frontend
│   ├── src/app/               # App Router pages
│   ├── src/components/        # React components
│   └── package.json
├── start-app.sh               # Start application script
├── stop-app.sh                # Stop application script
├── setup-native-vps.sh        # VPS setup script
├── .env                       # Environment config
└── README.md
```

## 💻 Development Commands

### **Database Management**
```bash
# Access PostgreSQL
/home/ubuntu/postgresql/bin/psql -U postgres -d prd

# Seed data dari CSV
cd backend
conda activate prd6
python seed_data.py

# Backup database
/home/ubuntu/postgresql/bin/pg_dump -U postgres prd > backup_$(date +%Y%m%d).sql
```

### **Manual Development**
```bash
# Activate conda environment
conda activate prd6

# Run backend manually
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run frontend manually (in another terminal)
cd frontend
pnpm run dev
```

## 🐛 Troubleshooting

### **Port sudah digunakan**
```bash
# Kill port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### **Backend tidak bisa connect ke database**
```bash
# Start PostgreSQL
/home/ubuntu/postgresql/bin/pg_ctl -D /home/ubuntu/postgresql/data start

# Test koneksi
/home/ubuntu/postgresql/bin/psql -U postgres -d prd
```

### **Module not found di backend**
```bash
conda activate prd6
cd backend
pip install -r requirements.txt
```

### **pnpm command not found**
```bash
source ~/.bashrc
# atau
npm install -g pnpm
```

📚 **Troubleshooting lengkap**: Lihat [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## 📝 Environment Variables

Copy dari `env.example` dan sesuaikan:

```bash
cp env.example .env
nano .env
```

**Required variables:**
- `DB_URL` - PostgreSQL connection string
- `FRONTEND_URL` - Frontend URL (untuk CORS)
