import { useState } from "react"
import { TrendingUp, ArrowRight, ExternalLink } from "lucide-react"
import { cn } from "@/lib/utils"
import { Modal } from "@/components/ui/Modal"
import { getHotspotDetails, HotspotDetail } from "@/lib/api"

interface HotspotCardProps {
    id: number
    title: string
    summary: string
    score: number
    itemsCount: number
    time: string
    className?: string
}

export function HotspotCard({
    id,
    title,
    summary,
    score,
    itemsCount,
    time,
    className,
}: HotspotCardProps) {
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [details, setDetails] = useState<HotspotDetail | null>(null)
    const [isLoading, setIsLoading] = useState(false)

    const handleOpenModal = async () => {
        setIsModalOpen(true)
        if (!details) {
            setIsLoading(true)
            const data = await getHotspotDetails(id)
            setDetails(data)
            setIsLoading(false)
        }
    }

    return (
        <>
            <div
                className={cn(
                    "group relative flex flex-col justify-between overflow-hidden border-2 border-black bg-white p-6 shadow-hard transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]",
                    className
                )}
            >
                <div className="space-y-4">
                    <div className="flex items-center justify-between border-b-2 border-black pb-3">
                        <div className="flex items-center gap-2 bg-accent px-3 py-1 border-2 border-black">
                            <TrendingUp className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase">Score: {score.toFixed(0)}</span>
                        </div>
                        <span className="text-xs font-mono font-bold">{time}</span>
                    </div>

                    <div className="space-y-3">
                        <h3 className="line-clamp-2 text-2xl font-black leading-none tracking-tight">
                            {title}
                        </h3>
                        <p className="line-clamp-3 text-sm font-medium leading-relaxed text-gray-600">
                            {summary}
                        </p>
                    </div>
                </div>

                <div className="mt-6 flex items-center justify-between pt-4">
                    <div className="flex items-center gap-2 text-xs font-bold">
                        <span className="flex h-6 w-6 items-center justify-center border-2 border-black bg-black text-white">
                            {itemsCount}
                        </span>
                        <span className="uppercase tracking-wider">Events</span>
                    </div>
                    <button
                        onClick={handleOpenModal}
                        className="group/btn flex items-center gap-2 text-sm font-bold uppercase hover:underline cursor-pointer"
                    >
                        Read More <ArrowRight className="h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
                    </button>
                </div>
            </div>

            <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} className="max-w-3xl h-[80vh] flex flex-col">
                <div className="space-y-6 h-full flex flex-col">
                    <div className="flex-shrink-0">
                        <h2 className="text-2xl font-black pr-8">{title}</h2>
                        <p className="mt-2 text-gray-600">{summary}</p>
                    </div>

                    <div className="flex-grow overflow-y-auto pr-2 -mr-2">
                        {isLoading ? (
                            <div className="py-10 text-center font-bold animate-pulse">Loading details...</div>
                        ) : details ? (
                            <div className="space-y-4">
                                <h3 className="text-lg font-bold uppercase border-b-2 border-black pb-2 sticky top-0 bg-white z-10">
                                    Related News ({details.items.length})
                                </h3>
                                <div className="grid gap-4 pb-4">
                                    {details.items.map((item) => (
                                        <a
                                            key={item.id}
                                            href={item.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="block p-4 border-2 border-black hover:bg-accent transition-colors group/item"
                                        >
                                            <div className="flex justify-between items-start gap-4">
                                                <div>
                                                    <h4 className="font-bold group-hover/item:underline">{item.title}</h4>
                                                    {item.summary && <p className="text-sm text-gray-600 mt-1 line-clamp-2">{item.summary}</p>}
                                                    <div className="flex gap-2 mt-2 text-xs font-mono text-gray-500">
                                                        <span className="bg-black text-white px-1">{item.source}</span>
                                                        <span>{item.publishedAt}</span>
                                                        {item.author && <span>by {item.author}</span>}
                                                    </div>
                                                </div>
                                                <ExternalLink className="h-4 w-4 flex-shrink-0" />
                                            </div>
                                        </a>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="py-10 text-center text-red-500 font-bold">Failed to load details.</div>
                        )}
                    </div>
                </div>
            </Modal>
        </>
    )
}
