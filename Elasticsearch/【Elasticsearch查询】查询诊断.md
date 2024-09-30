## Profile (概要)

> Profile API是一种调试工具，开启时消耗搜索性能。

Profile API提供了关于搜索请求中各个组件执行的详细时间信息。让用户了解搜索请求是如何在较低的层次上执行的，这样用户就可以理解为什么某些请求很慢，并采取措施改进它们。

请注意，该API并不度量网络延迟、搜索获取阶段所花费的时间、请求在队列中花费的时间或在协调节点上合并分片响应时所花费的时间。

Profile API的输出非常冗长，特别是对于跨多个切分执行的复杂请求。建议使用pretty打印响应，以帮助理解输出。



### 使用

```
GET /test_after/_search?human
{
  "profile": true,
  "query" : {
    "match" : { "message" : "some number" }
  }
}
```



### 响应总体结构

```
{
   "profile": {
        "shards": [
           {
              "id": "[2aE02wS1R8q_QFnYu6vDVQ][twitter][0]",   //为参与响应的每个分片返回一个配置文件，并由惟一的ID标识
              "searches": [
                 {
                    "query": [...],   //有关查询执行的详细信息        
                    "rewrite_time": 51443,      //表示累计重写的时间,显示重写查询花费的总时间(以纳秒为单位)。
                    "collector": [...]     //关于运行搜索的Lucene收集器     
                 }
              ],
              "aggregations": [...]    //包含关于聚合执行的详细信息         
           }
        ]
     }
}
```



### 查询概要

Profile API提供的详细信息直接公开了Lucene类名和概念，这意味着对结果的完整解释需要相当高级的Lucene知识。这个页面试图提供一个关于Lucene如何执行查询的概要流程，这样就可以使用Profile API成功地诊断和调试查询。

> 要获得完整的理解，请参考Lucene的文档和代码。

话虽如此，修复缓慢的查询通常不需要完全理解。通常，只要看到查询的某个特定组件很慢就足够了，而不必理解为什么为什么查询慢。



### query部分

查询树

match query示例

```
"query": [
    {
       "type": "BooleanQuery",  // Lucene类名，通常与Elasticsearch名称一致
       "description": "message:some message:number", //查询的Lucene解释文本,并且可用来帮助区分查询的各个部分
       "time_in_nanos": "1873811", //显示执行整个BooleanQuery花费了~1.8ms，包含子查询的时间
       "breakdown": {...},         //提供关于时间是如何花费的详细统计信息       
       "children": [   //子查询详细过程
          {
             "type": "TermQuery",
             "description": "message:some",
             "time_in_nanos": "391943",
             "breakdown": {...}
          },
          {
             "type": "TermQuery",
             "description": "message:number",
             "time_in_nanos": "210682",
             "breakdown": {...}
          }
       ]
    }
]
```

breakdown

breakdown列出了Lucene底层执行的详细时间统计信息（所有时间为纳秒时间）:

```
"breakdown": {
   "score": 51306,
   "score_count": 4,
   "build_scorer": 2935582,
   "build_scorer_count": 1,
   "match": 0,
   "match_count": 0,
   "create_weight": 919297,
   "create_weight_count": 1,
   "next_doc": 53876,
   "next_doc_count": 5,
   "advance": 0,
   "advance_count": 0
}
```

create_weight：Lucene中的查询必须能够跨多个IndexSearchers (可以把它看作是针对特定的Lucene索引执行搜索的引擎)。这将Lucene置于一个棘手的位置，因为许多查询需要积累与索引相关的临时状态/统计信息，但是查询契约要求它必须是不可变的。为了解决这个问题，Lucene要求每个查询生成一个权重对象，作为一个临时上下文对象来保存与这个特定(IndexSearcher, query)元组关联的状态。weight度量显示了这个过程需要多长时间

