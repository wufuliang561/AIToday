import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { Badge } from "@/components/ui/Badge"
import { Flame, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/Button"

interface HotspotCardProps {
    title: string
    summary?: string
    score: number
    itemsCount: number
    time: string
}

export function HotspotCard({ title, summary, score, itemsCount, time }: HotspotCardProps) {
    return (
        <Card className="group relative overflow-hidden transition-all hover:shadow-md hover:border-primary/20">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <Flame className="h-24 w-24 text-primary" />
            </div>
            <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                    <Badge variant="secondary" className="mb-2">
                        <Flame className="mr-1 h-3 w-3 text-orange-500" />
                        Hotspot
                    </Badge>
                    <span className="text-xs text-muted-foreground">{time}</span>
                </div>
                <CardTitle className="text-xl leading-tight group-hover:text-primary transition-colors">
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                    {summary || "No summary available."}
                </p>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                        <span className="font-medium text-foreground">{score}</span>
                        <span>Heat Score</span>
                        <span>•</span>
                        <span>{itemsCount} sources</span>
                    </div>
                    <Button variant="ghost" size="sm" className="group-hover:translate-x-1 transition-transform">
                        View Details <ChevronRight className="ml-1 h-4 w-4" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
