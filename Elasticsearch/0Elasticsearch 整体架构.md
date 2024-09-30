# Elasticsearch整体架构

底层原理

检索

开发

文本分析

聚合

查询

映射

模块

Kibana

节点间通信9300端口

一个主分片最大能够存储 Integer.MAX_VALUE - 128 大约是2亿条的样子

## 集群管理

### Cluster

集群健康：集群的健康

节点 Node

Index

Shard

Segments

allocation

settings

repositories

任务 tasks pending_tasks

线程池 thread_pool

远程集群 Remote Cluster

缓存 Cache

* Shard Request
* Node Query
* FieldData

相似度

文件系统

网络代理

事务日志

熔断机制

慢日志

发现机制

本地网关

## 索引管理

索引冻结

索引生命周期管理

索引删除

索引开启

索引关闭

索引重建

索引刷新

索引收缩

索引预排序

索引模板

索引恢复

索引滚动

索引拆分

索引别名

索引阻塞

## 分片管理

分片分配

## 文档管理

插入 PUT twitter/_doc/1

更新 POST test/_doc/1/_update

删除 DELETE /twitter/_doc/1

获取 GET <index>/_doc/<_id>

## 数据管理

备份恢复

时间序列 DataStream

安全事件 EQL Search

数据转换 Ingest Node

表格查询 SQL

脚本 Scripting

集群监控 Monitor Cluster

集群高可用

命令行工具

数据管理 Data Management

# 查询

<https://www.yuque.com/qzhg29/tnbgcb/yschr2>

# 聚合

<https://www.yuque.com/qzhg29/tnbgcb/yschr2>

# 映射

<https://www.yuque.com/qzhg29/tnbgcb/aksv69>

# 分片重分配

<https://www.yuque.com/qzhg29/wuryzp/si1ukq>

# 索引分片分配

<https://www.yuque.com/qzhg29/wuryzp/si1ukq>

# Elasticsearch资源汇总

