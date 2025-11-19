'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { NewsCard } from './NewsCard';
import { NewsItem } from '@/lib/api';

interface FeedSectionProps {
    items: NewsItem[];
}

const CATEGORIES = ["全部", "AI工具", "学术论文", "行业新闻", "教程指南", "其他"];

export default function FeedSection({ items }: FeedSectionProps) {
    const [activeCategory, setActiveCategory] = useState("全部");

    const filteredItems = activeCategory === "全部"
        ? items
        : items.filter(item => item.category === activeCategory);

    return (
        <section className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b-2 border-black pb-4">
                <h2 className="text-4xl font-black uppercase tracking-tighter">Latest Feed</h2>

                <div className="flex flex-wrap gap-2">
                    {CATEGORIES.map((cat) => (
                        <button
                            key={cat}
                            onClick={() => setActiveCategory(cat)}
                            className={`
                px-4 py-2 font-bold text-sm border-2 border-black transition-all
                ${activeCategory === cat
                                    ? 'bg-black text-white shadow-hard-sm translate-x-[-2px] translate-y-[-2px]'
                                    : 'bg-white text-black hover:bg-accent hover:shadow-hard-sm hover:translate-x-[-2px] hover:translate-y-[-2px]'}
              `}
                        >
                            {cat}
                        </button>
                    ))}
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {filteredItems.map((item, index) => (
                    <motion.div
                        key={item.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                    >
                        <NewsCard
                            title={item.title}
                            source={item.source}
                            url={item.url}
                            publishedAt={item.publishedAt}
                            author={item.author}
                            category={item.category}
                            summary={item.summary}
                        />
                    </motion.div>
                ))}

                {filteredItems.length === 0 && (
                    <div className="col-span-full py-12 text-center border-2 border-black border-dashed bg-white/50">
                        <p className="font-bold text-gray-500">暂无该分类内容</p>
                    </div>
                )}
            </div>
        </section>
    );
}