build_scorer：此参数显示为查询构建Scorer 所需的时间。Scorer 是在匹配文档上迭代生成每个文档得分的机制(例如，“foo”匹配文档的效果如何?)注意，这记录了生成Scorer对象所需的时间，而不是实际为文档打分。有些查询对Scorer的初始化更快或更慢，这取决于优化程度、复杂性等。

next_doc：Lucene方法next_doc返回与查询匹配的下一个文档的Doc ID。这个统计数据显示了确定哪个文档是下一个匹配所需的时间，这个过程根据查询的性质有很大的不同。Next_doc是advance()的一种特殊形式，它对Lucene中的许多查询更加方便。相当于advance(docId() + 1)

advance：advance是next_doc的低版本信息:它的目的与查找下一个匹配的doc相同，但要求调用查询执行额外的任务，例如识别和略过以前跳过的部分，等等。但是，并不是所有查询都可以使用next_doc，所以对于这些查询，advance也是计时的。

matches：有些查询(例如短语查询)使用“两阶段”过程匹配文档。首先，文档是“近似”匹配的，如果它近似匹配，则使用更严格(也更昂贵)的过程进行第二次检查。第二阶段验证是matches的统计度量。例如，短语查询首先通过确保短语中的所有term都出现在文档中来大致检查文档。如果所有term都存在，则执行第二阶段验证，以确保term是为了形成短语，这比仅仅检查term是否存在要昂贵得多。因为这个两阶段过程只被少数查询使用，所以度量统计信息通常为零

score：它记录了通过某个特定文档的scorer为该文档计算得分所花费的时间

*_count：记录特定方法的调用次数



### collector 部分

响应的collector 部分显示高级执行细节。Lucene通过定义一个“collector ”来工作，它负责协调匹配文档的遍历、评分和收集。collector 也是单个查询记录聚合结果、执行未限定作用域的“全局”查询、执行查询后过滤器等的方式。

```
"collector": [
   {
      "name": "CancellableCollector",
      "reason": "search_cancelled",
      "time_in_nanos": "304311",
      "children": [
        {
          "name": "SimpleTopScoreDocCollector",
          "reason": "search_top_hits",
          "time_in_nanos": "32273"
        }
      ]
   }
]
```



### rewrite 部分

Lucene中的所有查询都要经历一个“重写”过程。一个查询(及其子查询)可能会被重写一次或多次，这个过程将持续下去，直到查询停止。这个过程允许Lucene执行优化，比如删除冗余子句，替换一个查询以获得更高效的执行路径，等等。例如，Boolean→Boolean→TermQuery可以被重写为TermQuery，因为在这种情况下，所有的布尔值都是不必要的。

重写过程非常复杂，很难显示，因为查询可能会发生巨大的变化。不显示中间结果，而是简单地将rewrite 总时间显示为一个值(以纳秒为单位)。这个值是累积的，包含rewrite所有查询的总时间。



### 注意事项

开启概要文件需要巨大的开销，因此不建议经常开启，毕竟它只是一个诊断工具。并且在有些禁止优化的特殊Lucene查询中，会消耗更多的时间。



### 限制

- 不测量搜索fetch阶段或网络开销
- 不考虑花费在队列、合并协调节点上的分片响应或其他工作上的时间，比如构建全局序号(用于加速搜索的内部数据结构)
- 对于建议、高亮显示、dfs_query_then_fetch，目前没有可用的分析统计信息
- 聚合的reduce阶段目前不可用



# Validate 

Validate允许用户验证一个可能很昂贵的查询，而无需执行它。

使用样例

```
PUT twitter/_doc/_bulk?refresh
{"index":{"_id":1}}
{"user" : "kimchy", "post_date" : "2009-11-15T14:12:12", "message" : "trying out Elasticsearch"}
{"index":{"_id":2}}
{"user" : "kimchi", "post_date" : "2009-11-15T14:12:13", "message" : "My username is similar to @kimchy!"}

GET twitter/_validate/query?q=user:foo
```

支持通用参数

