"use client"

import { useEffect, useRef, useState } from "react"
import useSWR, { mutate as globalMutate } from "swr"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/Button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/Dialog"
import { Input } from "@/components/ui/Input"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import DataTable from "./DataTable"
import { LinkRecord, Status } from "@/types/linkRecord"
import { apiPost, apiGet, apiPut, apiDelete } from "@/lib/api"
import { useAuth } from "@/contexts/AuthContext"

const fetcher = async (url: string) => await apiGet(url)

function formatDate(d: string | Date) {
  const date = new Date(d)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(
    date.getDate()
  ).padStart(2, "0")}`
}

function toHexId(n: number) {
  const hex = Math.max(1, Number(n)).toString(16).toUpperCase().padStart(7, "0")
  return `#${hex}`
}

function getImageSrc(imageData: string | null | undefined): string | null {
  if (!imageData) {
    console.log('[getImageSrc] No image data provided')
    return null
  }

  console.log('[getImageSrc] Processing image data:', imageData.substring(0, 100) + '...')

  // Check if it's already a complete data URL
  if (imageData.startsWith('data:image/')) {
    console.log('[getImageSrc] Already a data URL')
    return imageData
  }

  // Check if it's a file path (contains /)
  if (imageData.includes('/')) {
    console.log('[getImageSrc] Detected as file path')

    // Extract just the filename from the full path
    // Handle both Unix and Windows paths
    const pathParts = imageData.split(/[/\\]/)
    const filename = pathParts[pathParts.length - 1]

    console.log('[getImageSrc] Extracted filename:', filename)

    // If filename is empty or looks invalid, return null
    if (!filename || filename.trim() === '') {
      console.error('[getImageSrc] Invalid filename extracted')
      return null
    }

    // Construct API URL - use relative path for proper proxying
    const fullUrl = `/api/images/detection/${filename}`
    console.log('[getImageSrc] Constructed URL:', fullUrl)
    return fullUrl
  }

  // Assume it's base64 data
  console.log('[getImageSrc] Treating as base64 data')

  // Remove any whitespace
  const cleanBase64 = imageData.replace(/\s/g, '')

  // Detect image format from base64 magic bytes
  let mimeType = 'image/png' // default

  if (cleanBase64.startsWith('/9j/') || cleanBase64.startsWith('iVBORw0KG')) {
    mimeType = cleanBase64.startsWith('/9j/') ? 'image/jpeg' : 'image/png'
    console.log('[getImageSrc] Detected format from prefix:', mimeType)
  } else {
    // Try to decode first few bytes to detect format
    try {
      const firstChars = cleanBase64.substring(0, 20)
      if (firstChars.includes('iVBOR')) {
        mimeType = 'image/png'
      } else if (firstChars.includes('R0lGOD')) {
        mimeType = 'image/gif'
      } else if (firstChars.includes('Qk0') || firstChars.includes('Qk1')) {
        mimeType = 'image/bmp'
      }
      console.log('[getImageSrc] Detected format from content:', mimeType)
    } catch (e) {
      console.warn('[getImageSrc] Could not detect format, using default PNG')
    }
  }

  const dataUrl = `data:${mimeType};base64,${cleanBase64}`
  console.log('[getImageSrc] Created data URL with length:', dataUrl.length)
  return dataUrl
}

