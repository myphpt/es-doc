@[toc]
# 缓存

## Field data cache（字段数据缓存）

字段数据缓存主要用于对字段进行排序或对字段计算聚合。它将所有字段值加载到内存中，以便提供基于文档的对这些值的快速访问。

为字段构建字段数据缓存的成本可能很高，因此建议使用足够的内存来分配它，并保持其加载。

字段数据缓存使用的内存量可以使用`indices.fielddata.cache.size`来控制。

> 注意:重新加载不适合你缓存的字段数据将是昂贵的，性能很差。

```
indices.fielddata.cache.size
字段数据缓存的最大大小，如节点堆空间的30%，或绝对值，如12GB。默认为无限。
```

关联配置 Field data circuit breaker（熔断器）

> 这些是静态设置，必须在集群中的每个数据节点上配置。

字段数据的内存使用情况（节点级别）:

```
curl -XGET "http://node02:9200/_nodes/stats/indices/fielddata?human"
```

响应：

```
"memory_size" : "552b",
"memory_size_in_bytes" : 552,
"evictions" : 0
```

根据索引查看：

```
curl -XGET "http://node02:9200/out-7.7.0-2020.10.29/_stats/fielddata?human"
```



## Node query cache（节点查询缓存）

查询缓存负责缓存查询的结果。每个节点都有一个由所有分片共享的查询缓存。缓存实现了一种LRU回收策略:当缓存满了时，会回收最近最少使用的数据，以便为新数据让路。

> 无法查看被缓存的内容。
>
> 查询缓存仅缓存在filter上下文中使用的查询。

以下设置是静态的，必须在集群中的每个数据节点上配置:

```
indices.queries.cache.size 
控制 filter cache的内存大小，默认为10%。接受百分比值(如5%)或精确值(如512mb)。
```

以下设置是一个索引设置，可以在每个索引的基础上配置:

```
index.queries.cache.enabled 
控制是否启用查询缓存。接受true(默认值)或false。
```

节点查询缓存使用情况：

```
curl -XGET "http://node02:9200/_nodes/stats/indices/query_cache?human"
```

响应：

```json
    "query_cache" : {
          "memory_size" : "0b",
          "memory_size_in_bytes" : 0,
          "total_count" : 96,
          "hit_count" : 0,
          "miss_count" : 96,
          "cache_size" : 0,
          "cache_count" : 0,
          "evictions" : 0
        }
```

索引查询缓存的使用情况：

```
curl -XGET "http://node02:9200/out-7.7.0-2020.10.29/_stats/query_cache?human"
```



## Indexing buffer（索引缓冲区）

索引缓冲区用于存储新索引的文档。当它填满时，缓冲区中的文档被写到磁盘上的一个段。它可以在节点上的所有分片上划分。

以下设置是静态的，必须在集群中的每个数据节点上配置:

```
indices.memory.index_buffer_size 
接受百分比或字节大小值。默认值为10%，这意味着分配给一个节点的堆总量的10%将用作所有分片之间共享的索引缓冲区大小。

indices.memory.min_index_buffer_size 
如果index_buffer_size指定为百分比，那么这个设置可以用来指定绝对最小值。默认为48 mb。

indices.memory.max_index_buffer_size 
如果index_buffer_size指定为百分比，那么这个设置可以用来指定绝对最大值。默认为无限。
```



## Shard request cache（分片请求缓存）

 当针对一个索引或多个索引运行搜索请求时，每个涉及的分片都在本地执行搜索，并将其本地结果返回到协调节点，该节点将这些分片级结果合并为一个“全局”结果集。

分片级请求缓存模块在每个分片上缓存本地结果。 这允许频繁使用（并且可能很繁重）的搜索请求几乎立即返回结果。 请求高速缓存非常适合日志记录用例，在这种情况下，只有最新索引才被主动更新-较旧索引的结果将直接从缓存中提供。

> 默认情况下，请求缓存将仅缓存size = 0时的搜索请求结果，因此将不缓存hits，但将缓存hits.total，aggregations, 和suggestions。
>
> 使用now的大多数查询无法缓存。



### 缓存失败

缓存是自动化的——它保持了与非缓存搜索相同的接近实时的结果。

缓存的结果在分片刷新时自动失效，但只有在分片中的数据实际发生更改时才会失效。换句话说，您将总是从缓存中获得与未执行的搜索请求相同的结果。

刷新间隔越长，缓存的记录保持有效的时间就越长。如果缓存已满，那么最近最少使用的缓存键将被逐出。

手动调整缓存过期：

```
POST /kimchy,elasticsearch/_cache/clear?request=true
```



### 启用/禁用缓存

默认情况下，缓存是启用的，但可以禁用时，创建一个新的索引如下:

```
PUT /my_index
{
  "settings": {
    "index.requests.cache.enable": false
  }
}
```