```
df	analyzer	default_operator	lenient		analyze_wildcard
```



## 条件查询

```
GET twitter/_doc/_validate/query
{
  "query" : {
    "bool" : {
      "must" : {
        "query_string" : {
          "query" : "*:*"
        }
      },
      "filter" : {
        "term" : { "user" : "kimchy" }
      }
    }
  }
}
```



## 无效查询

如果查询无效，valid将为false。这里的查询是无效的，因为Elasticsearch知道post_date字段应该是一个日期而由于动态映射，foo没有正确解析成一个日期:

```
GET twitter/_doc/_validate/query
{
  "query": {
    "query_string": {
      "query": "post_date:foo",
      "lenient": false
    }
  }
}
```

```
{"valid":false,"_shards":{"total":1,"successful":1,"failed":0}}
```



## 原因解释

```
GET twitter/_doc/_validate/query?explain=true
{
  "query": {
    "query_string": {
      "query": "post_date:foo",
      "lenient": false
    }
  }
}
```

当查询有效时，解释默认为该查询的字符串表示。当rewrite设置为true时，解释会更详细地显示将要执行的实际Lucene查询。

```
GET twitter/_doc/_validate/query?rewrite=true
{
  "query": {
    "more_like_this": {
      "like": {
        "_id": "2"
      },
      "boost_terms": 1
    }
  }
}
```

默认情况下，请求仅在随机选择的单个分片上执行。查询的详细解释可能取决于被查询的是哪个shard，因此可能因请求的不同而有所不同。因此，在查询重写的情况下，应该使用all_shards参数从所有可用的分片获得响应。

```
GET twitter/_doc/_validate/query?rewrite=true&all_shards=true
{
  "query": {
    "match": {
      "user": {
        "query": "kimchy",
        "fuzziness": "auto"
      }
    }
  }
}
```



# 慢日志

慢日志可将搜索慢或者写入慢的日志输出到日志文件中，以便后续的分析。

## 默认配置

查看索引慢日志默认配置，默认是关闭的

```
GET /test/_settings?include_defaults&filter_path=test.defaults.index.search,test.defaults.index.indexing

curl -XGET "http://node02:9200/test/_settings?include_defaults&filter_path=test.defaults.index.search,test.defaults.index.indexing"
```



## 搜索慢日志

分段级慢速搜索日志允许将慢速搜索(查询和获取阶段)记录到一个专用的日志文件中。

可以为执行的查询阶段和获取阶段设置阈值，下面是一个示例:

```
index.search.slowlog.threshold.query.warn: 10s
index.search.slowlog.threshold.query.info: 5s
index.search.slowlog.threshold.query.debug: 2s
index.search.slowlog.threshold.query.trace: 500ms

index.search.slowlog.threshold.fetch.warn: 1s
index.search.slowlog.threshold.fetch.info: 800ms
index.search.slowlog.threshold.fetch.debug: 500ms
index.search.slowlog.threshold.fetch.trace: 200ms

index.search.slowlog.level: info
```

以上所有设置都是动态的，并且是按索引设置的。

```
PUT /logstach-*-2020-10-20/_settings
{
  "index.search.slowlog.threshold.query.warn": "10s", #超过10秒的query产生1个warn日志
  "index.search.slowlog.threshold.query.info": "5s",
  "index.search.slowlog.threshold.query.debug": "2s",  
  "index.search.slowlog.threshold.query.trace": "500ms",
  
  "index.search.slowlog.threshold.fetch.warn": "1s",
  "index.search.slowlog.threshold.fetch.info": "800ms",
  "index.search.slowlog.threshold.fetch.debug": "500ms",
  "index.search.slowlog.threshold.fetch.trace": "200ms",
  "index.search.slowlog.level": "info"
 }
 
curl -XPUT "http://node02:9200/logstach-*-2020-10-20/_settings" -H 'Content-Type: application/json' -d'
{
  "index.search.slowlog.threshold.query.warn": "10s",
  "index.search.slowlog.threshold.query.info": "5s",
  "index.search.slowlog.threshold.query.debug": "2s",
  "index.search.slowlog.threshold.query.trace": "500ms",
  "index.search.slowlog.threshold.fetch.warn": "1s",
  "index.search.slowlog.threshold.fetch.info": "800ms",
  "index.search.slowlog.threshold.fetch.debug": "500ms",
  "index.search.slowlog.threshold.fetch.trace": "200ms",
  "index.search.slowlog.level": "info"
}'
```

