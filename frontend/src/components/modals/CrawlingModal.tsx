"use client"

import { useState, useEffect, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/Dialog"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"

const API_BASE = process.env.NEXT_PUBLIC_API_URL

type Tab = "detail" | "generating" | "result"

interface CrawlerSummary {
    status: string
    timestamp: string
    time_elapsed: string
    fetch_domain: { success: number; total: number }
    fetch_og_metadata: { success: number; total: number }
    screenshot: { success: number; failed: number; skipped: number; total: number }
    domains_inserted: number
    keywords: string[]
}

export default function CrawlingModal({
    open,
    onClose,
    onComplete,
}: {
    open: boolean
    onClose: () => void
    onComplete?: () => void
}) {
    const [activeTab, setActiveTab] = useState<Tab>("detail")
    const [domainCount, setDomainCount] = useState(15)
    const [keywords, setKeywords] = useState("judi online, slot gacor, casino online, poker online, togel online, situs judi, agen bola, bandar togel, slot deposit, judi bola")
    const [isEditingKeywords, setIsEditingKeywords] = useState(false)
    const [tempKeywords, setTempKeywords] = useState(keywords)

    // Generating tab state
    const [logs, setLogs] = useState<string[]>([])
    const [timeElapsed, setTimeElapsed] = useState(0)
    const [jobId, setJobId] = useState<string | null>(null)
    const [isMinimized, setIsMinimized] = useState(false)

    // Result tab state
    const [summary, setSummary] = useState<CrawlerSummary | null>(null)

    const logsEndRef = useRef<HTMLDivElement>(null)
    const eventSourceRef = useRef<EventSource | null>(null)
    const timerRef = useRef<NodeJS.Timeout | null>(null)

    // Auto-scroll logs to bottom
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [logs])

    // Timer for elapsed time
    useEffect(() => {
        if (activeTab === "generating" && !timerRef.current) {
            timerRef.current = setInterval(() => {
                setTimeElapsed((t) => t + 1)
            }, 1000)
        }

        return () => {
            if (timerRef.current) {
                clearInterval(timerRef.current)
                timerRef.current = null
            }
        }
    }, [activeTab])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close()
            }
            if (timerRef.current) {
                clearInterval(timerRef.current)
            }
        }
    }, [])

    // Request notification permission
    useEffect(() => {
        if (open && "Notification" in window && Notification.permission === "default") {
            Notification.requestPermission()
        }
    }, [open])

    const keywordList = keywords.split(/[,\n]/).map(k => k.trim()).filter(k => k)

    function handleEditKeywords() {
        setIsEditingKeywords(true)
        setTempKeywords(keywords)
    }

    function handleSaveKeywords() {
        setKeywords(tempKeywords)
        setIsEditingKeywords(false)
    }

    async function handleGenerate() {
        try {
            setLogs([])
            setTimeElapsed(0)
            setSummary(null)
            setActiveTab("generating")

            // Start crawler
            const res = await fetch(`${API_BASE}/api/crawler/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    domain_count: domainCount,
                    keywords: keywordList,
                }),
            })

            if (!res.ok) {
                const error = await res.json()
                throw new Error(error.detail || "Failed to start crawler")
            }

            const data = await res.json()
            setJobId(data.job_id)

            // Start streaming logs
            const eventSource = new EventSource(`${API_BASE}/api/crawler/logs/${data.job_id}`)
            eventSourceRef.current = eventSource

            eventSource.onmessage = (event) => {
                const line = event.data

                if (line === "[DONE]") {
                    eventSource.close()
                    eventSourceRef.current = null

                    // Show notification
                    if ("Notification" in window && Notification.permission === "granted") {
                        const notification = new Notification("Crawling Complete", {
                            body: `Successfully crawled ${domainCount} domains`,
                            icon: "/favicon.ico"
                        })

                        notification.onclick = () => {
                            window.focus()
                            setIsMinimized(false)
                        }
                    }

                    // Refresh dashboard data
                    if (onComplete) {
                        onComplete()
                    }

                    return
                }

                // Parse summary if present
                if (line.startsWith("[SUMMARY]")) {
                    const summaryJson = line.replace("[SUMMARY]", "").trim()
                    try {
                        const parsedSummary = JSON.parse(summaryJson)
                        setSummary(parsedSummary)
                        setActiveTab("result")
                    } catch (e) {
                        console.error("Failed to parse summary:", e)
                    }
                }

                // Add log line
                setLogs((prev) => [...prev, line])
            }

            eventSource.onerror = (error) => {
                console.error("EventSource error:", error)
                eventSource.close()
                eventSourceRef.current = null
                setLogs((prev) => [...prev, "[ERROR] Connection lost"])
            }
        } catch (err) {
            setLogs((prev) => [...prev, `[ERROR] ${err instanceof Error ? err.message : "Unknown error"}`])
        }
    }

    async function handleCancel() {
        if (!jobId) return

        try {
            await fetch(`${API_BASE}/api/crawler/cancel/${jobId}`, {
                method: "POST",
            })

            if (eventSourceRef.current) {
                eventSourceRef.current.close()
                eventSourceRef.current = null
            }

            setLogs((prev) => [...prev, "[CANCELLED] Crawling process cancelled by user"])

            // Reset to detail tab
            setTimeout(() => {
                handleClose()
            }, 1000)
        } catch (err) {
            console.error("Failed to cancel:", err)
        }
    }

    function handleMinimize() {
        setIsMinimized(true)
        onClose()
    }

    function handleClose() {
        // Only allow close if not generating
        if (activeTab !== "generating") {
            setActiveTab("detail")
            setLogs([])
            setTimeElapsed(0)
            setSummary(null)
            setJobId(null)
            setIsMinimized(false)
            onClose()
        }
    }

    function handleDone() {
        handleClose()
    }

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
    }

    return (
        <Dialog open={open && !isMinimized} onOpenChange={(v) => !v && activeTab !== "generating" && handleClose()}>
            <DialogContent className="max-w-2xl max-h-[80vh]">
                <DialogHeader>
                    <DialogTitle>Crawler</DialogTitle>
                </DialogHeader>

                {/* Tabs */}
                <div className="flex border-b border-border">
                    <button
                        className={`px-4 py-2 text-sm font-medium ${activeTab === "detail"
                                ? "border-b-2 border-primary text-primary"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                        onClick={() => activeTab !== "generating" && setActiveTab("detail")}
                        disabled={activeTab === "generating"}
                    >
                        Crawling Detail
                    </button>
                    <button
                        className={`px-4 py-2 text-sm font-medium ${activeTab === "generating"
                                ? "border-b-2 border-primary text-primary"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                        disabled
                    >
                        Generating
                    </button>
                    <button
                        className={`px-4 py-2 text-sm font-medium ${activeTab === "result"
                                ? "border-b-2 border-primary text-primary"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                        disabled
                    >
                        Result
                    </button>
                </div>

                {/* Tab Content */}
                <div className="flex-1 overflow-y-auto py-4">
                    {/* Tab 1: Crawling Detail */}
                    {activeTab === "detail" && (
                        <div className="space-y-4">
                            {/* Domain Count */}
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Jumlah Domain Generate</label>
                                <div className="flex items-center gap-2">
                                    <Button
                                        variant="outline"
                                        size="icon"
                                        onClick={() => setDomainCount((c) => Math.max(1, c - 1))}
                                    >
                                        -
                                    </Button>
                                    <Input
                                        type="number"
                                        value={domainCount}
                                        onChange={(e) => setDomainCount(Math.max(1, parseInt(e.target.value) || 1))}
                                        className="w-24 text-center"
                                    />
                                    <Button
                                        variant="outline"
                                        size="icon"
                                        onClick={() => setDomainCount((c) => c + 1)}
                                    >
                                        +
                                    </Button>
                                </div>
                            </div>

                            {/* Keywords */}
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <label className="text-sm font-medium">Keyword</label>
                                    <div className="flex gap-2">
                                        {isEditingKeywords ? (
                                            <Button size="sm" onClick={handleSaveKeywords}>
                                                Save
                                            </Button>
                                        ) : (
                                            <Button size="sm" variant="outline" onClick={handleEditKeywords}>
                                                Edit
                                            </Button>
                                        )}
                                    </div>
                                </div>

                                {isEditingKeywords ? (
                                    <textarea
                                        value={tempKeywords}
                                        onChange={(e) => setTempKeywords(e.target.value)}
                                        className="w-full min-h-[120px] p-3 text-sm border border-border rounded-md bg-background"
                                        placeholder="Masukkan keyword-keyword untuk mencari domain, pisahkan dengan koma atau baris baru"
                                    />
                                ) : (
                                    <div className="p-3 border border-border rounded-md bg-muted/30 min-h-[120px] text-sm">
                                        {keywords}
                                    </div>
                                )}

                                <div className="text-xs text-muted-foreground">
                                    {keywordList.length} keywords
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex justify-end gap-2 pt-4">
                                <Button variant="outline" onClick={handleClose}>
                                    Cancel
                                </Button>
                                <Button onClick={handleGenerate}>Generate</Button>
                            </div>
                        </div>
                    )}

                    {/* Tab 2: Generating */}
                    {activeTab === "generating" && (
                        <div className="space-y-4">
                            {/* Logs */}
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Log</label>
                                <div className="bg-black text-green-400 p-4 rounded-md h-[400px] overflow-y-auto font-mono text-xs">
                                    {logs.map((log, i) => (
                                        <div key={i}>{log}</div>
                                    ))}
                                    <div ref={logsEndRef} />
                                </div>
                            </div>

                            {/* Time Elapsed */}
                            <div className="text-sm text-muted-foreground">
                                Time elapsed: {formatTime(timeElapsed)}
                            </div>

                            {/* Actions */}
                            <div className="flex justify-end gap-2">
                                <Button variant="outline" onClick={handleMinimize}>
                                    Minimize
                                </Button>
                                <Button variant="destructive" onClick={handleCancel}>
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Tab 3: Result */}
                    {activeTab === "result" && summary && (
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Summary</label>
                                <div className="p-4 border border-border rounded-md space-y-2 text-sm">
                                    <div>
                                        <strong>Status:</strong> {summary.status === "success" ? "Success" : "Partial Success"}
                                    </div>
                                    <div>
                                        <strong>Time:</strong> {new Date(summary.timestamp).toLocaleString()}
                                    </div>
                                    <div>
                                        <strong>Time Elapsed:</strong> {summary.time_elapsed}
                                    </div>
                                    <div>
                                        <strong>Fetch Domain:</strong> {summary.fetch_domain.success}/{summary.fetch_domain.total} Success
                                    </div>
                                    <div>
                                        <strong>Fetch OG Metadata:</strong> {summary.fetch_og_metadata.success}/{summary.fetch_og_metadata.total} Success
                                    </div>
                                    <div>
                                        <strong>Screenshot:</strong> {summary.screenshot.success}/{summary.screenshot.total} Success
                                    </div>
                                </div>
                            </div>

                            <div className="text-sm text-muted-foreground">
                                {summary.domains_inserted} domain inserted
                            </div>

                            <div className="flex justify-end">
                                <Button onClick={handleDone}>Done</Button>
                            </div>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}
