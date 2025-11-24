import apiClient from './axios';

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

export async function getHotspots(): Promise<Hotspot[]> {
    try {
        const res = await apiClient.get<Hotspot[]>('/hotspots/');
        return res.data;
    } catch (error) {
        console.error("Error fetching hotspots:", error);
        return [];
    }
}

export async function getFeed(): Promise<NewsItem[]> {
    try {
        const res = await apiClient.get<NewsItem[]>('/feed/');
        return res.data;
    } catch (error) {
        console.error("Error fetching feed:", error);
        return [];
    }
}