默认情况下，没有启用(设置为-1)。级别(warn, info, debug, trace)允许控制记录日志的日志级别。并不是所有的都需要配置(例如，只能设置warn阈值)。多个级别的好处是能够在违反特定阈值时快速“grep”。

日志记录是在分片级别范围内完成的，这意味着在特定分片内执行搜索请求。它不包含整个搜索请求，它可以广播到几个分片来执行。与请求级别相比，分片级日志记录的一些好处是与特定机器上的实际执行相关联。

默认情况下使用以下配置配置日志文件(在`log4j2.properties`中):

```
appender.index_search_slowlog_rolling.type = RollingFile
appender.index_search_slowlog_rolling.name = index_search_slowlog_rolling
appender.index_search_slowlog_rolling.fileName = ${sys:es.logs}_index_search_slowlog.log
appender.index_search_slowlog_rolling.layout.type = PatternLayout
appender.index_search_slowlog_rolling.layout.pattern = [%d{ISO8601}][%-5p][%-25c] [%node_name]%marker %.10000m%n
appender.index_search_slowlog_rolling.filePattern = ${sys:es.logs}_index_search_slowlog-%d{yyyy-MM-dd}.log
appender.index_search_slowlog_rolling.policies.type = Policies
appender.index_search_slowlog_rolling.policies.time.type = TimeBasedTriggeringPolicy
appender.index_search_slowlog_rolling.policies.time.interval = 1
appender.index_search_slowlog_rolling.policies.time.modulate = true

logger.index_search_slowlog_rolling.name = index.search.slowlog
logger.index_search_slowlog_rolling.level = trace
logger.index_search_slowlog_rolling.appenderRef.index_search_slowlog_rolling.ref = index_search_slowlog_rolling
logger.index_search_slowlog_rolling.additivity = false
```



## 索引慢日志

索引慢日志，在功能上类似于搜索慢日志。日志文件名以`_index_indexing_slowlog.log`结尾。日志和阈值的配置方式与搜索慢日志相同。index slowlog示例:

```
index.indexing.slowlog.threshold.index.warn: 10s
index.indexing.slowlog.threshold.index.info: 5s
index.indexing.slowlog.threshold.index.debug: 2s
index.indexing.slowlog.threshold.index.trace: 500ms
index.indexing.slowlog.level: info
index.indexing.slowlog.source: 1000
```

以上所有设置都是动态的，并且是按索引设置的。

```
PUT /<index_name>/_settings
{
  "index.indexing.slowlog.threshold.index.debug": "2s",
  "index.indexing.slowlog.threshold.index.info": "5s",
  "index.indexing.slowlog.threshold.index.trace": "500ms",
  "index.indexing.slowlog.threshold.index.warn": "10s",
  "index.indexing.slowlog.level": "info",
  "index.indexing.slowlog.source": "1000"
}


curl -XPUT "http://node02:9200/<index_name>/_settings" -H 'Content-Type: application/json' -d'
{
  "index.indexing.slowlog.threshold.index.debug": "2s",
  "index.indexing.slowlog.threshold.index.info": "5s",
  "index.indexing.slowlog.threshold.index.trace": "500ms",
  "index.indexing.slowlog.threshold.index.warn": "10s",
  "index.indexing.slowlog.level": "info",
  "index.indexing.slowlog.source": "1000"
}'
```