[Elasticsearch: The Definitive Guide](https://www.elastic.co/guide/en/elasticsearch/guide/master/index.html)

[Elasticsearch Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)

[Elasticsearch功能列表](https://www.elastic.co/cn/elasticsearch/features#encryption-at-rest-support)

[issue](https://github.com/elastic/elasticsearch/issues)

[elasticsearch-autoops](https://opster.com/elasticsearch-autoops/)

[ORM框架-Easy-Es](https://www.easy-es.cn/pages/ec7460/)

## 合集

官方文档<https://www.elastic.co/guide/en/elasticsearch/reference/6.5/index.html>

中文社区：<https://elasticsearch.cn/>

权威指南：<https://www.elastic.co/guide/en/elasticsearch/guide/master/index.html>

权威指南中文版：<https://www.elastic.co/guide/cn/elasticsearch/guide/current/index.html>

Elastic 中国社区官方博客：<https://elasticstack.blog.csdn.net/>

[Elasticsearch 开发人员最佳实践指南—Elastic Stack 实战手册](https://developer.aliyun.com/article/784171?spm=a2c6h.23118828.J_5603110340.59.65f6256dzveOxR)

[《Elastic Stack 实战手册》早鸟版](https://developer.aliyun.com/topic/elasticstack/playbook?spm=a2c6h.21375034.J_9982055890.2.3f36155csBKGLn)

<https://issues.apache.org/jira/projects/LUCENE/issues/LUCENE-10053?filter=allopenissues>

<https://github.com/elastic/elasticsearch/issues>

<https://github.com/dzharii/awesome-elasticsearch>

<https://esdoc.bbossgroups.com/#/>

<https://easyice.cn/>

<https://elastic.blog.csdn.net/>

<https://opster.com/blogs/improve-elasticsearch-search-performance/>

<https://docs.logz.io/>

## 教程

Elastic 中国社区官方博客：<https://elasticstack.blog.csdn.net/?type=blog>

稀土掘金：<https://juejin.cn/user/2612095360441448>

如何做一个搜索框：<https://elastic-search-in-action.medcl.com/index.html>

博客：<https://www.jianshu.com/u/pEBdkp>

《Elasticsearch 源码解析与实战》作者：<https://easyice.cn/>

阿里云Elasticsearch 技术团队：<https://developer.aliyun.com/group/es?spm=a2c6h.14164896.0.0.616a4417yGhb0M#/?_k=mdu84j>

知乎中的Elasticsearch（内核原理）：<https://www.zhihu.com/column/Elasticsearch>

腾讯云Elasticsearch实验室：<https://cloud.tencent.com/developer/column/2428>

公众号博客：<https://elastic.blog.csdn.net>

Elasticsearch权威指南中文版：<https://github.com/elasticsearch-cn/elasticsearch-definitive-guide/blob/cn/010_Intro/05_What_is_it.asciidoc>

Elastic：菜鸟上手指南：<https://zhuanlan.zhihu.com/p/98889897?utm_source=com.zoho.notebook&utm_medium=social&utm_oi=1256917437280907264>

## 文章

可否完全使用ElasticSearch代替数据库存储？<https://www.zhihu.com/question/45510463/answer/2146695119?utm_source=com.zoho.notebook&utm_medium=social&utm_oi=1256917437280907264>

[一次看完28个关于ES的性能调优技巧](https://blog.csdn.net/u013256816/article/details/110017119)

[如何解决ES的性能问题](https://elasticsearch.cn/article/708)

[源码编译](https://zhuanlan.zhihu.com/p/188725714)

[<漫谈ElasticSearch>关于ES性能调优几件必须知道的事](https://www.cnblogs.com/guguli/p/5218297.html)

[腾讯Elasticsearch调优实践](https://mp.weixin.qq.com/s/0TMESj2Z-XK2PzwBQo0Mpg)

[从10秒到2秒！ElasticSearch性能调优实践](https://developer.51cto.com/article/591335.html)

[干货 | Elasticsearch索引管理利器——Curator深入详解](https://blog.csdn.net/laoyang360/article/details/85882832)

[预加载fileddata](https://www.elastic.co/guide/cn/elasticsearch/guide/current/preload-fielddata.html#preload-fielddata)

[聚合后分页](https://mp.weixin.qq.com/s?__biz=MzI2NDY1MTA3OQ%3D%3D&chksm=eaa82a0cdddfa31a268fc2414603d3b0a6fe6fbe3c8a9dd32f1d54e4002f0e113b21aba161c2&idx=1&mid=2247483940&scene=21&sn=4cb3b32b1d357691d5da21e83d973a83#wechat_redirect)

[Elastic Benchmarks](https://benchmarks.elastic.co/index.html)

[Elasticsearch Performance Tuning Practice at eBay](https://tech.ebayinc.com/engineering/elasticsearch-performance-tuning-practice-at-ebay/)

[How to monitor Elasticsearch performance](https://www.datadoghq.com/blog/monitor-elasticsearch-performance-metrics/)

[Queries and Filters](https://www.elastic.co/guide/en/elasticsearch/guide/master/_queries_and_filters.html)

[WHY IS MY ELASTICSEARCH QUERY SLOW?](https://www.objectrocket.com/blog/elasticsearch/why-is-my-elasticsearch-query-slow/)

[Elasticsearch 7.0 正式发布，盘他！](https://mp.weixin.qq.com/s?__biz=MzI2NDY1MTA3OQ==&mid=2247484406&idx=1&sn=0ab300356bd21f8c02d1a55f7ec20caa&chksm=eaa82bdedddfa2c8b6292847508cd230a4ff76eeb29bd91acb4d2aee664aa3b4d1c639f7cda0#rd)

[A Profile a Day Keeps the Doctor Away: The Elasticsearch Search Profiler](https://www.elastic.co/cn/blog/a-profile-a-day-keeps-the-doctor-away-the-elasticsearch-search-profiler)

[Slow Logs in Elasticsearch](https://qbox.io/blog/slow-logs-in-elasticsearch-search-index-config-example)

[number?keyword?傻傻分不清楚](https://elasticsearch.cn/article/446)

[高级调优：查找并修复 Elasticsearch 慢查询](https://www.elastic.co/cn/blog/advanced-tuning-finding-and-fixing-slow-elasticsearch-queries)

[Improving the performance of high-cardinality terms aggregations](https://www.elastic.co/cn/blog/improving-the-performance-of-high-cardinality-terms-aggregations-in-elasticsearch)

[Elasticsearch 缓存深度剖析：一次提高一种缓存的查询速度](https://www.elastic.co/cn/blog/elasticsearch-caching-deep-dive-boosting-query-speed-one-cache-at-a-time)

[Elasticsearch 优化排序查询，更快获得结果](https://www.elastic.co/cn/blog/optimizing-sort-queries-in-elasticsearch-for-faster-results)

[How we're making date_histogram aggregations faster than ever in Elasticsearch 7.11](https://www.elastic.co/cn/blog/how-we-made-date-histogram-aggregations-faster-than-ever-in-elasticsearch-7-11)

新浪是如何分析处理32亿条实时日志的：<http://dockone.io/article/505>

[Elasticsearch：运用 doc-value-only 字段来实现更快的索引速度并节省空间 - Elastic Stack 8.1](https://juejin.cn/post/7074795866082508808)

腾讯万亿级 Elasticsearch 技术解密<https://zhuanlan.zhihu.com/p/99184436?utm_source=com.zoho.notebook&utm_medium=social&utm_oi=1256917437280907264>

腾讯万亿级 Elasticsearch 内存效率提升技术解密<https://zhuanlan.zhihu.com/p/146083622?utm_source=com.zoho.notebook&utm_medium=social&utm_oi=1256917437280907264>

[How to monitor Elasticsearch performance](https://www.datadoghq.com/blog/monitor-elasticsearch-performance-metrics/)

[Queries and Filters](https://www.elastic.co/guide/en/elasticsearch/guide/master/_queries_and_filters.html)

[WHY IS MY ELASTICSEARCH QUERY SLOW?](https://www.objectrocket.com/blog/elasticsearch/why-is-my-elasticsearch-query-slow/)

[Elasticsearch 7.0 正式发布，盘他！](http://mp.weixin.qq.com/s?__biz=MzI2NDY1MTA3OQ==&mid=2247484406&idx=1&sn=0ab300356bd21f8c02d1a55f7ec20caa&chksm=eaa82bdedddfa2c8b6292847508cd230a4ff76eeb29bd91acb4d2aee664aa3b4d1c639f7cda0#rd)

[number?keyword?傻傻分不清楚](https://elasticsearch.cn/article/446)

[高级调优：查找并修复 Elasticsearch 慢查询](https://www.elastic.co/cn/blog/advanced-tuning-finding-and-fixing-slow-elasticsearch-queries)

[Improving the performance of high-cardinality terms aggregations](https://www.elastic.co/cn/blog/improving-the-performance-of-high-cardinality-terms-aggregations-in-elasticsearch)

[高级调优：查找并修复 Elasticsearch 慢查询](https://www.elastic.co/cn/blog/advanced-tuning-finding-and-fixing-slow-elasticsearch-queries)

[How we're making date_histogram aggregations faster than ever in Elasticsearch 7.11](https://www.elastic.co/cn/blog/how-we-made-date-histogram-aggregations-faster-than-ever-in-elasticsearch-7-11)

[Elasticsearch 优化排序查询，更快获得结果](https://www.elastic.co/cn/blog/optimizing-sort-queries-in-elasticsearch-for-faster-results)

[LUCENE issues](https://issues.apache.org/jira/projects/LUCENE/issues/LUCENE-10053?filter=allopenissues)

[Elasticsearch: The Definitive Guide](https://www.elastic.co/guide/en/elasticsearch/guide/master/index.html)

[预加载 fielddata](https://www.elastic.co/guide/cn/elasticsearch/guide/current/preload-fielddata.html)

## 搜索引擎

[OpenSearch](https://opensearch.org/)

[OpenSearch GitHub](https://github.com/opensearch-project/OpenSearch)

[MeiliSearch Github](https://github.com/meilisearch/MeiliSearch)

## 生态管理

Kibana

Elasticsearch Head

# 事务日志

<https://www.yuque.com/qzhg29/wuryzp/ii8cu4>

# 慢日志

<https://www.yuque.com/qzhg29/wuryzp/tn2uat>

# Elasticsearch 程序开发

相关性评分

## 和Elasticsearch交互

### Java Client

Elasticsearch8版本之前  Java High Level REST Client

Elasticsearch8版本 Elasticsearch Client

### RESTful API

9200端口

## 数据映射

## 数据查询

bool query

term query

Span queries

Specialized queries

分页查询

suggest

nested query

highlight query

geo query

scroll query

## 数据搜索

`match_phrase` 短语查询：匹配相关联的两个短语

高亮搜索highlight：在每个搜索结果中 *高亮* 部分文本片段

match query

近邻搜索

Collapse

Rescore

Profile

msearch

sort

inner hits

validate

store

source

search shards

ranking evaluation

post filter

field cap abilities

explain

doc value

## 数据聚合

桶聚合

指标聚合

管道聚合

# Node Query Cache

 filter context 使用的查询结果被缓存在节点查询缓存中，以便快速查找。每个节点有一个查询缓存，由所有的分片共享。cache使用LRU逐出策略:当cache满时，逐出最近最少使用的查询结果，为新数据让路。不能检查查询缓存的内容。

Term queries和queries，并且 filter context 之外的内容不适合缓存

默认情况下，缓存最多保存10000个查询，占总堆空间的10%。为了确定一个查询是否适合缓存，Elasticsearch维护一个查询历史记录来跟踪发生的事件。如果一个段包含至少10000个文档，并且该段至少拥有一个分片总文档的3%，那么缓存是在每个段的基础上进行的。因为缓存是按段进行的，所以合并段可以使缓存的查询失效。

以下设置为静态设置，必须在集群的每个数据节点上进行配置:

```
# Controls the memory size for the filter cache. Accepts either a percentage value, like 5%, or an exact value, like 512mb. Defaults to 10%.
indices.queries.cache.size:10%

```

  下面的设置是一个索引设置，可以在每个索引的基础上配置。只能在创建索引时或关闭索引时设置:

```
index.queries.cache.enabled
(Static) Controls whether to enable query caching. Accepts true (default) or false.
```

# Field Data Cache

```
https://www.yuque.com/qzhg29/wuryzp/xs7e1b
```

# 熔断机制

<https://www.yuque.com/qzhg29/wuryzp/zfc9xu>

# 缓存机制

<https://www.yuque.com/qzhg29/wuryzp/so5nl9>

# 文件系统

<https://www.yuque.com/qzhg29/wuryzp/sbxa7k>

# 网络代理

<https://www.yuque.com/qzhg29/wuryzp/ygesev>

# 本地网关

<https://www.yuque.com/qzhg29/wuryzp/si1ukq>

<https://www.elastic.co/guide/en/elasticsearch/reference/current/troubleshooting.html>

##

# 安全事件 EQL

<https://www.yuque.com/qzhg29/wuryzp/mgbfcy>

# 数据转换 Ingest Node

<https://www.yuque.com/qzhg29/wuryzp/etcdus>

# 表格查询 SQL

<https://www.yuque.com/qzhg29/wuryzp/iue0nq>

# 脚本 scripting

<https://www.yuque.com/qzhg29/wuryzp/xqrpbg>

# 命令行工具-Command line tools

  <https://www.elastic.co/guide/en/elasticsearch/reference/current/commands.html>

elasticsearch-certutil

# Elasticsearch解决方案

重建索引的时候，机器负载太高

机器负载分布不均衡

业务的查询和流量不可控

## Elasticsearch优化

# 文件系统存储

存储模块允许控制如何在磁盘上存储和访问索引数据。

有不同的文件系统实现或存储类型。默认情况下，Elasticsearch将根据操作环境选择最佳实现。通过将其添加到`config/elasticsearch.yml`，可以覆盖所有索引文件:

```
index.store.type: niofs

参数：
fs
默认文件系统实现。这将根据操作环境选择最佳的实现，目前在所有受支持的系统上都是mmapfs，但可能会更改。
```

它是一个静态设置，可以在索引创建时按索引进行设置:

```
PUT /my_index
{
  "settings": {
    "index.store.type": "niofs"
  }
}
```

# 文件系统缓存

默认情况下，Elasticsearch完全依赖于操作系统文件系统缓存来缓存I/O操作。可以设置index.store。预加载是为了告诉操作系统在打开时将热索引文件的内容加载到内存中。此设置接受以逗号分隔的文件扩展名列表:扩展名在列表中的所有文件将在打开时预先加载。这对于提高索引的搜索性能非常有用，特别是在主机操作系统重新启动时，因为这会导致文件系统缓存被销毁。但是请注意，这可能会降低打开索引的速度，因为只有在数据加载到物理内存之后，索引才可用。

此设置仅是最佳效果，根据存储类型和主机操作系统，可能根本不起作用。

静态设置`config/elasticsearch.yml`：

```
index.store.preload: ["nvd", "dvd"]
```

或者在创建时指定：

```
PUT /my_index
{
  "settings": {
    "index.store.preload": ["nvd", "dvd"]
  }
}
```

默认值是空数组，这意味着没有任何内容会被及时加载到文件系统缓存中。对于主动搜索的索引，可能需要将其设置为["nvd"， "dvd"]，这将导致规范和文档值被急切地加载到物理内存中。这是我们首先要考虑的两个扩展，因为Elasticsearch对它们执行随机访问。

可以使用通配符来指示应该预先加载所有文件：`index.store.preload: ["*"]`.。但是要注意,一般不是有用的所有文件加载到内存中,尤其是存储字段和词向量,所以可能是个更好的选择设置`["nvd", "dvd", "tim", "doc", "dim"]`,将预加载norms, doc values,terms dictionaries, postings lists 和points,这是最重要的部分索引搜索和聚合。

> 注意，这个设置对于大于主机主内存大小的索引可能是危险的，因为它会导致文件系统缓存在大型合并后重新打开时被销毁，这会使索引和搜索变慢。
