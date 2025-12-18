import { NextResponse } from 'next/server'

export async function GET() {
    try {
        // Call RunPod health check API
        const response = await fetch('https://l7i1ghaqgdha36-3000.proxy.runpod.net/health/services', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })

        if (!response.ok) {
            const errorText = await response.text()
            return NextResponse.json(
                { error: `RunPod health check error: ${response.status} - ${errorText}` },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)
    } catch (error: any) {
        console.error('Health check proxy error:', error)
        return NextResponse.json(
            { error: error.message || 'Internal server error' },
            { status: 500 }
        )
    }
}
