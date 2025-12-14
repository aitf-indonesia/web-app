# Image Storage Migration: File Path to Base64

## Overview
Sistem penyimpanan gambar telah diubah dari file path menjadi base64 encoding yang disimpan langsung di database.

## Changes Made

### 1. Database Schema Changes

#### Tables Modified:
- **`generated_domains`**: `image_path` → `image_base64`
- **`object_detection`**: `image_detected_path` → `image_detected_base64`

#### Migration Script:
```sql
-- Run this on existing database
ALTER TABLE public.generated_domains 
RENAME COLUMN image_path TO image_base64;

ALTER TABLE public.object_detection 
RENAME COLUMN image_detected_path TO image_detected_base64;

ALTER TABLE public.object_detection 
ALTER COLUMN image_detected_base64 TYPE text;
```

Location: `/database/migrations/001_image_path_to_base64.sql`

### 2. Backend Changes

#### New Utility Module: `utils/image_utils.py`

**Functions:**
- `image_file_to_base64(file_path)` - Convert image file to base64 data URI
- `base64_to_image_file(base64_string, output_path)` - Save base64 as image file
- `pil_image_to_base64(image, format)` - Convert PIL Image to base64
- `base64_to_pil_image(base64_string)` - Convert base64 to PIL Image
- `get_image_size_kb(base64_string)` - Get image size in KB

**Usage Example:**
```python
from utils.image_utils import image_file_to_base64, pil_image_to_base64

# Convert file to base64
base64_data = image_file_to_base64('/path/to/screenshot.png')

# Save to database
cursor.execute("""
    UPDATE generated_domains 
    SET image_base64 = %s 
    WHERE id_domain = %s
""", (base64_data, domain_id))
```

### 3. Frontend Changes

#### New Component: `components/ui/Base64Image.tsx`

**Component:**
```tsx
import Base64Image from '@/components/ui/Base64Image'

<Base64Image 
    base64Data={domain.image_base64}
    alt="Screenshot"
    className="w-full h-auto"
    width={800}
    height={600}
/>
```

**Props:**
- `base64Data` (required): Base64 string (with or without data URI prefix)
- `alt`: Alt text for image
- `className`: CSS classes
- `width`, `height`: Dimensions (optional)
- `fallbackSrc`: Fallback image if error
- `onClick`: Click handler

**Hooks:**
```tsx
import { useDownloadBase64Image } from '@/components/ui/Base64Image'

const { downloadImage } = useDownloadBase64Image()

// Download image
downloadImage(base64Data, 'screenshot.png')
```

**Utilities:**
```tsx
import { getBase64ImageDimensions } from '@/components/ui/Base64Image'

const { width, height } = await getBase64ImageDimensions(base64Data)
```

## Benefits

### ✅ Advantages:
1. **No File System Dependencies** - Images stored directly in database
2. **Easier Backup** - Database backup includes all images
3. **Simpler Deployment** - No need to sync image directories
4. **Atomic Operations** - Image and metadata saved together
5. **Better for Docker** - No volume mounting issues

### ⚠️ Considerations:
1. **Database Size** - Base64 increases size by ~33%
2. **Query Performance** - Larger row sizes
3. **Memory Usage** - Loading images into memory

## Migration Guide

### For Existing Data:

```python
# Python script to migrate existing images
from utils.image_utils import image_file_to_base64
import psycopg2

conn = psycopg2.connect("dbname=prd user=postgres")
cursor = conn.cursor()

# Get all domains with image paths
cursor.execute("SELECT id_domain, image_path FROM generated_domains WHERE image_path IS NOT NULL")

for domain_id, image_path in cursor.fetchall():
    # Convert to base64
    base64_data = image_file_to_base64(image_path)
    
    if base64_data:
        # Update database
        cursor.execute("""
            UPDATE generated_domains 
            SET image_base64 = %s 
            WHERE id_domain = %s
        """, (base64_data, domain_id))

conn.commit()
conn.close()
```

