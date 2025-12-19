# Fix: RunPod Process API JSON Parse Error

## 🐛 Masalah

Frontend menampilkan error saat memanggil RunPod API:

```
Unexpected token 'S', "Starting c"... is not valid JSON
```

## 🔍 Root Cause

API route `/api/runpod-process/route.ts` mencoba mem-parse response dari RunPod API sebagai JSON menggunakan `response.json()`, tapi RunPod API mengembalikan **text response** (bukan JSON).

Response dari RunPod API:
```
Starting crawler...
```

Kode lama:
```typescript
const data = await response.json()  // ❌ Error jika response bukan JSON
```

## ✅ Solusi

Menambahkan fallback untuk handle text response:

```typescript
// Check content-type header
const contentType = response.headers.get('content-type')
let data: any

if (contentType?.includes('application/json')) {
    try {
        data = await response.json()
    } catch (e) {
        // Fallback to text if JSON parsing fails
        const textData = await response.text()
        data = { message: textData, status: 'success' }
    }
} else {
    // Non-JSON response, treat as text
    const textData = await response.text()
    data = { message: textData, status: 'success' }
}
```

## 📝 Perubahan yang Dilakukan

**File**: `/home/ubuntu/web-app/frontend/src/app/api/runpod-process/route.ts`

- Menambahkan check untuk `content-type` header
- Menambahkan try-catch untuk graceful fallback
- Wrap text response dalam object JSON: `{ message: textData, status: 'success' }`

## 🧪 Testing

Setelah fix ini, frontend akan:
1. Coba parse sebagai JSON jika `content-type` adalah `application/json`
2. Jika gagal atau bukan JSON, treat sebagai text
3. Wrap text response dalam object JSON agar frontend bisa handle dengan baik

## 📊 Impact

- **Sebelum**: Error "Unexpected token" saat RunPod API return text
- **Sesudah**: Bisa handle baik JSON maupun text response dari RunPod API

---
**Fixed**: 2025-12-19  
**Related**: Domain Generator integration with RunPod API
