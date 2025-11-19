import { getHotspots, getFeed } from "@/lib/api"
import { HotspotCard } from "@/components/hotspot/HotspotCard"
import { NewsCard } from "@/components/feed/NewsCard"

// Actually, for simplicity and "Apple-style", let's just show Hotspots on top and Feed below, or side-by-side on large screens.
// Let's go with a clean vertical layout: Hotspots (Horizontal Scroll) -> Feed (Vertical List).

export default async function Home() {
  const hotspots = await getHotspots()
  const feed = await getFeed()

  return (
    <div className="container py-8 space-y-10">
      {/* Header */}
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">今日 AI 热点</h1>
        <p className="text-muted-foreground">
          汇聚全网 AI 资讯精华。
        </p>
      </div>

      {/* Hotspots Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold tracking-tight">热门事件</h2>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {hotspots.map((hotspot) => (
            <HotspotCard
              key={hotspot.id}
              title={hotspot.title}
              summary={hotspot.summary}
              score={hotspot.score}
              itemsCount={hotspot.itemsCount}
              time={hotspot.time}
            />
          ))}
        </div>
      </section>

      {/* Feed Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold tracking-tight">最新动态</h2>
        </div>
        <div className="space-y-4">
          {feed.map((item) => (
            <NewsCard
              key={item.id}
              title={item.title}
              source={item.source}
              url={item.url}
              publishedAt={item.publishedAt}
              author={item.author}
              category={item.category}
              summary={item.summary}
            />
          ))}
        </div>
      </section>
    </div>
  )
}