默认情况下，Elasticsearch将在slowlog中记录`_source`的前1000个字符。可以用`index.indexing.slowlog.source`来改变。将其设置为`false`或`0`将跳过对整个源的日志记录，而将其设置为`true`将记录整个源的日志，无论大小如何。默认情况下，将重新格式化原始`_source`，以确保它适合单个日志行。

如果保存原始文档格式很重要，可以通过设置`index.indexing.slowlog.reformat`来关闭重新格式化。重新格式化为false，这将导致源被“按原样”记录，并且可能跨越多个日志行。

```
index.indexing.slowlog.source:true    默认记录source的前1000个字符，设置为true，对source进行原样记录，无论大小
index.indexing.slowlog.reformat：true  默认为true，即对原始的文档进行格式化，如需保留原文档格式，设置为false
```

默认情况下，log4j2中配置了索引慢速日志文件。属性文件:

```
appender.index_indexing_slowlog_rolling.type = RollingFile
appender.index_indexing_slowlog_rolling.name = index_indexing_slowlog_rolling
appender.index_indexing_slowlog_rolling.fileName = ${sys:es.logs}_index_indexing_slowlog.log
appender.index_indexing_slowlog_rolling.layout.type = PatternLayout
appender.index_indexing_slowlog_rolling.layout.pattern = [%d{ISO8601}][%-5p][%-25c] [%node_name]%marker %.-10000m%n
appender.index_indexing_slowlog_rolling.filePattern = ${sys:es.logs}_index_indexing_slowlog-%d{yyyy-MM-dd}.log
appender.index_indexing_slowlog_rolling.policies.type = Policies
appender.index_indexing_slowlog_rolling.policies.time.type = TimeBasedTriggeringPolicy
appender.index_indexing_slowlog_rolling.policies.time.interval = 1
appender.index_indexing_slowlog_rolling.policies.time.modulate = true

logger.index_indexing_slowlog.name = index.indexing.slowlog.index
logger.index_indexing_slowlog.level = trace
logger.index_indexing_slowlog.appenderRef.index_indexing_slowlog_rolling.ref = index_indexing_slowlog_rolling
logger.index_indexing_slowlog.additivity = false
```



## 慢日志配置

按索引进行配置，只对本机器的分片有效

```
PUT /_all/_settings   //设置全部索引
{

//慢搜索
  "index.search.slowlog.threshold.query.warn": "10s", #超过10秒的query产生1个warn日志
  "index.search.slowlog.threshold.query.info": "5s",
  "index.search.slowlog.threshold.query.debug": "2s",  
  "index.search.slowlog.threshold.query.trace": "500ms",
  
  "index.search.slowlog.threshold.fetch.warn": "1s",
  "index.search.slowlog.threshold.fetch.info": "800ms",
  "index.search.slowlog.threshold.fetch.debug": "500ms",
  "index.search.slowlog.threshold.fetch.trace": "200ms",
  "index.search.slowlog.level": "info",
  
 //慢写入
  "index.indexing.slowlog.threshold.index.debug": "2s",
  "index.indexing.slowlog.threshold.index.info": "5s",
  "index.indexing.slowlog.threshold.index.trace": "500ms",
  "index.indexing.slowlog.threshold.index.warn": "10s",

  "index.indexing.slowlog.level": "info",
  "index.indexing.slowlog.source": "1000"

}
```



## 集群日志

设置集群日志输出级别（未设置阈值则无效）

```
PUT /_cluster/settings
{
  "transient": {
    "logger.index.search.slowlog": "DEBUG",
    "logger.index.indexing.slowlog": "WARN"
  }
}
```



## 关闭慢日志

将值设置为-1即可

