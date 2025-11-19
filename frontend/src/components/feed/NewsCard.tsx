import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { ExternalLink, Calendar, User } from "lucide-react"
import Link from "next/link"

interface NewsCardProps {
    title: string
    source: string
    url: string
    publishedAt: string
    author?: string
    category?: string
    summary?: string
}

export function NewsCard({ title, source, url, publishedAt, author, category, summary }: NewsCardProps) {
    return (
        <Card className="hover:bg-accent/5 transition-colors border-none shadow-none bg-transparent">
            <CardHeader className="pb-2 px-0">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs font-normal">
                            {source}
                        </Badge>
                        {category && (
                            <Badge variant="secondary" className="text-xs font-normal">
                                {category}
                            </Badge>
                        )}
                    </div>
                    <span className="text-xs text-muted-foreground flex items-center">
                        <Calendar className="mr-1 h-3 w-3" />
                        {publishedAt}
                    </span>
                </div>
                <CardTitle className="text-lg font-medium leading-snug">
                    <Link href={url} target="_blank" rel="noopener noreferrer" className="hover:underline decoration-primary underline-offset-4">
                        {title}
                    </Link>
                </CardTitle>
            </CardHeader>
            <CardContent className="px-0 pb-4 border-b">
                {summary && (
                    <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                        {summary}
                    </p>
                )}
                <div className="flex items-center justify-between">
                    <div className="flex items-center text-xs text-muted-foreground">
                        {author && (
                            <span className="flex items-center mr-4">
                                <User className="mr-1 h-3 w-3" />
                                {author}
                            </span>
                        )}
                    </div>
                    <Link href={url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary flex items-center hover:text-primary/80">
                        Read Source <ExternalLink className="ml-1 h-3 w-3" />
                    </Link>
                </div>
            </CardContent>
        </Card>
    )
}
