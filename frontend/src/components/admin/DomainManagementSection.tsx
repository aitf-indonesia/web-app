"use client"

import { useState } from "react"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { Input } from "@/components/ui/Input"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/Dialog"
import { apiDelete } from "@/lib/api"

export default function DomainManagementSection() {
    const [showDeleteAllModal, setShowDeleteAllModal] = useState(false)
    const [showDeleteByIdModal, setShowDeleteByIdModal] = useState(false)
    const [confirmText, setConfirmText] = useState("")
    const [domainId, setDomainId] = useState("")
    const [loading, setLoading] = useState(false)

    const handleDeleteAll = async () => {
        if (confirmText !== "konfirmasi") {
            alert("Please type 'konfirmasi' to confirm deletion")
            return
        }

        setLoading(true)
        try {
            const response = await apiDelete(`/api/admin/domains/all?confirmation=${confirmText}`)
            alert(`Successfully deleted ${response.deleted_count} domains`)
            setShowDeleteAllModal(false)
            setConfirmText("")
        } catch (err: any) {
            alert(`Failed to delete all domains: ${err.message}`)
        } finally {
            setLoading(false)
        }
    }

    const handleDeleteById = async () => {
        if (!domainId) {
            alert("Please enter a domain ID")
            return
        }

        if (!confirm(`Are you sure you want to delete domain with ID ${domainId}?`)) {
            return
        }

        setLoading(true)
        try {
            await apiDelete(`/api/admin/domains/${domainId}`)
            alert(`Successfully deleted domain with ID ${domainId}`)
            setShowDeleteByIdModal(false)
            setDomainId("")
        } catch (err: any) {
            alert(`Failed to delete domain: ${err.message}`)
        } finally {
            setLoading(false)
        }
    }

    return (
        <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Domain Management</h2>

            <div className="space-y-4">
                <div>
                    <h3 className="text-sm font-medium mb-2">Delete Specific Domain</h3>
                    <div className="flex gap-2">
                        <Input
                            type="number"
                            placeholder="Enter domain ID"
                            value={domainId}
                            onChange={(e) => setDomainId(e.target.value)}
                            className="max-w-xs"
                        />
                        <Button
                            variant="destructive"
                            onClick={() => setShowDeleteByIdModal(true)}
                            disabled={!domainId}
                        >
                            Delete Domain
                        </Button>
                    </div>
                </div>

                <div className="border-t pt-4">
                    <h3 className="text-sm font-medium mb-2 text-destructive">Danger Zone</h3>
                    <Button
                        variant="destructive"
                        onClick={() => setShowDeleteAllModal(true)}
                    >
                        Delete All Domains
                    </Button>
                </div>
            </div>

            {/* Delete All Confirmation Modal */}
            <Dialog open={showDeleteAllModal} onOpenChange={(open) => !open && setShowDeleteAllModal(false)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="text-destructive">Delete All Domains</DialogTitle>
                    </DialogHeader>

                    <div className="space-y-4">
                        <p className="text-sm text-muted-foreground">
                            This action will permanently delete ALL domains from the database. This cannot be undone.
                        </p>

                        <div>
                            <label className="text-sm font-medium">
                                Type <code className="bg-muted px-1 py-0.5 rounded">konfirmasi</code> to confirm:
                            </label>
                            <Input
                                value={confirmText}
                                onChange={(e) => setConfirmText(e.target.value)}
                                placeholder="konfirmasi"
                                className="mt-2"
                            />
                        </div>

                        <div className="flex gap-2 justify-end">
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setShowDeleteAllModal(false)
                                    setConfirmText("")
                                }}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="destructive"
                                onClick={handleDeleteAll}
                                disabled={loading || confirmText !== "konfirmasi"}
                            >
                                {loading ? "Deleting..." : "Delete All Domains"}
                            </Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>

            {/* Delete By ID Modal */}
            {showDeleteByIdModal && (
                <Dialog open={showDeleteByIdModal} onOpenChange={(open) => !open && setShowDeleteByIdModal(false)}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Confirm Deletion</DialogTitle>
                        </DialogHeader>

                        <div className="space-y-4">
                            <p className="text-sm text-muted-foreground">
                                Are you sure you want to delete domain with ID {domainId}?
                            </p>

                            <div className="flex gap-2 justify-end">
                                <Button
                                    variant="outline"
                                    onClick={() => {
                                        setShowDeleteByIdModal(false)
                                        setDomainId("")
                                    }}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    variant="destructive"
                                    onClick={handleDeleteById}
                                    disabled={loading}
                                >
                                    {loading ? "Deleting..." : "Delete Domain"}
                                </Button>
                            </div>
                        </div>
                    </DialogContent>
                </Dialog>
            )}
        </Card>
    )
}
