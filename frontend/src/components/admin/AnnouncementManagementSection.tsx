"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { useAuth } from "@/contexts/AuthContext"
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api"

interface Announcement {
    id: number
    title: string
    content: string
    category: string
    created_by: string
    created_at: string
    updated_at: string
}

export default function AnnouncementManagementSection() {
    const { user } = useAuth()
    const [announcements, setAnnouncements] = useState<Announcement[]>([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [editingId, setEditingId] = useState<number | null>(null)

    // Form states
    const [formData, setFormData] = useState({
        title: "",
        content: "",
        category: "info"
    })

    // Fetch announcements
    const fetchAnnouncements = async () => {
        try {
            setLoading(true)
            const data = await apiGet("/api/announcements?page=1&limit=100")
            setAnnouncements(data)
        } catch (error) {
            console.error("Failed to fetch announcements:", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchAnnouncements()
    }, [])

    // Handle create/update
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        try {
            if (editingId) {
                await apiPut(`/api/announcements/${editingId}`, formData)
            } else {
                await apiPost("/api/announcements", formData)
            }

            await fetchAnnouncements()
            setShowForm(false)
            setEditingId(null)
            setFormData({ title: "", content: "", category: "info" })
        } catch (error: any) {
            console.error("Error saving announcement:", error)
            alert(error.message || "Failed to save announcement")
        }
    }

    // Handle delete
    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure you want to delete this announcement?")) {
            return
        }

        try {
            await apiDelete(`/api/announcements/${id}`)
            await fetchAnnouncements()
        } catch (error: any) {
            console.error("Error deleting announcement:", error)
            alert(error.message || "Failed to delete announcement")
        }
    }

    // Handle edit
    const handleEdit = (announcement: Announcement) => {
        setEditingId(announcement.id)
        setFormData({
            title: announcement.title,
            content: announcement.content,
            category: announcement.category,
        })
        setShowForm(true)
    }

    // Cancel form
    const handleCancel = () => {
        setShowForm(false)
        setEditingId(null)
        setFormData({ title: "", content: "", category: "info" })
    }

    const categoryColors: Record<string, string> = {
        info: "border-blue-500",
        warning: "border-orange-500",
        urgent: "border-red-500",
        success: "border-green-500",
    }

    return (
        <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-semibold">Announcement Management</h2>
                    <p className="text-sm text-muted-foreground">
                        Manage announcements displayed on the dashboard
                    </p>
                </div>
                {!showForm && (
                    <Button onClick={() => setShowForm(true)}>
                        + New Announcement
                    </Button>
                )}
            </div>

            {/* Form */}
            {showForm && (
                <Card className="p-4 mb-6 bg-muted/30">
                    <h3 className="text-lg font-semibold mb-4">
                        {editingId ? "Edit Announcement" : "New Announcement"}
                    </h3>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Title *
                            </label>
                            <input
                                type="text"
                                value={formData.title}
                                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                className="w-full px-3 py-2 border rounded-md"
                                required
                                maxLength={255}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Content *
                            </label>
                            <textarea
                                value={formData.content}
                                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                                className="w-full px-3 py-2 border rounded-md"
                                rows={4}
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Category
                            </label>
                            <select
                                value={formData.category}
                                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                                className="w-full px-3 py-2 border rounded-md"
                            >
                                <option value="info">Info (Blue)</option>
                                <option value="warning">Warning (Orange)</option>
                                <option value="urgent">Urgent (Red)</option>
                                <option value="success">Success (Green)</option>
                            </select>
                        </div>

                        <div className="flex gap-2">
                            <Button type="submit">
                                {editingId ? "Update" : "Create"}
                            </Button>
                            <Button type="button" variant="outline" onClick={handleCancel}>
                                Cancel
                            </Button>
                        </div>
                    </form>
                </Card>
            )}

            {/* List */}
            <div className="space-y-3">
                {loading ? (
                    <p className="text-center py-8 text-muted-foreground">Loading...</p>
                ) : announcements.length === 0 ? (
                    <p className="text-center py-8 text-muted-foreground">
                        No announcements yet. Create one to get started.
                    </p>
                ) : (
                    announcements.map((announcement) => (
                        <Card key={announcement.id} className="p-4">
                            <div className="flex items-start justify-between">
                                <div className={`flex-1 border-l-4 ${categoryColors[announcement.category] || "border-blue-500"} pl-3`}>
                                    <h3 className="font-semibold mb-1">{announcement.title}</h3>
                                    <p className="text-sm text-muted-foreground mb-2">
                                        {announcement.content}
                                    </p>
                                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                        <span>Category: {announcement.category}</span>
                                        <span>By: {announcement.created_by}</span>
                                        <span>
                                            {new Date(announcement.created_at).toLocaleDateString('id-ID', {
                                                day: 'numeric',
                                                month: 'short',
                                                year: 'numeric'
                                            })}
                                        </span>
                                    </div>
                                </div>
                                <div className="flex gap-2 ml-4">
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleEdit(announcement)}
                                    >
                                        Edit
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="destructive"
                                        onClick={() => handleDelete(announcement.id)}
                                    >
                                        Delete
                                    </Button>
                                </div>
                            </div>
                        </Card>
                    ))
                )}
            </div>
        </Card>
    )
}