也可以动态启用或禁用一个现有的索引的设置:

```
PUT /my_index/_settings
{ "index.requests.cache.enable": true }
```



### 根据请求启用/禁用缓存

request_cache查询字符串参数可用于根据每个请求启用或禁用缓存。如果设置，它将覆盖索引级设置:

```
GET /my_index/_search?request_cache=true
{
  "size": 0,
  "aggs": {
    "popular_colors": {
      "terms": {
        "field": "colors"
      }
    }
  }
}

```

> 如果你的查询使用的脚本，其结果是不确定的(例如，它使用一个随机函数或引用当前时间)，你应该设置request_cache标志为false，以禁用该请求的缓存。

即使在索引设置中启用了请求缓存，size大于0的请求也不会被缓存。要缓存这些请求，需要使用query-string参数。



### 缓存Key

整个JSON主体被用作缓存键。这意味着如果JSON发生了变化——例如，如果键以不同的顺序输出——那么缓存键将不会被识别。

大多数JSON库都支持一种规范模式，该模式确保JSON键始终按照相同的顺序发出。此规范模式可用于应用程序中，以确保始终以相同的方式序列化请求。

缓存是在节点级别管理的，默认最大大小为堆的1%。可以在config/elasticsearch.yml中更改:

```
indices.requests.cache.size: 2%
```

此外，还可以使用`indices.requests.cache.expire`设置，以指定缓存结果的TTL。当索引刷新时，陈旧的结果将自动失效。此设置仅为完整性起见而提供。



### 缓存使用监控

节点级别的缓存使用情况查看：

```
GET /_nodes/stats/indices/request_cache?human
```

响应：

```json
"request_cache" : {
          "memory_size" : "917.7kb",
          "memory_size_in_bytes" : 939768,
          "evictions" : 0,
          "hit_count" : 3944,
          "miss_count" : 1342
        }
```

索引级别的缓存使用情况查看：

```
curl -XGET "http://node02:9200/_stats/request_cache?human"
curl -XGET "http://node02:9200/out-7.7.0-2020.10.29/_stats/request_cache?human"
```



## 缓存查询

```
curl -XGET "http://node02:9200/_nodes/stats/indices/fielddata,query_cache,request_cache?human"
```
# 熔断机制

Elasticsearch包含多个断路器用于防止操作造成OutOfMemoryError。每个断路器指定了它可以使用多少内存的限制。

此外，还有一个父级断路器，它指定可以跨所有断路器使用的内存总量。这些设置可以在活动集群上动态更新。

## Parent circuit breaker（父级断路器）

 Parent circuit breaker可配置如下设置:

```
indices.breaker.total.limit 
Parent circuit breaker的总的起始限制，默认为JVM堆的70%。
```



## Field data circuit breaker（字段数据断路器）

 field data circuit breaker 允许Elasticsearch测算需要加载的字段数据内存总量。然后，它可以通过引发异常来防止字段数据加载。默认情况下，该限制配置为最大JVM堆的60%。可配置以下参数:

```
indices.breaker.fielddata.limit 
字段数据内存限制，默认为JVM堆的60%

indices.breaker.fielddata.overhead 
字段数据负载，一个常数，默认为1.03
```



## Request circuit breaker（请求断路器）

 Request circuit breaker允许Elasticsearch防止每个请求的数据结构(例如，在请求期间用于计算聚合的内存)超过一定数量的内存。

```
indices.breaker.request.limit 
请求内存限制，默认为JVM堆的60%

indices.breaker.request.overhead 
请求负载，一个常数，默认为1
```



执行的 requests circuit breaker允许Elasticsearch限制所有当前活跃的传入请求的内存使用在传输或HTTP水平超过一个节点上的一定数量的内存。内存使用情况基于请求本身的内容长度。

```
network.breaker.inflight_requests.limit 
挂起的请求短路器内存限制，默认为100%的JVM堆。这意味着，它由父断路器控制。

network.breaker.inflight_requests.overhead 
所有挂起请求的负载，一个常数，默认为1。
```



## Accounting requests circuit breaker

Accounting requests circuit breaker允许Elasticsearch限制请求完成后未释放的内存中所保存内容的内存使用量。 这包括Lucene段占用的内存。

```
indices.breaker.accounting.limit 
计费断路器内存限制，默认为JVM堆的100%。这意味着，它是由限父断路器控制。

indices.breaker.accounting.overhead 
计费断路器负载，一个常数，默认为1
```



## 脚本编译断路器

与以前的基于内存的断路器略有不同，脚本编译断路器限制一段时间内内联脚本编译的数量。

```
script.max_compilations_rate 
限制在一定的时间间隔内允许编译的唯一动态脚本的数量。默认值为75/5m，即每5分钟75条。
```



其他资料参考：

https://www.easyice.cn/archives/367