export default function DetailModal({
  item,
  onClose,
  onMutate,
}: {
  item: LinkRecord | null
  onClose: () => void
  onMutate: () => void
}) {
  const [message, setMessage] = useState("")
  const [loading, setLoading] = useState(false)
  const chatScrollRef = useRef<HTMLDivElement | null>(null)

  type ChatMsg = { role: "user" | "assistant"; text: string; ts: number; link: string }
  const [chat, setChat] = useState<ChatMsg[]>([])

  const [contextMode, setContextMode] = useState(false)
  const [selectedContexts, setSelectedContexts] = useState<string[]>([])

  const { user } = useAuth()
  const [chatMode, setChatMode] = useState<"edukasi" | "hukum">("edukasi")

  useEffect(() => {
    setContextMode(false)
    setSelectedContexts([])
  }, [item])

  // Debug: Log image data when item changes
  useEffect(() => {
    if (item?.image) {
      console.log('[DetailModal] Item image value:', item.image)
      console.log('[DetailModal] Image type:', typeof item.image)
      console.log('[DetailModal] Image length:', item.image.length)
      console.log('[DetailModal] First 200 chars:', item.image.substring(0, 200))
    } else {
      console.log('[DetailModal] No image data in item')
    }
  }, [item])

  // Fetch chat history from database
  const { data: chatHistory, mutate: mutateChat } = useSWR<{ role: string; message: string; created_at: string }[]>(
    item && user ? `/api/chat/history/${item.id}?username=${user.username}` : null,
    fetcher,
    { refreshInterval: 0, revalidateOnFocus: false }
  )

  // Load chat history from API
  useEffect(() => {
    if (!item || !chatHistory || !user) return

    if (chatHistory.length === 0) {
      // No chat history, save initial greeting to database
      const greetingMessage = "Halo, saya siap membantu menganalisis kasus ini. Apa yang ingin Anda ketahui?"

      // Save greeting to database
      apiPost(`/api/chat/history/${item.id}`, {
        username: user.username,
        role: "assistant",
        message: greetingMessage
      }).then(() => {
        // After saving, set the chat state
        setChat([
          {
            role: "assistant",
            text: greetingMessage,
            ts: Date.now(),
            link: item.link,
          },
        ])
        // Refresh chat history
        mutateChat()
      }).catch((err) => {
        console.error("Failed to save greeting message:", err)
        // Still show greeting even if save fails
        setChat([
          {
            role: "assistant",
            text: greetingMessage,
            ts: Date.now(),
            link: item.link,
          },
        ])
      })
    } else {
      // Load chat history from database
      const loadedChat = chatHistory.map((msg) => ({
        role: msg.role as "user" | "assistant",
        text: msg.message,
        ts: new Date(msg.created_at).getTime(),
        link: item.link,
      }))
      setChat(loadedChat)
    }
  }, [chatHistory, item, user, mutateChat])

  const [flaggedLocal, setFlaggedLocal] = useState<boolean>(!!item?.flagged)
  useEffect(() => {
    if (item) setFlaggedLocal(item.flagged)
  }, [item])

  const { data: history, error: historyError, mutate: mutateHistory } = useSWR<{ events: { time: string; text: string }[] }>(
    item ? `/api/history?id=${item.id}` : null,
    fetcher,
    {
      refreshInterval: 0,
      revalidateOnFocus: false,
      onError: (err) => {
        console.error('[History] SWR Error:', err)
      }
    }
  )

  // Notes state and fetching
  type Note = { id: number; id_domain: number; note_text: string; created_by: string; created_at: string; updated_at: string }
  const { data: notes, mutate: mutateNotes } = useSWR<Note[]>(
    item ? `/api/notes/${item.id}` : null,
    fetcher,
    { refreshInterval: 0, revalidateOnFocus: true }
  )
  const [newNote, setNewNote] = useState("")
  const [editingNote, setEditingNote] = useState<Note | null>(null)
  const [editNoteText, setEditNoteText] = useState("")
  const [openMenuNoteId, setOpenMenuNoteId] = useState<number | null>(null)
  const [showNoteInput, setShowNoteInput] = useState(false)
  const [imageLoading, setImageLoading] = useState(true)
  const [zoomImage, setZoomImage] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [chat])

  // Handle ESC key to close zoom image
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && zoomImage) {
        e.preventDefault()
        e.stopPropagation()
        setZoomImage(false)
      }
    }

    if (zoomImage) {
      document.addEventListener('keydown', handleEscape, true) // Use capture phase
      // Prevent body scroll when zoom is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape, true)
      document.body.style.overflow = 'unset'
    }
  }, [zoomImage])

  function toggleContext(text: string) {
    // Auto-enable context mode if not already enabled
    if (!contextMode) {
      setContextMode(true)
    }

    setSelectedContexts((prev) =>
      prev.includes(text) ? prev.filter((x) => x !== text) : [...prev, text]
    )
  }


  async function send() {
    if (!item || !user) return
    const content = message.trim()
    if (!content) return

    let finalMsg = content
    if (contextMode && selectedContexts.length > 0) {
      finalMsg = `${content}`
    }

    setChat((c) => [...c, { role: "user", text: finalMsg, ts: Date.now(), link: item.link }])
    setMessage("")
    setLoading(true)
    setContextMode(false)

    try {
      // Save user message to database first
      await apiPost(`/api/chat/history/${item.id}`, {
        username: user.username,
        role: "user",
        message: finalMsg
      })

      // Call RunPod API via proxy endpoint
      let aiReply = ""
      try {
        // Get auth token
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null

        const response = await fetch("/api/runpod-chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {})
          },
          body: JSON.stringify({
            query: finalMsg,
            category: chatMode === "hukum" ? "hukum" : "edukasi",
            k: 5,
            max_new_tokens: 512,
            temperature: 0.1
          })
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
          throw new Error(errorData.error || `HTTP ${response.status}`)
        }

        const data = await response.json()
        aiReply = data.answer || data.response || data.reply || "Maaf, tidak ada balasan dari AI."
      } catch (fetchErr: any) {
        console.error("RunPod API fetch error:", fetchErr)

        // More detailed error message
        if (fetchErr.message.includes('502')) {
          throw new Error("API RunPod sedang tidak tersedia (502 Bad Gateway). Silakan coba lagi nanti.")
        } else if (fetchErr.message.includes('503')) {
          throw new Error("API RunPod sedang dalam maintenance (503 Service Unavailable). Silakan coba lagi nanti.")
        } else {
          throw new Error(fetchErr.message || "Tidak dapat terhubung ke API RunPod.")
        }
      }

      setChat((c) => [
        ...c,
        { role: "assistant", text: aiReply, ts: Date.now(), link: item.link },
      ])

      // Save AI response to database
      await apiPost(`/api/chat/history/${item.id}`, {
        username: user.username,
        role: "assistant",
        message: aiReply
      })

      // Refresh chat history from database
      mutateChat()
    } catch (err: any) {
      console.error("Chat error:", err)

      // Show specific error message
      const errorMessage = err.message || "Terjadi kesalahan saat menghubungi AI."
      setChat((c) => [
        ...c,
        { role: "assistant", text: errorMessage, ts: Date.now(), link: item.link },
      ])

      // Try to save error message to database
      try {
        await apiPost(`/api/chat/history/${item.id}`, {
          username: user.username,
          role: "assistant",
          message: errorMessage
        })
        mutateChat()
      } catch (saveErr) {
        console.error("Failed to save error message:", saveErr)
      }
    } finally {
      setLoading(false)
    }
  }

  async function deleteDomain() {
    if (!item) return

    const domainType = item.isManual ? "manual" : "generated"
    if (!confirm(`Apakah Anda yakin ingin menghapus domain ${domainType} ini?`)) return

    setLoading(true)
    try {
      if (item.isManual) {
        await apiDelete(`/api/manual-domain/${item.id}`)
      } else {
        // For generated domains, use the admin endpoint
        await apiDelete(`/api/admin/domains/${item.id}`)
      }

      // Refresh data first, then close modal
      await onMutate()

      // Also trigger global mutate to ensure all SWR caches are updated
      await globalMutate('/api/data/')

      onClose()
    } catch (err: any) {
      alert(`Gagal menghapus domain: ${err.message || "Unknown error"}`)
    } finally {
      setLoading(false)
    }
  }

  async function updateStatus(next: Status) {
    if (!item) return
    setLoading(true)
    try {
      const data = await apiPost("/api/update", {
        id: item.id,
        patch: { status: next },
      })

      console.log("[updateStatus] response:", data)

      // Close modal immediately for better UX
      onClose()

      // Update history and refresh data in background
      await mutateHistory()
      try {
        onMutate()
      } catch (err) {
        console.warn("onMutate failed or not provided:", err)
      }
    } catch (err: any) {
      console.error("Update status failed:", err)
      alert(`Gagal update status: ${err.message || "Unknown error"}`)
      setLoading(false)
    }
  }


  async function toggleFlag() {
    if (!item) return
    const nextVal = !flaggedLocal
    setFlaggedLocal(nextVal)

    try {
      const data = await apiPost("/api/update", {
        id: item.id,
        patch: { flagged: nextVal },
      })

      console.log("[toggleFlag] response:", data)

      await mutateHistory()
      try {
        onMutate()
      } catch (err) {
        console.warn("onMutate failed or not provided:", err)
      }
    } catch (err: any) {
      console.error("Toggle flag failed:", err)
      setFlaggedLocal(!nextVal)
      alert(`Gagal mengubah flag: ${err.message || "Unknown error"}`)
    }
  }

  // Notes functions
  async function handleAddNote() {
    if (!item || !newNote.trim()) return
    setLoading(true)

    try {
      await apiPost(`/api/notes/${item.id}`, { note_text: newNote })
      setNewNote("")
      mutateNotes()
    } catch (err: any) {
      alert(`Gagal menambahkan catatan: ${err.message || "Unknown error"}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleUpdateNote() {
    if (!editingNote || !editNoteText.trim()) return
    setLoading(true)

    try {
      await apiPut(`/api/notes/${editingNote.id}`, { note_text: editNoteText })
      setEditingNote(null)
      setEditNoteText("")
      mutateNotes()
    } catch (err: any) {
      alert(`Gagal mengupdate catatan: ${err.message || "Unknown error"}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleDeleteNote(noteId: number) {
    if (!confirm("Hapus catatan ini?")) return
    setLoading(true)

    try {
      await apiDelete(`/api/notes/${noteId}`)
      mutateNotes()
    } catch (err: any) {
      alert(`Gagal menghapus catatan: ${err.message || "Unknown error"}`)
    } finally {
      setLoading(false)
    }
  }

  async function clearChat() {
    if (!item || !user) return
    if (!confirm("Hapus semua riwayat percakapan untuk domain ini?")) return

    setLoading(true)
    try {
      await apiDelete(`/api/chat/history/${item.id}?username=${user.username}`)

      // Reset chat to greeting message
      const greetingMessage = "Halo, saya siap membantu menganalisis kasus ini. Apa yang ingin Anda ketahui?"
      setChat([
        {
          role: "assistant",
          text: greetingMessage,
          ts: Date.now(),
          link: item.link,
        },
      ])

      // Save greeting to database
      await apiPost(`/api/chat/history/${item.id}`, {
        username: user.username,
        role: "assistant",
        message: greetingMessage
      })

      // Refresh chat history
      mutateChat()
    } catch (err: any) {
      alert(`Gagal menghapus riwayat chat: ${err.message || "Unknown error"}`)
    } finally {
      setLoading(false)
    }
  }


  if (!item) return null

  return (
    <Dialog open={!!item} onOpenChange={(v) => {
      // Don't close the dialog if zoom is open
      if (!v && zoomImage) {
        setZoomImage(false)
        return
      }
      !v && onClose()
    }}>
      <DialogContent className="max-w-[min(95vw,1000px)] sm:max-w-[min(95vw,1000px)] max-h-screen" showCloseButton={false}>
        {/* Accessible DialogHeader - visually hidden */}
        <DialogHeader className="sr-only">
          <DialogTitle>{toHexId(item.id)} · Info Detail · {item.isManual ? 'Added' : 'Generated'} by {item.createdBy}{user?.username === item.createdBy ? ' (You)' : ''}</DialogTitle>
        </DialogHeader>

        {/* Visual Header + Link combined */}
        <div
          className="-mx-6 -mt-6 mb-1 border-b rounded-t-lg"
          style={{
            background: 'linear-gradient(135deg, #00336A 0%, #003D7D 50%, #003F81 100%)'
          }}
        >
          {/* Header */}
          <div className="px-6 py-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white" aria-hidden="true">
              {toHexId(item.id)} · {item.isManual ? 'Added' : 'Generated'} by {item.createdBy}{user?.username === item.createdBy ? ' (You)' : ''}
            </h2>
            <button
              onClick={onClose}
              className="text-white hover:text-white/80 transition-colors"
              aria-label="Close modal"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          {/* Link */}
          <div className="flex items-center gap-2 px-6 pb-4 rounded-b-xl">
            <Input
              readOnly
              value={item.link}
              className="text-xs bg-white cursor-default"
              title={item.link}
              onFocus={(e) => e.target.blur()}
            />
            <Button
              variant="outline"
              size="icon"
              className="bg-white hover:bg-gray-100"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(item.link);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                } catch (err) {
                  console.error("Copy failed:", err);
                  // Fallback method
                  const textArea = document.createElement("textarea");
                  textArea.value = item.link;
                  textArea.style.position = "fixed";
                  textArea.style.left = "-999999px";
                  document.body.appendChild(textArea);
                  textArea.focus();
                  textArea.select();
                  try {
                    document.execCommand('copy');
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  } catch (err2) {
                    console.error("Fallback copy failed:", err2);
                    alert("Gagal menyalin link. Silakan copy manual.");
                  }
                  document.body.removeChild(textArea);
                }
              }}
              aria-label="Copy link"
              title={copied ? "Copied!" : "Copy link"}
            >
              {copied ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2" stroke="currentColor" strokeWidth="2" />
                  <path d="M8 16h8a2 2 0 002-2v-8" stroke="currentColor" strokeWidth="2" />
                </svg>
              )}
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="bg-white hover:bg-gray-100"
              onClick={() => window.open(item.link, "_blank", "noopener,noreferrer")}
              aria-label="Open domain in new tab"
              title="Open domain"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </Button>
            <Button
              variant={flaggedLocal ? "default" : "outline"}
              size="sm"
              className="text-xs md:text-sm whitespace-nowrap bg-white hover:bg-gray-100 text-gray-900 dark:text-white"
              onClick={toggleFlag}
              style={flaggedLocal ? {
                background: 'linear-gradient(135deg, #1DC0EB 0%, #1199DA 50%, #0B88D3 100%)',
                color: 'white'
              } : undefined}
            >
              {flaggedLocal ? "Unflag" : "Flag"}
            </Button>
            {/* Show delete button for: 1) Administrators (all domains), 2) Manual domain creators, 3) Generated domain creators */}
            {
              (
                user?.role === "administrator" ||
                (item.isManual && user?.username === item.createdBy) ||
                (!item.isManual && user?.username === item.createdBy)
              ) && (
                <Button
                  variant="destructive"
                  size="sm"
                  className="text-xs md:text-sm whitespace-nowrap"
                  onClick={deleteDomain}
                  disabled={loading}
                >
                  Delete
                </Button>
              )
            }
          </div >
        </div >

        <div className="grid grid-cols-1 md:grid-cols-7 gap-6 h-[80vh]">
          {/* LEFT */}
          <div className="flex flex-col md:col-span-4 relative overflow-hidden">
            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto thin-scroll pr-2 pb-2" style={{ maxHeight: item.isManual ? '100%' : '90%' }}>
              <div className="flex flex-col gap-4 pr-1">
                {/* Reasoning - Hidden for manual domains */}
                {!item.isManual && (
                  <div className="rounded-md p-2">
                    <div className="flex items-center gap-2 mb-2">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" className="h-4 w-4 fill-current">
                        <path d="M64 304C64 358.4 83.3 408.6 115.9 448.9L67.1 538.3C65.1 542 64 546.2 64 550.5C64 564.6 75.4 576 89.5 576C93.5 576 97.3 575.4 101 573.9L217.4 524C248.8 536.9 283.5 544 320 544C461.4 544 576 436.5 576 304C576 171.5 461.4 64 320 64C178.6 64 64 171.5 64 304zM158 471.9C167.3 454.8 165.4 433.8 153.2 418.7C127.1 386.4 112 346.8 112 304C112 200.8 202.2 112 320 112C437.8 112 528 200.8 528 304C528 407.2 437.8 496 320 496C289.8 496 261.3 490.1 235.7 479.6C223.8 474.7 210.4 474.8 198.6 479.9L140 504.9L158 471.9zM208 336C225.7 336 240 321.7 240 304C240 286.3 225.7 272 208 272C190.3 272 176 286.3 176 304C176 321.7 190.3 336 208 336zM352 304C352 286.3 337.7 272 320 272C302.3 272 288 286.3 288 304C288 321.7 302.3 336 320 336C337.7 336 352 321.7 352 304zM432 336C449.7 336 464 321.7 464 304C464 286.3 449.7 272 432 272C414.3 272 400 286.3 400 304C400 321.7 414.3 336 432 336z" />
                      </svg>
                      <div className="text-xs font-semibold">Reasoning</div>
                    </div>
                    <div className="text-sm">{item.reasoning}</div>
                  </div>
                )}

                {/* Gambar - Hidden for manual domains */}
                {!item.isManual && (
                  <div className="rounded-md p-2">
                    <div className="flex items-center gap-2 mb-2">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" className="h-4 w-4 fill-current">
                        <path d="M72 128C72 114.7 82.7 104 96 104C109.3 104 120 114.7 120 128C120 141.3 109.3 152 96 152C82.7 152 72 141.3 72 128zM120 187.3C136 180.8 148.9 168 155.3 152L484.6 152C491.1 168 503.9 180.9 519.9 187.3L519.9 452.6C503.9 459.1 491 471.9 484.6 487.9L155.3 487.9C148.8 471.9 136 459 120 452.6L120 187.3zM544 64C517.1 64 494.1 80.5 484.7 104L155.3 104C145.9 80.5 122.9 64 96 64C60.7 64 32 92.7 32 128C32 154.9 48.5 177.9 72 187.3L72 452.6C48.5 462.1 32 485.1 32 511.9C32 547.2 60.7 575.9 96 575.9C122.9 575.9 145.9 559.4 155.3 535.9L484.6 535.9C494.1 559.4 517.1 575.9 543.9 575.9C579.2 575.9 607.9 547.2 607.9 511.9C607.9 485 591.4 462 567.9 452.6L567.9 187.3C591.4 177.8 607.9 154.8 607.9 128C607.9 92.7 579.2 64 543.9 64zM520 128C520 114.7 530.7 104 544 104C557.3 104 568 114.7 568 128C568 141.3 557.3 152 544 152C530.7 152 520 141.3 520 128zM96 488C109.3 488 120 498.7 120 512C120 525.3 109.3 536 96 536C82.7 536 72 525.3 72 512C72 498.7 82.7 488 96 488zM520 512C520 498.7 530.7 488 544 488C557.3 488 568 498.7 568 512C568 525.3 557.3 536 544 536C530.7 536 520 525.3 520 512zM224 240L312 240L312 296L224 296L224 240zM216 200C198.3 200 184 214.3 184 232L184 304C184 321.7 198.3 336 216 336L320 336C337.7 336 352 321.7 352 304L352 232C352 214.3 337.7 200 320 200L216 200zM288 384L288 408C288 425.7 302.3 440 320 440L424 440C441.7 440 456 425.7 456 408L456 336C456 318.3 441.7 304 424 304L400 304C400 318.6 396.1 332.2 389.3 344L416 344L416 400L328 400L328 383.6C325.4 383.9 322.7 384 320 384L288 384z" />
                      </svg>
                      <div className="text-xs font-semibold">Inference Visualization</div>
                    </div>
                    {item.image ? (
                      <div
                        className="relative rounded-md mx-auto w-full max-w-4xl border bg-muted cursor-pointer hover:opacity-90 transition-opacity"
                        style={{ aspectRatio: '1920/941' }}
                        onClick={() => setZoomImage(true)}
                        title="Klik untuk memperbesar gambar"
                      >
                        {imageLoading && (
                          <div className="absolute inset-0 flex items-center justify-center bg-muted text-muted-foreground text-sm">
                            <div className="flex flex-col items-center gap-2">
                              <svg className="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              <span>Loading image...</span>
                            </div>
                          </div>
                        )}
                        <img
                          src={getImageSrc(item.image) || ''}
                          alt="Hasil deteksi object detection"
                          className="rounded-md w-full h-auto object-contain"
                          onLoad={() => {
                            console.log('[Image] Successfully loaded')
                            setImageLoading(false)
                          }}
                          onError={(e) => {
                            console.error('[Image] Failed to load:', e)
                            console.error('[Image] Source was:', getImageSrc(item.image))
                            setImageLoading(false)
                          }}
                          style={{ display: imageLoading ? 'none' : 'block' }}
                        />
                      </div>
                    ) : (
                      <div className="rounded-md mx-auto w-full max-w-4xl border bg-muted text-muted-foreground" style={{ aspectRatio: '1920/941' }}>
                        <div className="flex items-center justify-center h-full">
                          <div className="text-center">
                            <svg className="mx-auto h-12 w-12 text-muted-foreground/50 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <p className="text-sm">Tidak ada gambar object detection</p>
                            <p className="text-xs text-muted-foreground/70 mt-1">1920 x 941</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Catatan */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" className="h-4 w-4 fill-current">
                      <path d="M336 496L160 496C151.2 496 144 488.8 144 480L144 160C144 151.2 151.2 144 160 144L480 144C488.8 144 496 151.2 496 160L496 336L408 336C368.2 336 336 368.2 336 408L336 496zM476.1 384L384 476.1L384 408C384 394.7 394.7 384 408 384L476.1 384zM96 480C96 515.3 124.7 544 160 544L357.5 544C374.5 544 390.8 537.3 402.8 525.3L525.3 402.7C537.3 390.7 544 374.4 544 357.4L544 160C544 124.7 515.3 96 480 96L160 96C124.7 96 96 124.7 96 160L96 480z" />
                    </svg>
                    <div className="text-xs font-semibold">Catatan</div>
                  </div>
                  <div className="border border-border rounded-md p-3 bg-card space-y-2">
                    {/* Existing notes */}
                    {notes && notes.length > 0 && (
                      <div className="space-y-2 max-h-40 overflow-auto mb-2">
                        {notes.map((note) => (
                          <div key={note.id} className="border-b pb-2 last:border-b-0">
                            {editingNote?.id === note.id ? (
                              <div className="space-y-2">
                                <textarea
                                  className="w-full p-2 border rounded text-xs"
                                  value={editNoteText}
                                  onChange={(e) => setEditNoteText(e.target.value)}
                                  rows={2}
                                />
                                <div className="flex gap-2">
                                  <Button size="sm" onClick={handleUpdateNote} disabled={loading}>
                                    Save
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      setEditingNote(null)
                                      setEditNoteText("")
                                    }}
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div>
                                <div className="text-xs mb-1">{note.note_text}</div>
                                <div className="flex items-center justify-between">
                                  <span className="text-[10px] text-foreground/50">
                                    {note.created_by} · {new Date(note.created_at).toLocaleString()}
                                  </span>
                                  {user?.username === note.created_by && (
                                    <div className="flex items-center gap-1">
                                      <button
                                        className="h-6 w-6 flex items-center justify-center hover:bg-muted rounded"
                                        onClick={() => setOpenMenuNoteId(openMenuNoteId === note.id ? null : note.id)}
                                        aria-label="Note options"
                                      >
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                          <circle cx="12" cy="5" r="2" />
                                          <circle cx="12" cy="12" r="2" />
                                          <circle cx="12" cy="19" r="2" />
                                        </svg>
                                      </button>
                                      {openMenuNoteId === note.id && (
                                        <>
                                          <button
                                            className="px-2 py-1 text-xs hover:bg-muted rounded border border-border"
                                            onClick={() => {
                                              setEditingNote(note)
                                              setEditNoteText(note.note_text)
                                              setOpenMenuNoteId(null)
                                            }}
                                          >
                                            Edit
                                          </button>
                                          <button
                                            className="px-2 py-1 text-xs hover:bg-muted rounded border border-border text-destructive"
                                            onClick={() => {
                                              handleDeleteNote(note.id)
                                              setOpenMenuNoteId(null)
                                            }}
                                          >
                                            Delete
                                          </button>
                                        </>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Add new note button and input */}
                    {!showNoteInput ? (
                      <div className="flex justify-end">
                        <Button
                          size="sm"
                          className="text-[11px] text-white"
                          style={{ background: 'linear-gradient(135deg, #00336A 0%, #003D7D 50%, #003F81 100%)' }}
                          onClick={() => setShowNoteInput(true)}
                        >
                          Tambah
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <textarea
                          className="w-full p-2 border rounded text-xs"
                          placeholder="Tambahkan catatan..."
                          value={newNote}
                          onChange={(e) => setNewNote(e.target.value)}
                          rows={2}
                        />
                        <div className="flex gap-2">
                          <Button size="sm" onClick={() => {
                            handleAddNote()
                            setShowNoteInput(false)
                          }} disabled={loading || !newNote.trim()}>
                            Simpan
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => {
                            setShowNoteInput(false)
                            setNewNote("")
                          }}>
                            Batal
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Riwayat */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" className="h-4 w-4 fill-current">
                      <path d="M320 128C426 128 512 214 512 320C512 426 426 512 320 512C254.8 512 197.1 479.5 162.4 429.7C152.3 415.2 132.3 411.7 117.8 421.8C103.3 431.9 99.8 451.9 109.9 466.4C156.1 532.6 233 576 320 576C461.4 576 576 461.4 576 320C576 178.6 461.4 64 320 64C234.3 64 158.5 106.1 112 170.7L112 144C112 126.3 97.7 112 80 112C62.3 112 48 126.3 48 144L48 256C48 273.7 62.3 288 80 288L104.6 288C105.1 288 105.6 288 106.1 288L192.1 288C209.8 288 224.1 273.7 224.1 256C224.1 238.3 209.8 224 192.1 224L153.8 224C186.9 166.6 249 128 320 128zM344 216C344 202.7 333.3 192 320 192C306.7 192 296 202.7 296 216L296 320C296 326.4 298.5 332.5 303 337L375 409C384.4 418.4 399.6 418.4 408.9 409C418.2 399.6 418.3 384.4 408.9 375.1L343.9 310.1L343.9 216z" />
                    </svg>
                    <div className="text-xs font-semibold">Riwayat Aktivitas</div>
                  </div>
                  <div className="border border-border rounded-md p-3 bg-card max-h-40 overflow-auto">
                    {historyError ? (
                      <div className="text-xs text-red-500">Error: {historyError.message}</div>
                    ) : !history ? (
                      <div className="text-xs text-foreground/60">Memuat riwayat...</div>
                    ) : history.events && history.events.length > 0 ? (
                      <ul className="space-y-1">
                        {history.events.map((ev, idx) => (
                          <li key={idx} className="text-xs">
                            <div className="flex flex-col">
                              <span className="text-foreground/50 text-[10px]">
                                {new Date(ev.time).toLocaleString('id-ID', {
                                  year: 'numeric',
                                  month: '2-digit',
                                  day: '2-digit',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                  second: '2-digit',
                                  hour12: false
                                })}
                              </span>
                              <span className="mt-0.5">{ev.text}</span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-xs text-foreground/60">Belum ada riwayat aktivitas</div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Fixed Verifikasi Section - Hidden for manual domains */}
            {!item.isManual && (
              <div className="absolute bottom-0 left-0 right-0 bg-background border-t border-border pt-3 pr-3 pl-0">
                <div className="text-xs font-semibold mb-2 pr-1">Verifikasi Status Laporan Mesin</div>
                {item.status === "unverified" ? (
                  <div className="grid grid-cols-2 gap-2 pr-1">
                    <Button
                      className="w-full text-xs text-white"
                      style={{ background: 'linear-gradient(135deg, #00336A 0%, #003D7D 50%, #003F81 100%)' }}
                      onClick={() => updateStatus("verified")}
                    >
                      Confirm
                    </Button>
                    <Button
                      className="w-full text-xs"
                      variant="destructive"
                      onClick={() => updateStatus("false-positive")}
                    >
                      False Positive
                    </Button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pr-1">
                    {item.status !== "false-positive" && (
                      <Button className="text-xs" variant="destructive" onClick={() => updateStatus("false-positive")}>
                        Ubah ke False Positive
                      </Button>
                    )}
                    {item.status !== "verified" && (
                      <Button className="text-xs" onClick={() => updateStatus("verified")}>
                        Ubah ke Verified
                      </Button>
                    )}
                    <Button className="text-xs" variant="outline" onClick={() => updateStatus("unverified")}>
                      Ubah ke Unverified
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* RIGHT - Chat AI Panel */}
          <div className="flex flex-col border border-border rounded-md overflow-hidden md:col-span-3 h-full">
            <div
              className="flex items-center justify-between p-2 border-b border-border"
              style={{ background: 'linear-gradient(135deg, #1DC0EB 0%, #1199DA 50%, #0B88D3 100%)' }}
            >
              <div className="flex items-center gap-2">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  className="shrink-0"
                >
                  {/* Diamond/Sparkle shape similar to Gemini logo */}
                  <path
                    d="M12 2L16 8L22 12L16 16L12 22L8 16L2 12L8 8L12 2Z"
                    fill="white"
                  />
                  <path
                    d="M12 6L14 10L18 12L14 14L12 18L10 14L6 12L10 10L12 6Z"
                    fill="white"
                    opacity="0.6"
                  />
                </svg>
                <div className="text-xs font-semibold text-white">Chat AI</div>
              </div>
              <div className="flex items-center gap-2">
                {/* Hide Ask with Context button for manual domains */}
                {!item.isManual && (
                  <Button
                    size="sm"
                    className="text-[11px] h-7 px-2 py-1"
                    variant={contextMode ? "default" : "outline"}
                    onClick={() => {
                      // toggle context mode, reset selections if turned off
                      if (contextMode) setSelectedContexts([])
                      setContextMode(!contextMode)
                    }}
                  >
                    {`Ask with Context${selectedContexts.length > 0 ? ` (${selectedContexts.length})` : ""}`}
                  </Button>
                )}
                {/* Clear Chat button */}
                <Button
                  size="sm"
                  className="text-[11px] h-7 px-2 py-1"
                  variant="outline"
                  onClick={clearChat}
                  disabled={loading || chat.length <= 1}
                  title="Hapus riwayat percakapan"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </Button>
              </div>
            </div>

            <div ref={chatScrollRef} className="flex-1 overflow-y-auto thin-scroll p-3 space-y-2">
              {chat.map((m, i) => (
                <div key={i} className={cn("text-sm flex", m.role === "user" ? "justify-end" : "justify-start")}>
                  <div
                    className={cn(
                      "rounded-lg px-3 py-2 max-w-[85%]",
                      m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                    )}
                  >
                    <div className="text-[10px] opacity-70 mb-1">{new Date(m.ts).toLocaleTimeString()}</div>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                  </div>
                </div>
              ))}
              {loading && <div className="text-xs text-foreground/60">...</div>}
            </div>

            <div className="border-t border-border p-2">
              {/* Show selected contexts */}
              {selectedContexts.length > 0 && (
                <div className="mb-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-md border border-blue-200 dark:border-blue-800">
                  <div className="text-[10px] text-blue-700 dark:text-blue-300 font-semibold mb-1">
                    Konteks yang dipilih ({selectedContexts.length}):
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {selectedContexts.map((ctx, idx) => (
                      <div
                        key={idx}
                        className="inline-flex items-center gap-1 bg-blue-100 dark:bg-blue-800/50 text-blue-800 dark:text-blue-200 text-[10px] px-2 py-1 rounded-full"
                      >
                        <span className="max-w-[200px] truncate">
                          {ctx === "Gambar Terkait" ? "Object Detection" : ctx.substring(0, 50) + (ctx.length > 50 ? "..." : "")}
                        </span>
                        <button
                          onClick={() => toggleContext(ctx)}
                          className="hover:bg-blue-200 dark:hover:bg-blue-700 rounded-full p-0.5"
                          title="Hapus konteks"
                        >
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex justify-between items-center px-1 mb-2">
                <span className="text-[10px] text-muted-foreground">Pilih Mode Chat:</span>
                <select
                  value={chatMode}
                  onChange={(e) => setChatMode(e.target.value as "edukasi" | "hukum")}
                  className="text-xs border rounded p-1 bg-white dark:bg-gray-800 h-6"
                >
                  <option value="edukasi">Mode Edukasi</option>
                  <option value="hukum">Mode Hukum</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Tanya tentang kasus ini..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && send()}
                />
                <Button
                  onClick={() => send()}
                  disabled={loading}
                  className="text-white"
                  style={{ background: 'linear-gradient(135deg, #00336A 0%, #003D7D 50%, #003F81 100%)' }}
                >
                  Kirim
                </Button>
              </div>
            </div>
          </div>
        </div>
      </DialogContent >

      {/* Image Zoom Modal */}
      {zoomImage && item.image && (
        <div
          className="fixed inset-0 z-[9999] bg-black/90 flex items-center justify-center p-4"
          onClick={(e) => {
            e.stopPropagation()
            setZoomImage(false)
          }}
        >
          <button
            onClick={(e) => {
              e.stopPropagation()
              setZoomImage(false)
            }}
            className="absolute top-4 right-4 text-white hover:text-white/80 transition-colors z-10"
            aria-label="Close zoom"
          >
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
          <img
            src={getImageSrc(item.image) || ''}
            alt="Hasil deteksi object detection - Zoom"
            className="max-w-full max-h-full object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </Dialog >
  )
}

DetailModal.Table = DataTable
