"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"

export default function ProtectedAdminRoute({ children }: { children: React.ReactNode }) {
    const router = useRouter()
    const { user, isAuthenticated, isLoading } = useAuth()

    useEffect(() => {
        if (!isLoading) {
            if (!isAuthenticated) {
                router.replace("/login")
            } else if (user?.role !== "administrator") {
                router.replace("/dashboard")
            }
        }
    }, [isAuthenticated, isLoading, user, router])

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <p className="text-gray-500">Memeriksa sesi pengguna...</p>
            </div>
        )
    }

    if (!isAuthenticated || user?.role !== "administrator") {
        return null
    }

    return <>{children}</>
}