```
PUT /<index_name>/_settings
{
  "index.search.slowlog.threshold.query.warn": "-1", 
  "index.search.slowlog.threshold.query.info": "-1",
  "index.search.slowlog.threshold.query.debug": "-1",  
  "index.search.slowlog.threshold.query.trace": "-1",
  
  "index.search.slowlog.threshold.fetch.warn": "-1",
  "index.search.slowlog.threshold.fetch.info": "-1",
  "index.search.slowlog.threshold.fetch.debug": "-1",
  "index.search.slowlog.threshold.fetch.trace": "-1",
  "index.search.slowlog.level": "info"
 }
 
curl -XPUT "http://node02:9200/<index_name>/_settings" -H 'Content-Type: application/json' -d'
{
  "index.search.slowlog.threshold.query.warn": "-1",
  "index.search.slowlog.threshold.query.info": "-1",
  "index.search.slowlog.threshold.query.debug": "-1",
  "index.search.slowlog.threshold.query.trace": "-1",
  "index.search.slowlog.threshold.fetch.warn": "-1",
  "index.search.slowlog.threshold.fetch.info": "-1",
  "index.search.slowlog.threshold.fetch.debug": "-1",
  "index.search.slowlog.threshold.fetch.trace": "-1",
  "index.search.slowlog.level": "info"
}'
```



## 查询验证

`Elasticsearch`根目录下的`<ES_NAME>_index_indexing_slowlog.log`为索引写入慢的日志，`<ES_NAME>__index_search_slowlog.log`为查询慢的日志

构建一个查询

```

GET /es01-7.7.0-2020.09.21/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "bool": {
            "must": [
              {
                "term": {
                  "host.name": "localhost.localdomain"
                }
              },
              {
                "term": {
                  "agent.version": "7.7.0"
                }
              }
            ]
          }
        },
        {
          "range": {
            "@timestamp": {
              "gte": "2020-09-21T03:17:44.728Z",
              "lte": "2020-09-21T23:18:44.728Z"
            }
          }
        }
      ]
    }
  },
  "from": 100,
  "size": 20,
  "sort": [
    {
      "@timestamp": {
        "order": "desc"
      }
    }
  ]
}
```

可以将info级别的时间设置小一点，以便于观察是否有日志输出，如有日志输出，则配置成功。



## 日志解读

日志示例：

```
[2020-10-19T16:19:43,725][INFO ][index.search.slowlog.query] [node02] [es01-7.7.0-2020.09.21][3] took[5.8s], took_millis[5842], total_hits[28260241], types[], stats[], search_type[QUERY_THEN_FETCH], total_shards[5], source[{"from":100,"size":20,"query":{"bool":{"must":[{"bool":{"must":[{"term":{"host.name":{"value":"localhost.localdomain","boost":1.0}}},{"term":{"agent.version":{"value":"7.7.0","boost":1.0}}}],"adjust_pure_negative":true,"boost":1.0}},{"range":{"@timestamp":{"from":null,"to":null,"include_lower":true,"include_upper":true,"boost":1.0}}}],"adjust_pure_negative":true,"boost":1.0}},"sort":[{"@timestamp":{"order":"desc"}}]}],

```

Slowlog 日志拆解:

| 日志拆分项                    | 描述                           |
| ----------------------------- | ------------------------------ |
| [2020-10-19T16:19:43,725]     | 检索时间                       |
| [INFO ]                       | 日志级别                       |
| [index.search.slowlog.query]  | 属于search的query阶段慢日志    |
| [node02]                      | 节点名称                       |
| [es01-7.7.0-2020.09.21]       | 索引名称                       |
| [3]                           | query执行的分片序号            |
| took[5.8s]                    | 分片3的查询事假。              |
| took_millis[5842]             | 耗费时间（毫秒）               |
| total_hits[28260241]          | 命中数                         |
| search_type[QUERY_THEN_FETCH] | search类型（query_then_fetch） |
| total_shards[5]               | 索引的总分片大小               |
| source[]                      | 执行检索的请求body体           |



## 注意事项

1、慢日志设置根据索引设置，如需设置多个索引，可根据通配符进行匹配

2、该设置为永久设置，集群重启依然有效

3、节点上的慢日志只记录当前节点上分片的查询速率