# Search

Elasticsearch提供了一个完整的基于JSON的查询DSL(领域特定语言)来定义查询。可以将查询DSL看作查询的AST(抽象语法树)，它由两种类型的子句组成:

Leaf query

子查询子句在特定字段中查找特定值，例如[`match`], [`term`] or[`range`]查询。

Compound query

复合查询子句包装其他子查询或复合查询，并用于以逻辑方式组合多个查询(如bool或dis_max查询)，或用于改变它们的行为(如constant_score查询)。

查询子句的行为取决于它们是在查询上下文中使用还是在筛选上下文中使用。

## 查询环境

查询上下文环境回答了一个问题:“这个文档与这个查询子句匹配得有多好?”。因此除了决定文档是否匹配之外，query子句还计算一个表示文档相对于其他文档匹配程度的_score。

> 利用query查询不仅返回精确匹配的文档，还会根据相关性得分，返回部分匹配的文档。

查询上下文在将查询子句传递给query参数时起作用。

## routing（路由）

当执行搜索时，它将广播到所有的索引/索引分片(在副本之间循环)。可以通过提供路由参数来控制搜索哪个分片。例如，在索引twitter时，路由值可以为用户名:

```
POST /twitter/_doc?routing=kimchy
{
    "user" : "kimchy",
    "postDate" : "2009-11-15T14:12:12",
    "message" : "trying out Elasticsearch"
}
```

在这种情况下，如果我们只想搜索一个特定用户的tweets，我们可以将其指定为路由，导致搜索只命中相关的shard:

```
POST /twitter/_search?routing=kimchy
{
    "query": {
        "bool" : {
            "must" : {
                "query_string" : {
                    "query" : "some query string here"
                }
            },
            "filter" : {
                "term" : { "user" : "kimchy" }
            }
        }
    }
}
```

路由参数可以多值表示为逗号分隔的字符串。这将导致命中与路由值匹配的相分片。

## 自适应选择副本策略

作为以循环方式将请求发送到数据副本的替代方法，可以启用自适应副本选择。这使得协调节点可以根据以下几个标准将请求发送给被认为是“最佳”的副本:

- 协调节点和包含数据副本的节点之间请求的响应时间
- 发送到包含数据的节点上执行搜索请求所花费的时间
- 包含数据的节点上的搜索线程池的队列大小

这可以通过更改动态集群设置来开启。`cluster.routing.use_adaptive_replica_selection`从false到true:

```
PUT /_cluster/settings
{
    "transient": {
        "cluster.routing.use_adaptive_replica_selection": true
    }
}
```

## 全局检索超时

作为请求体搜索的一部分，单个搜索可以有一个超时。由于搜索请求可以有许多来源，Elasticsearch有一个动态的集群级全局搜索超时设置，适用于请求主体中没有设置超时的所有搜索请求。这些请求将在指定时间后被取消，使用下面搜索取消部分中描述的机制。因此，适用于超时响应的所有注意事项。

设置键是search.default_search_timeout，可以使用集群更新设置端点进行设置。默认值是没有全局超时。将此值设置为-1将全局搜索超时重置为无超时。

```
PUT /_cluster/settings
{
    "transient": {
        "search.default_search_timeout": "5m"
    }
}
```

## 检索取消

可以使用标准任务取消机制取消搜索。默认情况下，运行的搜索只检查它是否在段边界上被取消，因此取消可以被大段延迟。可以通过设置动态集群级别的设置搜索来改进搜索取消响应性。`search.low_level_cancellation`设置true。但是，它带来了更频繁的取消检查的额外开销，这在快速运行的大型搜索查询中很明显。更改此设置只影响更改后开始的搜索。

## 并发搜索

默认情况下，Elasticsearch不会根据请求命中的分片数量拒绝任何搜索请求。虽然Elasticsearch会优化协调节点上的搜索执行，但大量的分片会对CPU和内存有显著的影响。以更少的大分片的方式组织数据通常是一个更好的主意。如果想配置一个软限制，可以更新`action.search.shard_count.limit`集群设置，以拒绝触及太多分片的搜索请求。

