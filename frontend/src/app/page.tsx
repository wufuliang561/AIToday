import { getHotspots, getFeed } from "@/lib/api"
import { HotspotCard } from "@/components/hotspot/HotspotCard"
import { NewsCard } from "@/components/feed/NewsCard"
import FeedSection from "@/components/feed/FeedSection"
import { Header } from "@/components/layout/Header"

export const dynamic = 'force-dynamic'

export default async function Home() {
  const hotspots = await getHotspots()
  const feed = await getFeed()

  return (
    <div className="min-h-screen bg-white bg-grid-pattern font-sans text-black selection:bg-accent selection:text-black">
      <Header />

      <main className="container pb-20 pt-12">
        {/* Hero / Hotspots Section */}
        <section className="mb-20 space-y-8 animate-slide-up">
          <div className="flex flex-col gap-2 border-l-4 border-black pl-6">
            <h2 className="text-5xl font-black tracking-tighter uppercase md:text-7xl">
              Hotspots
            </h2>
            <p className="text-lg font-bold text-gray-500 max-w-xl">
              Curated AI news and events from around the web. Real-time updates.
            </p>
          </div>

          {/* Horizontal Scroll Container */}
          <div className="relative -mx-4 px-4 md:mx-0 md:px-0">
            <div className="flex gap-8 overflow-x-auto pb-8 pt-4 scrollbar-hide snap-x">
              {hotspots.map((hotspot) => (
                <div key={hotspot.id} className="min-w-[85vw] snap-center md:min-w-[450px]">
                  <HotspotCard
                    title={hotspot.title}
                    summary={hotspot.summary}
                    score={hotspot.score}
                    itemsCount={hotspot.itemsCount}
                    time={hotspot.time}
                    className="h-full"
                  />
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Feed Section */}
        <FeedSection items={feed} />
      </main>
    </div>
  )
}
