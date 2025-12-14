"use client"

import { useState } from "react"
import Image from "next/image"

interface Base64ImageProps {
    base64Data: string
    alt?: string
    className?: string
    width?: number
    height?: number
    fallbackSrc?: string
    onClick?: () => void
}

/**
 * Component to display base64 encoded images
 * Handles both data URI format and raw base64 strings
 */
export default function Base64Image({
    base64Data,
    alt = "Image",
    className = "",
    width,
    height,
    fallbackSrc = "/placeholder-image.png",
    onClick
}: Base64ImageProps) {
    const [error, setError] = useState(false)
    const [loading, setLoading] = useState(true)

    // Ensure base64Data has proper data URI format
    const getImageSrc = (): string => {
        if (!base64Data) {
            return fallbackSrc
        }

        // If already has data URI prefix, return as is
        if (base64Data.startsWith('data:image')) {
            return base64Data
        }

        // If raw base64, add data URI prefix (assume PNG)
        return `data:image/png;base64,${base64Data}`
    }

    const handleLoad = () => {
        setLoading(false)
        setError(false)
    }

    const handleError = () => {
        setLoading(false)
        setError(true)
    }

    const imageSrc = error ? fallbackSrc : getImageSrc()

    // If using Next.js Image component with specific dimensions
    if (width && height) {
        return (
            <div className={`relative ${className}`} onClick={onClick}>
                {loading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                    </div>
                )}
                <Image
                    src={imageSrc}
                    alt={alt}
                    width={width}
                    height={height}
                    onLoad={handleLoad}
                    onError={handleError}
                    className={className}
                />
            </div>
        )
    }

    // Standard img tag for flexible sizing
    return (
        <div className={`relative ${loading ? 'min-h-[100px]' : ''}`} onClick={onClick}>
            {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                </div>
            )}
            <img
                src={imageSrc}
                alt={alt}
                onLoad={handleLoad}
                onError={handleError}
                className={className}
                style={{ display: loading ? 'none' : 'block' }}
            />
        </div>
    )
}

/**
 * Hook to download base64 image as file
 */
export function useDownloadBase64Image() {
    const downloadImage = (base64Data: string, filename: string = 'image.png') => {
        try {
            // Ensure proper data URI format
            let dataUri = base64Data
            if (!base64Data.startsWith('data:image')) {
                dataUri = `data:image/png;base64,${base64Data}`
            }

            // Create download link
            const link = document.createElement('a')
            link.href = dataUri
            link.download = filename
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        } catch (error) {
            console.error('Error downloading image:', error)
        }
    }

    return { downloadImage }
}

/**
 * Utility function to get image dimensions from base64
 */
export function getBase64ImageDimensions(base64Data: string): Promise<{ width: number; height: number }> {
    return new Promise((resolve, reject) => {
        const img = new window.Image()

        img.onload = () => {
            resolve({
                width: img.width,
                height: img.height
            })
        }

        img.onerror = () => {
            reject(new Error('Failed to load image'))
        }

        // Ensure proper data URI format
        if (base64Data.startsWith('data:image')) {
            img.src = base64Data
        } else {
            img.src = `data:image/png;base64,${base64Data}`
        }
    })
}