请求参数`max_concurrent_shard_requests`可以用于控制搜索将为该请求执行的并发分片请求的最大数量。这个参数应该用来防止单个请求超载集群(例如，默认的请求会击中集群中的所有索引，如果每个节点的分片数很高，可能会导致分片请求拒绝)。这个默认值是基于集群中的数据节点数，但最多256个。

## terminate_after

`terminate_after`总是应用在post_filter之后，并在分片上收集到足够的命中率时停止查询和聚合执行。尽管doc所依赖的聚合可能不能反映出点击率。因为聚合应用于post过滤之前，所以在响应中使用总数。

如果只想知道是否有匹配特定查询的文档，可以将大小设置为0，以表示对搜索结果不感兴趣。还可以将`terminate_after`设置为1，以表明只要找到第一个匹配的文档(每个分片)，查询执行就可以终止。

```
GET /_search?q=message:number&size=0&terminate_after=1
```

响应将不包含任何命中，因为大小被设置为0。hits.total将等于0，表示没有匹配的文档，或者大于0，表示在查询被提前终止时，至少有相同数量的文档匹配查询。另外，如果查询提前终止，则在响应中将terminated_early标志设置为true。

响应中的时间包含处理此请求所花费的毫秒数，从节点收到查询后迅速开始，一直到所有搜索相关工作完成，再到将上面的JSON返回给客户机。这意味着它包括在线程池中等待、在整个集群中执行分布式搜索和收集所有结果所花费的时间。

## search_type

在执行分布式搜索时，可以执行不同的执行路径。分布式搜索操作需要分散到所有相关的分片上，然后收集所有的结果。在执行分散/聚集类型时，有几种方法可以做到这一点，特别是对搜索引擎。

执行分布式搜索时的一个问题是要从每个分片检索多少结果。例如，如果有10个分片，第一个分片可能包含从0到10最相关的结果，其他分片结果排在它下面。因此，在执行请求时，需要从所有shard中获得0到10的结果，对它们进行排序，然后返回结果，如果想确保结果正确的话。

另一个与搜索引擎有关的问题是，每个分片都是独立的。在特定的分片上执行查询时，它不考虑Term频率和来自其他分片的其他搜索引擎信息。如果想要支持精确的排序，需要首先从所有分片中收集Term频率来计算全局Term频率，然后使用这些全局频率对每个分片执行查询。

另外，由于需要对结果进行排序，因此在维护正确的排序行为的同时，获取大型文档集甚至滚动可能是一项非常昂贵的操作。对于大的结果集滚动，如果返回文档的顺序不重要，那么最好按`_doc`进行排序。

Elasticsearch非常灵活，允许根据每个搜索请求控制执行的搜索类型。可以通过在查询字符串中设置search_type参数来配置类型。类型是:

**query_then_fetch**

该请求被分为两个阶段处理。在第一个阶段，查询被转发到所有涉及的分片。每个分片执行搜索并生成一个排序后的结果列表，该结果列表位于该分片的本地。每个分片返回足够的信息到协调节点，允许它将分片级别的结果合并并重新排序为全局排序的结果集，并具有最大长度。

在第二阶段，协调节点仅从相关的分片请求文档内容(以及高亮显示的片段，如果有的话)。

如果没有在请求中指定search_type，则这是默认设置。

 **dfs_query_then_fetch**

与“Query Then Fetch”相同，除了初始散射相位，它去计算更精确的评分分布项频率。

```
GET  /book_publisher/_search?&search_type=query_then_fetch
```

## preference

 控制要对哪些分片副本执行搜索的首选项。默认情况下，Elasticsearch会考虑分配感知和自适应副本选择配置，以未指定的顺序从可用的分片副本中进行选择。然而，有时尝试将某些搜索路由到某些分片副本集可能是可取的，例如为了更好地使用每个副本缓存。

