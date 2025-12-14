# Base64 Image Storage - Quick Reference

## 🎯 Quick Start

### Backend: Convert & Save Image

```python
from utils.image_utils import image_file_to_base64

# Convert screenshot to base64
base64_data = image_file_to_base64('/path/to/screenshot.png')

# Save to database
cursor.execute("""
    INSERT INTO generated_domains (url, title, domain, image_base64)
    VALUES (%s, %s, %s, %s)
""", (url, title, domain, base64_data))
```

### Frontend: Display Image

```tsx
import Base64Image from '@/components/ui/Base64Image'

<Base64Image 
    base64Data={domain.image_base64}
    alt="Screenshot"
    className="w-full h-auto rounded-lg"
/>
```

## 📋 Common Use Cases

### 1. Display Thumbnail in Table
```tsx
<Base64Image 
    base64Data={domain.image_base64}
    width={100}
    height={75}
    className="rounded cursor-pointer"
    onClick={() => openDetailModal(domain)}
/>
```

### 2. Full Image in Modal
```tsx
<Dialog open={isOpen}>
    <DialogContent className="max-w-4xl">
        <Base64Image 
            base64Data={selectedDomain.image_base64}
            alt={selectedDomain.title}
            className="w-full"
        />
    </DialogContent>
</Dialog>
```

### 3. Download Image
```tsx
import { useDownloadBase64Image } from '@/components/ui/Base64Image'

function DownloadButton({ domain }) {
    const { downloadImage } = useDownloadBase64Image()
    
    return (
        <Button onClick={() => downloadImage(
            domain.image_base64,
            `${domain.domain}.png`
        )}>
            📥 Download
        </Button>
    )
}
```

### 4. Convert PIL Image to Base64
```python
from PIL import Image
from utils.image_utils import pil_image_to_base64

# Create or process image
image = Image.open('screenshot.png')
image = image.resize((800, 600))

# Convert to base64
base64_data = pil_image_to_base64(image, format='PNG')
```

## 🔧 Database Migration

Run this SQL on existing database:

```bash
# Connect to database
docker exec -it prd_postgres psql -U postgres -d prd

# Run migration
\i /database/migrations/001_image_path_to_base64.sql
```

Or manually:

```sql
ALTER TABLE generated_domains RENAME COLUMN image_path TO image_base64;
ALTER TABLE object_detection RENAME COLUMN image_detected_path TO image_detected_base64;
ALTER TABLE object_detection ALTER COLUMN image_detected_base64 TYPE text;
```

## 📊 Data Format

### Accepted Formats:
1. **Data URI** (recommended): `data:image/png;base64,iVBORw0KG...`
2. **Raw Base64**: `iVBORw0KG...`

### Component Auto-Handles Both:
```tsx
// Both work!
<Base64Image base64Data="data:image/png;base64,iVBORw..." />
<Base64Image base64Data="iVBORw..." />
```

## ⚡ Performance Tips

### 1. Use Lazy Loading
```tsx
<Base64Image 
    base64Data={image}
    loading="lazy"
/>
```

### 2. Create Thumbnails
```python
from PIL import Image
from utils.image_utils import base64_to_pil_image, pil_image_to_base64

# Load full image
full_image = base64_to_pil_image(full_base64)

# Create thumbnail
thumbnail = full_image.resize((200, 150), Image.Resampling.LANCZOS)
thumbnail_base64 = pil_image_to_base64(thumbnail, format='JPEG')

# Store both
cursor.execute("""
    UPDATE generated_domains 
    SET image_base64 = %s, thumbnail_base64 = %s
    WHERE id_domain = %s
""", (full_base64, thumbnail_base64, domain_id))
```

### 3. Compress Images
```python
from PIL import Image
from utils.image_utils import base64_to_pil_image, pil_image_to_base64

image = base64_to_pil_image(original_base64)

# Compress as JPEG with quality 85
compressed_base64 = pil_image_to_base64(image, format='JPEG')
```

## 🐛 Troubleshooting

### Image Not Displaying?
```tsx
// Add fallback
<Base64Image 
    base64Data={domain.image_base64}
    fallbackSrc="/placeholder.png"
/>
```

### Check Image Size
```python
from utils.image_utils import get_image_size_kb

size_kb = get_image_size_kb(base64_data)
print(f"Image size: {size_kb:.2f} KB")
```

### Validate Base64
```python
def is_valid_base64(base64_string):
    try:
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',', 1)[1]
        base64.b64decode(base64_string)
        return True
    except:
        return False
```

## 📝 TypeScript Types

```typescript
// Add to your types file
interface Domain {
    id_domain: number
    url: string
    title: string
    domain: string
    image_base64: string  // Changed from image_path
    date_generated: string
}

interface ObjectDetection {
    id_detection: string
    id_domain: number
    label: boolean
    confidence_score: number
    image_detected_base64: string  // Changed from image_detected_path
    bounding_box: object
    ocr: object
}
```

## 🔗 Related Files

- **Backend Utils**: `/backend/utils/image_utils.py`
- **Frontend Component**: `/frontend/src/components/ui/Base64Image.tsx`
- **Migration SQL**: `/database/migrations/001_image_path_to_base64.sql`
- **Full Documentation**: `/docs/IMAGE_BASE64_MIGRATION.md`
