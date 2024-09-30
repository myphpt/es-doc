# 深度查询

## from/to

运行Search进行查询时，可以使用from和size参数对结果进行分页。

- from参数定义了要获取的第一个结果的偏移量。
- size参数表示允许返回的最大命中次数，即返回的条数。



1、作为请求参数

```
GET /_search?from=0&size=10
{
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```

2、在请求体中设置

```
GET /_search
{
    "from" : 0, "size" : 10,
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```

from默认值为0，size为10。

> 注意from + size不能大于index.max_result_window索引设置，默认值为10,000。

## Scroll

 虽然搜索请求一般返回单个“页面”的结果，但滚动查询可以用于从单个搜索请求检索大量结果(甚至所有结果)，其方式与在传统数据库上使用游标非常相似。

滚动查询不是为了满足实时的用户请求，而是为了处理大量的数据，例如，为了将一个索引的内容重新索引到一个具有不同配置的新索引中。

> 滚动请求返回的结果反映了发出初始搜索请求时索引的状态，比如实时快照。对文档的后续更改(索引、更新或删除)只会影响以后的搜索请求。



### 如何查询

为了使用滚动查询，初始搜索请求应该在查询字符串中指定滚动参数，它告诉Elasticsearch它应该保持“搜索上下文”环境活跃多久(参见保持搜索上下文活跃)，例如?scroll=1m。

```
POST /twitter/_search?scroll=1m
{
    "size": 100,
    "query": {
        "match" : {
            "title" : "elasticsearch"
        }
    }
}
```

上述请求的结果包括一个_scroll_id，它应该被传递给滚动查询，以便检索下一批结果。

```
POST /_search/scroll  //可以使用GET或POST, URL不应该包含索引名——这是在原始搜索请求中指定的。
{
    "scroll" : "1m",  //滚动参数告诉Elasticsearch将搜索上下文再打开1m。
    "scroll_id" : "DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAAD4WYm9laVYtZndUQlNsdDcwakFMNjU1QQ==" 
}
```

size参数允许您配置每批结果返回的最大命中次数。每次调用滚动API返回下一批结果，直到没有更多的结果留下返回，即hits数组是空的。



### 重要笔记

1. 初始搜索请求和随后的每个滚动请求都返回一个`_scroll_id`。虽然`_scroll_id`可以在请求之间更改，但它并不应该总是更改——在任何情况下，只应该使用最近接收到的`_scroll_id`。

2. 如果请求指定aggregations，则只有初始搜索响应中包含aggregations结果。

3. 当排序顺序为_doc时，滚动请求的优化可以使它们更快。如果您想遍历所有文档而不考虑顺序，这是最有效的选项:

   ```
   GET /_search?scroll=1m
   {
     "sort": [
       "_doc"
     ]
   }
   ```



### 保持搜索上下文环境存活

滚动参数(传递给搜索请求和每个滚动请求)告诉Elasticsearch它应该保持搜索上下文存活多长时间。它的值(例如1m)不需要足够长来处理所有数据——它只需要足够长的时间来处理前一批结果。

每个滚动请求(带滚动参数)设置一个新的到期时间。如果滚动请求没有传递滚动参数，那么搜索上下文将作为滚动请求的一部分被释放。

通常，后台合并过程通过合并较小的段来优化索引，以创建新的较大的段，同时删除较小的段。这个过程在滚动期间继续进行，但是一个开放的搜索上下文环境可以防止旧的段在仍在使用时被删除。这就是为什么Elasticsearch能够返回初始搜索请求的结果，而不考虑随后对文档的更改的原因。

> 保持较旧的段处于活动状态意味着需要更多的文件句柄。确保已将节点配置为具有足够的空闲文件句柄。

查看节点有多少的搜索上下文环境是开放的：

```
GET /_nodes/stats/indices/search?human


响应：
"scroll_total" : 75,
"scroll_time" : "1.6h",
"scroll_time_in_millis" : 5868591,
"scroll_current" : 0,    //当前的滚动查询
```



### 手动清除

当滚动超时时，搜索上下文将自动删除。然而，保持滚动打开是有代价的，正如前面所讨论的，一旦滚动不再被使用，使用clear-scroll API应该明确地清除滚动:

```
DELETE /_search/scroll
{
    "scroll_id" : "DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAAD4WYm9laVYtZndUQlNsdDcwakFMNjU1QQ=="
}
```

多个滚动id可以作为数组传递:

```
DELETE /_search/scroll
{
    "scroll_id" : [
   "DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAAD4WYm9laVYtZndUQlNsdDcwakFMNjU1QQ==","DnF1ZXJ5VGhlbkZldGNoBQAAAAAAAAABFmtSWWRRWUJrU2o2ZExpSGJCVmQxYUEAAAAAAAAAAxZrU"
    ]
}
```

可以使用_all参数清除所有搜索上下文:

```
DELETE /_search/scroll/_all
```

scroll_id还可以作为查询字符串参数或在请求主体中传递。多个滚动id可以作为逗号分隔值传递:

```
DELETE /_search/scroll/DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAAD4WYm9laVYtZndUQlNsdDcwakFMNjU1QQ==,DnF1ZXJ5VGhlbkZldGNoBQAAAAAAAAABFmtSWWRRWUJrU2o2ZExpSGJCVmQxYUEAA
```



### 切片

对于返回大量文档的滚动查询，可以将该滚动分割成多个切片，并且每个切片可以独立消费：