```
_primary 
_primary_first
_replica _replica_first 
_only_local 
_local 
_prefer_nodes:abc,xyz 
_shards:2,3 
_only_nodes:abc*,x*yz,... Custom (string) value( 自定义首选项值的最佳候选是Web会话ID或用户名。)
```

例如，使用用户的会话ID xyzabc123如下:

```
GET /_search?preference=xyzabc123
{
    "query": {
        "match": {
            "title": "elasticsearch"
        }
    }
}
```

>`_only_local`首选项保证只在本地节点上使用分片副本，这有时对于故障排除很有用。所有其他选项都不能完全保证在搜索中使用任何特定的分片副本，对于一个变化的索引，这可能意味着重复的搜索可能会产生不同的结果，如果它们是在处于不同刷新状态的不同分片副本上执行的话。

> 不推荐使用`_primary`，`_primary_first`，`_replica`和`_replica_first`。 它们无助于避免由于使用具有不同刷新状态的分片而导致的不一致结果，并且Elasticsearch使用同步复制，因此主数据库通常不保存比其副本更新的数据。 如果无法搜索首选副本，则`_primary_first`和`_replica_first`首选项将以静默方式退回到非首选副本。 如果将副本提升为主副本，则`_primary`和`_replica`首选项将无提示地更改其首选分片，这可以随时发生。 `_primary`首选项还会给主分片带来不必要的额外负载。 这些选项与高速缓存相关的好处也可以使用`_only_nodes`，`_prefer_nodes`或自定义字符串值来获得。

## batched_reduce_size

应该在协调节点上进行聚合的分片结果的数量。如果请求中的分片数量过大，则将该值用作一种保护机制，以减少每个搜索请求的内存开销。

```
GET  /out-7.7.0-2020.10.29/_search?batched_reduce_size=10
```

## Source

`_source`字段包含索引时传递的原始JSON文档主体。`_source`字段本身没有索引(因此不能搜索)，但是存储它以便在执行fetch请求(如get或search)时返回。

设置为`false`禁用检索`_source`字段。还可以通过使用`_source_include`和`_source_exclude`来检索部分文档

```
GET  /out-7.7.0-2020.10.29/_search?_source=false
```

### 禁止_source字段

```
PUT tweets
{
  "mappings": {
    "_doc": {
      "_source": {
        "enabled": false
      }
    }
  }
}
```

不支持的特性：

- update、和reindex操作

- 从一个Elasticsearch索引重新索引到另一个，或者更改映射或分析，或者将索引升级到一个新的主要版本。

- 通过查看索引时使用的原始文档来调试查询或聚合的能力。

  > 如果需要考虑磁盘空间，应该增加压缩级别，而不是禁用_source。

### metrics用例数据

指标用例数据与其他基于时间或日志的数据不同，因为有许多仅由数字、日期或关键字组成的小文档。没有更新，没有高亮显示请求，数据过期很快，所以没有必要重新索引。搜索请求通常使用简单的查询按日期或标记过滤数据集，结果作为聚合返回。

在这种情况下，禁用`_source`字段将节省空间并减少I/O。建议在metrics情况下禁用_all字段。

### 从source中筛选字段

> 从source中删除字段与禁用source有类似的缺点，特别是不能从一个Elasticsearch重新索引文档到另一个Elasticsearch。考虑使用过滤。

```
PUT logs
{
  "mappings": {
    "_doc": {
      "_source": {
        "includes": [
          "*.count",
          "meta.*"
        ],
        "excludes": [
          "meta.description",
          "meta.other.*"
        ]
      }
    }
  }
}


PUT logs/_doc/1
{
  "requests": {
    "count": 10,
    "foo": "bar" 
  },
  "meta": {
    "name": "Some metric",
    "description": "Some metric description", 
    "other": {
      "foo": "one", 
      "baz": "two" 
    }
  }
}

GET logs/_search
{
  "query": {
    "match": {
      "meta.other.foo": "one" 
    }
  }
}
```