### For New Screenshots:

```python
# When capturing screenshot
from selenium import webdriver
from utils.image_utils import pil_image_to_base64
from PIL import Image
import io

# Capture screenshot
screenshot = driver.get_screenshot_as_png()
image = Image.open(io.BytesIO(screenshot))

# Convert to base64
base64_data = pil_image_to_base64(image, format='PNG')

# Save to database
cursor.execute("""
    INSERT INTO generated_domains (url, title, domain, image_base64)
    VALUES (%s, %s, %s, %s)
""", (url, title, domain, base64_data))
```

## Frontend Usage Examples

### Display in Modal:
```tsx
import Base64Image from '@/components/ui/Base64Image'
import { Dialog } from '@/components/ui/Dialog'

<Dialog>
    <DialogContent>
        <Base64Image 
            base64Data={selectedDomain.image_base64}
            alt={selectedDomain.title}
            className="w-full rounded-lg"
        />
    </DialogContent>
</Dialog>
```

### Display in Table:
```tsx
<td>
    <Base64Image 
        base64Data={domain.image_base64}
        alt="Thumbnail"
        width={100}
        height={75}
        className="rounded object-cover cursor-pointer"
        onClick={() => openModal(domain)}
    />
</td>
```

### Download Button:
```tsx
import { useDownloadBase64Image } from '@/components/ui/Base64Image'

function DownloadButton({ domain }) {
    const { downloadImage } = useDownloadBase64Image()
    
    return (
        <Button onClick={() => downloadImage(
            domain.image_base64, 
            `${domain.domain}_screenshot.png`
        )}>
            Download Screenshot
        </Button>
    )
}
```

## Performance Optimization

### Lazy Loading:
```tsx
<Base64Image 
    base64Data={domain.image_base64}
    loading="lazy"  // Browser native lazy loading
    className="w-full"
/>
```

### Thumbnail Generation:
```python
from PIL import Image
from utils.image_utils import base64_to_pil_image, pil_image_to_base64

# Create thumbnail
image = base64_to_pil_image(full_image_base64)
thumbnail = image.resize((200, 150), Image.Resampling.LANCZOS)
thumbnail_base64 = pil_image_to_base64(thumbnail, format='JPEG')

# Store both
cursor.execute("""
    UPDATE generated_domains 
    SET image_base64 = %s, thumbnail_base64 = %s
    WHERE id_domain = %s
""", (full_image_base64, thumbnail_base64, domain_id))
```

## Testing

### Backend Test:
```python
from utils.image_utils import image_file_to_base64, base64_to_image_file

# Test conversion
base64_data = image_file_to_base64('test.png')
assert base64_data.startswith('data:image/png;base64,')

# Test round-trip
base64_to_image_file(base64_data, 'test_output.png')
```

### Frontend Test:
```tsx
import { render } from '@testing-library/react'
import Base64Image from '@/components/ui/Base64Image'

test('renders base64 image', () => {
    const { getByAlt } = render(
        <Base64Image 
            base64Data="data:image/png;base64,iVBORw0KG..."
            alt="Test Image"
        />
    )
    expect(getByAlt('Test Image')).toBeInTheDocument()
})
```

## Rollback Plan

If needed to rollback:

```sql
-- Rename columns back
ALTER TABLE public.generated_domains 
RENAME COLUMN image_base64 TO image_path;

ALTER TABLE public.object_detection 
RENAME COLUMN image_detected_base64 TO image_detected_path;

ALTER TABLE public.object_detection 
ALTER COLUMN image_detected_path TYPE varchar(512);
```

## Support

For issues or questions, refer to:
- Backend utils: `/backend/utils/image_utils.py`
- Frontend component: `/frontend/src/components/ui/Base64Image.tsx`
- Migration script: `/database/migrations/001_image_path_to_base64.sql`
