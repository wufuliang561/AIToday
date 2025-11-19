AI 热点资讯聚合平台 - 产品需求文档 (PRD) v1.0

1. 项目概述

1.1 背景

AI 领域信息爆炸，信噪比低。用户需要一个能够自动从 YouTube, Reddit, X (Twitter) 及 RSS 中获取高价值信息，并自动进行翻译、分类、去重和热点聚合的系统。

1.2 核心价值

降噪: 通过指定高质量信源 + 算法去重。

提效: 中文翻译 + 核心摘要。

聚焦: 区分“全网热点”与“日常资讯流”。

2. 系统架构与流程图

(概念流程)

Fetch: 抓取器获取元数据 (标题, 链接, 互动数据).

Score: 本地算法计算初始热度值 (Heat Score).

Process (LLM): 翻译标题, 总结内容(仅X), 智能分类.

Store: 存入 Postgres raw_items 表.

Cluster: 周期性任务扫描库中未归档数据 -> 向量聚合 -> 生成热点 -> 更新库.

Display: 前端 React 分别请求“热点接口”和“信息流接口”.

3. 功能需求说明 (Functional Requirements)

3.1 数据采集源 (Data Sources)

渠道

抓取内容

必须元数据 (用于热度计算)

LLM 处理策略

YouTube

标题, 链接

播放量 (Views), 发布时间

翻译标题

Reddit

标题, 链接

点赞数 (Upvotes), 评论数

翻译标题

X (Twitter)

正文文本, 链接

浏览量, 点赞, 转推

总结正文 + 翻译

RSS

标题, 链接

无 (给予基础权重)

翻译标题

3.2 评分与预处理逻辑 (Scoring & Processing)

原则: 在数据落库前，必须计算出 heat_score。

3.2.1 热度计算算法 (Normalize Heat Score)

由于不同平台量级不同，需归一化处理 (0-100分制):

$S_{yt} = \min(100, \frac{\text{Views}}{10000} \times 2)$ (万播权重)

$S_{rd} = \min(100, \text{Upvotes} \times 0.5 + \text{Comments} \times 1)$

$S_{x} = \min(100, \frac{\text{Likes}}{50} + \text{Retweets} \times 2)$

$S_{rss} = 10$ (RSS 默认低热度，除非后续聚合命中)

最终热度: base_score * source_weight (如指定的大V权重可设为 1.5)

3.2.2 LLM 处理 (OpenAI API)

翻译: 统一翻译为中文。

分类: [实用工具, 学术论文, 行业动态, 其他]。

X总结: 将推文缩写为一句话中文摘要。

3.3 聚合与去重 (Clustering & Aggregation)

触发时机: 每次采集任务完成后执行。

逻辑:

提取过去 24h 内 cluster_id 为空的 Item。

使用 Embeddings (如 text-embedding-3-small) 计算标题语义相似度。

成团条件: 相似度 > 0.85 且 来源数量 >= 2 (或单条热度极高 > 80)。

生成热点:

生成一个概括性标题 (LLM)。

写入 hotspots 表。

将相关 Item 的 cluster_id 更新为该 Hotspot ID。

3.4 前端展示 (React)

3.4.1 板块 A: 全网热点 (Hotspots)

展示条件: 取 hotspots 表中热度最高的前 10 条。

交互:

显示：热点总标题 (e.g., "OpenAI 发布 Sora 模型")。

展开：列出该事件下的所有 Item (Youtube 视频, X 推文)。

互斥: 此处展示过的内容，不再进入下方信息流。

3.4.2 板块 B: 资讯流 (The Feed)

展示条件: 查询 raw_items 表。

过滤规则: WHERE cluster_id IS NULL (确保互斥)。

排序: 按 published_at 倒序。

UI: 卡片式，展示中文标题、分类标签、原始链接。

4. 数据模型设计 (PostgreSQL Schema)

4.1 原始数据表 (raw_items)

存储每一条抓取到的独立信息。

CREATE TABLE raw_items (
    id SERIAL PRIMARY KEY,
    source_platform VARCHAR(20) NOT NULL, -- 'youtube', 'x', 'reddit', 'rss'
    source_id VARCHAR(255) UNIQUE NOT NULL, -- 原始平台ID，防止重复抓取
    
    -- 内容字段
    original_title TEXT NOT NULL,
    original_text TEXT, -- 仅 X 需要存正文
    title_cn TEXT NOT NULL, -- 翻译后的标题
    summary_cn TEXT, -- X 的总结，其他平台为空
    url TEXT NOT NULL,
    
    -- 元数据
    category VARCHAR(50), -- 'tools', 'paper', etc.
    author_name VARCHAR(100),
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 核心算法字段
    heat_score FLOAT DEFAULT 0, -- 预计算的热度值
    cluster_id INT REFERENCES hotspots(id) -- 关联热点，为空则属于普通流
);

-- 索引优化
CREATE INDEX idx_raw_items_cluster ON raw_items(cluster_id);
CREATE INDEX idx_raw_items_time ON raw_items(published_at DESC);


4.2 热点聚合表 (hotspots)

存储聚合后的“大事件”。

CREATE TABLE hotspots (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL, -- AI 生成的聚合标题
    summary TEXT, -- 可选：热点综述
    total_heat_score FLOAT, -- 聚合热度 (子项热度之和 or Max值)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


5. 技术栈选型 (Tech Stack)

Backend: Python 3.11+

FastAPI: 提供前端接口。

APScheduler: 调度每2小时的定时任务。

SQLAlchemy: ORM 操作 Postgres。

Pydantic: 数据校验。

Crawlers:

yt-dlp / Google API (Youtube)

praw (Reddit API)

tweepy 或 第三方 Scraper (X)

feedparser (RSS)

AI / ML:

LangChain + OpenAI (Chat & Embeddings).

scikit-learn (用于简单的聚类计算，如果不用向量库的话)。

Database: PostgreSQL 15+

Frontend: React + Tailwind CSS + Lucide React (Icons)

6. 接口定义 (API Requirements)

GET /api/v1/hotspots

返回 Top 10 热点事件及其包含的 items。

GET /api/v1/feed

Params: page, category

返回 cluster_id 为 null 的 items。