### 查询

允许控制如何每次命中返回`_source`字段。默认情况下，操作返回`_source`字段的内容，除非使用了`stored_fields`参数，或者`_source`字段被禁用。

禁用source字段

```
GET /_search
{
    "_source": false,
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```

筛选

```
GET /_search
{
    "_source": {
        "includes": [ "obj1.*", "obj2.*" ],
        "excludes": [ "*.description" ]
    },
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```

## Store

### stored_fields

每次命中要返回的文档的可选存储字段，以逗号分隔。不指定任何值将不会导致返回任何字段。

```
GET  /out-7.7.0-2020.10.29/_search?stored_fields=message
```

### 映射

默认情况下，字段值被索引以使其可搜索，但不存储它们。这意味着可以查询字段，但不能检索原始字段值。

字段值已经是`_source`字段的一部分，该字段默认存储。如果只想检索单个字段或几个字段的值，而不是整个`_source`，那么可以通过source过滤实现这一点。

在某些情况下，存储字段是有意义的。例如，如果有一个有标题的文档，一个日期，和一个非常大的内容字段，可能想要检索仅仅标题和日期，而不必从一个大_source字段提取这些字段:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "title": {
          "type": "text",
          "store": true 
        },
        "date": {
          "type": "date",
          "store": true 
        },
        "content": {
          "type": "text"
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "title":   "Some short title",
  "date":    "2015-01-01",
  "content": "A very long content field..."
}

GET my_index/_search
{
  "stored_fields": [ "title", "date" ] 
}
```

> 为了保持一致性，存储的字段总是作为数组返回，因为无法知道原始字段值是单个值、多个值还是一个空数组。
>
> 如果需要原始值，则应该从_source字段检索它。

对于那些没有出现在_source字段中的字段(例如copy_to字段)，存储字段是有意义的。

### 查询

stored_fields参数是关于显式标记为存储在映射中的字段的，默认情况下是关闭的，通常不推荐使用。使用source筛选来选择要返回的原始文档的子集。

允许有选择地为搜索命中的每个文档加载特定的存储字段。

```
GET /_search
{
    "stored_fields" : ["user", "postDate"],
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
*可用于从文档中加载所有存储字段。
```

空数组只会导致每次命中返回`_id`和`_type`

```
GET /_search
{
    "stored_fields" : [],
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```

如果请求的字段没有被存储(存储映射设置为false)，它们将被忽略。从文档本身获取的存储字段值总是作为数组返回。相反，像`_routing`这样的元数据字段不会作为数组返回。此外，只能通过field选项返回叶字段。因此不能返回对象字段，这样的请求将失败。

禁用存储字段(和元数据字段)

```
GET /_search
{
    "stored_fields": "_none_",
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
如果使用_none_，则不能激活_source和版本参数。
```

## track_scores

当排序时，设置为“true”，以便仍然跟踪分数，并将他们作为每一次命中的一部分返回。

```
GET  /out-7.7.0-2020.10.29/_search?sort=log.offset&track_scores=true
```

## track_total_hits

  设置为“false”，以禁用跟踪匹配查询的总命中数。默认值为true。

```
GET  /out-7.7.0-2020.10.29/_search?track_total_hits=true
```

## timeout

```
GET  /book_publisher/_search?&timeout=5s
```

## from/size

```
GET  /book_publisher/_search?from=0&size=1
```

## allow_partial_search_results

默认值为true，这将允许在超时或部分失败的情况下产生部分结果。可以使用集群级别设置`search.default_allow_partial_results`来控制这个默认值。

```
GET  /out-7.7.0-2020.10.29/_search?&allow_partial_search_results=true
```

## min_score

 排除`_score`小于min_score中指定的最小值的文档:

```
GET /_search
{
    "min_score": 0.5,
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```

注意，大多数时候，这没有太大意义，只是提供给高级用例。
