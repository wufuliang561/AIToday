export interface Hotspot {
    id: number
    title: string
    summary: string
    score: number
    itemsCount: number
    time: string
}

export interface NewsItem {
    id: number
    title: string
    source: "YouTube" | "Reddit" | "X" | "RSS"
    url: string
    publishedAt: string
    author?: string
    category?: string
    summary?: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

export async function getHotspots(): Promise<Hotspot[]> {
    try {
        const res = await fetch(`${API_BASE_URL}/hotspots/`, { cache: 'no-store' })
        if (!res.ok) throw new Error('Failed to fetch hotspots')
        return res.json()
    } catch (error) {
        console.error("Error fetching hotspots:", error)
        return []
    }
}

export async function getFeed(): Promise<NewsItem[]> {
    try {
        const res = await fetch(`${API_BASE_URL}/feed/`, { cache: 'no-store' })
        if (!res.ok) throw new Error('Failed to fetch feed')
        return res.json()
    } catch (error) {
        console.error("Error fetching feed:", error)
        return []
    }
}
