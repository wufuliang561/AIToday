import { TrendingUp, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface HotspotCardProps {
    title: string
    summary: string
    score: number
    itemsCount: number
    time: string
    className?: string
}

export function HotspotCard({
    title,
    summary,
    score,
    itemsCount,
    time,
    className,
}: HotspotCardProps) {
    return (
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
                        <span className="text-xs font-bold uppercase">Score: {score}</span>
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
                <button className="group/btn flex items-center gap-2 text-sm font-bold uppercase hover:underline">
                    Read More <ArrowRight className="h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
                </button>
            </div>
        </div>
    )
}

