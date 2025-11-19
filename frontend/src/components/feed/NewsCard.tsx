import Link from "next/link"
import { ExternalLink, Calendar, User } from "lucide-react"
import { cn } from "@/lib/utils"

interface NewsCardProps {
    title: string
    source: string
    url: string
    publishedAt: string
    author?: string
    category?: string
    summary?: string
    className?: string
}

export function NewsCard({
    title,
    source,
    url,
    publishedAt,
    author,
    category,
    summary,
    className,
}: NewsCardProps) {
    return (
        <Link
            href={url}
            target="_blank"
            className={cn(
                "group block border-2 border-black bg-white p-5 shadow-hard-sm transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-hard",
                className
            )}
        >
            <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider">
                    <div className="flex items-center gap-3">
                        <span className="bg-black text-white px-2 py-0.5">{source}</span>
                        <span className="flex items-center gap-1 text-gray-500">
                            <Calendar className="h-3 w-3" />
                            {publishedAt}
                        </span>
                    </div>
                    {category && (
                        <span className="bg-accent border border-black px-2 py-0.5 text-[10px] font-bold">
                            {category}
                        </span>
                    )}
                </div>

                <h3 className="text-lg font-bold leading-tight group-hover:underline decoration-2 underline-offset-2">
                    {title}
                </h3>

                {summary && (
                    <p className="line-clamp-2 text-sm font-medium text-gray-600">
                        {summary}
                    </p>
                )}

                <div className="flex items-center justify-between pt-2 border-t-2 border-gray-100 mt-2">
                    <div className="flex items-center gap-2 text-xs font-bold text-gray-500">
                        {author && (
                            <span className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {author}
                            </span>
                        )}
                    </div>
                    <ExternalLink className="h-4 w-4 text-black transition-transform group-hover:rotate-45" />
                </div>
            </div>
        </Link>
    )
}