```
GET /twitter/_search?scroll=1m
{
    "slice": {
        "id": 0, 
        "max": 2 
    },
    "query": {
        "match" : {
            "title" : "elasticsearch"
        }
    }
}

GET /twitter/_search?scroll=1m
{
    "slice": {
        "id": 1,
        "max": 2
    },
    "query": {
        "match" : {
            "title" : "elasticsearch"
        }
    }
}
```

第一个请求的结果返回了属于第一个分片（id：0）的文档，第二个请求的结果返回了属于第二个分片的文档。 由于切片的最大数量设置为2，所以两个请求的结果的并集等效于不切片的滚动查询的结果。

 默认情况下，拆分首先在分片上进行，然后使用uid字段在每个分片上进行本地拆分，其公式如下：`slice(doc) = floorMod(hashCode(doc._uid), max)`。例如，如果分片数为2而用户请求4个切片，则将切片0和2分配给第一个分片，并将切片1和3分配给第二个分片。

每个滚动都是独立的，可以像任何滚动查询一样并行处理。

如果切片的数量大于分片的数量，切片过滤器在第一次调用时非常慢，它的复杂度为O(N)，内存消耗等于每切片N位，其中N是切片中的文档总数。在几个调用之后，应该缓存过滤器，随后的调用应该更快，但是您应该限制并行执行的切片查询的数量，以避免内存爆炸。

为了完全避免这种开销，可以使用另一个字段的doc_values来做切片，但用户必须确保该字段具有以下属性:

- 字段是数字的。
- doc_values在该字段上启用
- 每个文档都应该包含一个值。如果文档中指定的字段有多个值，则使用第一个值。
- 每个文档的值应该在创建文档且不更新时设置一次。这确保了每个片都得到确定性的结果。
- 该字段的基数应该很高。这确保了每个切片获得大致相同数量的文档。

```
GET /twitter/_search?scroll=1m
{
    "slice": {
        "field": "date",
        "id": 0,
        "max": 10
    },
    "query": {
        "match" : {
            "title" : "elasticsearch"
        }
    }
}
```

对于仅追加基于时间的索引，可以安全地使用时间戳字段。

> 默认情况下，每次滚动允许的最大切片数限制为1024。您可以更新index.max_slices_per_scroll索引设置绕过此限制。



## Search After

 可以通过使用from和size来对结果进行分页，但是当达到深度分页时，成本就变得过高了。 `index.max_result_window`默认值为10,000是一个保障，搜索请求占用堆内存和时间与from +size成比例。

建议使用scroll查询进行有效的深度滚动，但是滚动上下文开销很大，不建议将其用于实时用户请求。search_after参数提供了一个活动游标，从而绕过了这个问题。其思想是使用来自前一页的结果来帮助检索下一页。

### 排序

1. 应将每个文档中的具有唯一值的字段作为排序依据， 否则，具有相同排序值的文档的排序顺序将不确定，并可能导致结果丢失或重复。
2. id字段在每个文档中都有唯一的值，但是不建议直接将其用作排序。
3. 请注意search_after会寻找第一个完全或部分与排序字段提供的值相匹配的文档。 因此，如果文档的排序字段值是“ 654323”，而在search_after中搜索“ 654”，则该文档仍将匹配并返回在此文档之后找到的结果。 
4. 在此字段上禁用`doc_values`（默认启用），则对其进行排序时需要在内存中加载大量数据。 建议在另一个启用了`doc_values`的字段中（客户端侧或使用摄取节点的提取器）复制id字段的内容，并使用此新字段作为排序的最终字段。



### 查询

```
GET twitter/_search
{
    "size": 10,
    "query": {
        "match" : {
            "title" : "elasticsearch"
        }
    },
    "sort": [
        {"date": "asc"},
        {"tie_breaker_id": "asc"}      
    ]
}

启用doc_values的_id字段副本
```

上述请求的结果包括每个文档的排序值数组。这些排序值与search_after参数一起使用，并返回“after”之后的结果集。例如，我们可以使用上一个文档的排序值，并将其传递给search_after来检索下一页的结果:

```
GET twitter/_search
{
    "size": 10,
    "query": {
        "match" : {
            "title" : "elasticsearch"
        }
    },
    "search_after": [1463538857, "654323"],
    "sort": [
        {"date": "asc"},
        {"tie_breaker_id": "asc"}
    ]
}
```



### 注意

使用search_after时，from的参数必须设置为0(或-1)。

search_after不是一个自由跳转到随机页面的解决方案，而是并行的滚动许多查询。它与滚动查询非常相似，但与之不同的是，search_after参数是无状态的，它总是根据最新版本的searcher进行解析。因此，在遍历过程中，排序顺序可能会根据索引的更新和删除而改变。



### Demo

```
POST /test_after/_doc/_bulk
{"index":{"_id":1}}
{"title":"ElasticSearch","collectTime":1}
{"index":{"_id":2}}
{"title":"logstach","collectTime":2}
{"index":{"_id":3}}
{"title":"Kibana","collectTime":3}
{"index":{"_id":4}}
{"title":"Beats","collectTime":4}


GET test_after/_search
{
  "size": 2,
  "query": {
    "match_all": {}
  },
  "sort": [
    {
      "collectTime": "asc"
    }
  ]
}

GET test_after/_search
{
    "size": 2,
    "query": {
         "match_all": {}
    },
    "search_after": [2],
    "sort": [
        {"collectTime": "asc"}
    ]
}
```

