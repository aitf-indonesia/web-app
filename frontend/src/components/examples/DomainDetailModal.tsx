"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import Base64Image, { useDownloadBase64Image } from "@/components/ui/Base64Image"
import { Download, ExternalLink, X } from "lucide-react"

interface DomainDetailModalProps {
    isOpen: boolean
    onClose: () => void
    domain: {
        id_domain: number
        url: string
        title: string
        domain: string
        image_base64: string
        date_generated: string
    } | null
}

/**
 * Example modal component that displays domain details with base64 screenshot
 */
export default function DomainDetailModal({ isOpen, onClose, domain }: DomainDetailModalProps) {
    const { downloadImage } = useDownloadBase64Image()

    if (!domain) return null

    const handleDownload = () => {
        if (domain.image_base64) {
            downloadImage(domain.image_base64, `${domain.domain}_screenshot.png`)
        }
    }

    const handleOpenUrl = () => {
        window.open(domain.url, '_blank', 'noopener,noreferrer')
    }

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <DialogTitle className="text-xl font-bold mb-2">
                                {domain.title || domain.domain}
                            </DialogTitle>
                            <div className="text-sm text-gray-600 space-y-1">
                                <p className="flex items-center gap-2">
                                    <span className="font-semibold">Domain:</span>
                                    <span className="text-blue-600">{domain.domain}</span>
                                </p>
                                <p className="flex items-center gap-2">
                                    <span className="font-semibold">URL:</span>
                                    <a
                                        href={domain.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline truncate max-w-md"
                                    >
                                        {domain.url}
                                    </a>
                                </p>
                                <p className="flex items-center gap-2">
                                    <span className="font-semibold">Generated:</span>
                                    <span>{new Date(domain.date_generated).toLocaleString('id-ID')}</span>
                                </p>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={onClose}
                            className="ml-4"
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>
                </DialogHeader>

                {/* Screenshot Section */}
                <div className="mt-4">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold text-lg">Screenshot</h3>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleOpenUrl}
                                className="flex items-center gap-2"
                            >
                                <ExternalLink className="h-4 w-4" />
                                Open URL
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleDownload}
                                disabled={!domain.image_base64}
                                className="flex items-center gap-2"
                            >
                                <Download className="h-4 w-4" />
                                Download
                            </Button>
                        </div>
                    </div>

                    {/* Base64 Image Display */}
                    {domain.image_base64 ? (
                        <div className="border rounded-lg overflow-hidden bg-gray-50">
                            <Base64Image
                                base64Data={domain.image_base64}
                                alt={`Screenshot of ${domain.domain}`}
                                className="w-full h-auto"
                                fallbackSrc="/placeholder-screenshot.png"
                            />
                        </div>
                    ) : (
                        <div className="border rounded-lg p-12 text-center bg-gray-50">
                            <p className="text-gray-500">No screenshot available</p>
                        </div>
                    )}
                </div>

                {/* Additional Info Section (Optional) */}
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                        <strong>💡 Tip:</strong> Click "Download" to save the screenshot,
                        or "Open URL" to visit the website directly.
                    </p>
                </div>
            </DialogContent>
        </Dialog>
    )
}

/**
 * Example usage in parent component:
 * 
 * const [selectedDomain, setSelectedDomain] = useState(null)
 * const [isModalOpen, setIsModalOpen] = useState(false)
 * 
 * const handleViewDetails = (domain) => {
 *     setSelectedDomain(domain)
 *     setIsModalOpen(true)
 * }
 * 
 * return (
 *     <>
 *         <Button onClick={() => handleViewDetails(domain)}>
 *             View Details
 *         </Button>
 *         
 *         <DomainDetailModal
 *             isOpen={isModalOpen}
 *             onClose={() => setIsModalOpen(false)}
 *             domain={selectedDomain}
 *         />
 *     </>
 * )
 */
