# Create Index

创建一个默认设置的索引

```
PUT twitter
```



索引命名规则：

- 小写字母
- 不能包含`\,/,*,?,",<,>,|,空格,#`
- 在7.0之前的索引可以包含冒号`:`，但是这已经被废弃，并且在7.0+中不受支持
- 不能以`-，_，+`开头
- 不能超过255字节(注意是字节)

索引设置

```
PUT twitter
{
    "settings" : {
        "index" : {
            "number_of_shards" : 3,     //默认为5
            "number_of_replicas" : 2     //默认为1
        }
    }
}

//简单写法
PUT twitter
{
    "settings" : {
        "number_of_shards" : 3,
        "number_of_replicas" : 2
    }
}
```

索引映射

```
PUT test
{
    "settings" : {
        "number_of_shards" : 1
    },
    "mappings" : {
        "_doc" : {
            "properties" : {
                "field1" : { "type" : "text" }
            }
        }
    }
}
```

别名

```
PUT test
{
    "aliases" : {
        "alias_1" : {},
        "alias_2" : {
            "filter" : {
                "term" : {"user" : "kimchy" }
            },
            "routing" : "kimchy"
        }
    }
}
```



等待活跃分片

默认情况下，索引创建将只在每个分片的主副本已经启动或请求超时时向客户机返回响应。索引创建响应将表明发生了什么:

```
{
    "acknowledged": true,
    "shards_acknowledged": true,
    "index": "test"
}
```

* acknowledge表示索引是否在集群中成功创建

* shards_acknowledged表示在超时之前是否为索引中的每个分片启动了所需数量的分片副本。

  > 注意，仍然可能acknowledged或shards_acknowledged为false，但是索引创建成功了。这些值仅表示操作是否在超时之前完成。

如果 `acknowledged`为`false`，则在使用新创建的索引更新集群状态之前会超时，但是可能很快就会创建。

如果`shards_acknowledged` 是`false`，那么即使群集状态已成功更新以反映新创建的索引（即`acknowledged=true`），也会在启动所需数量的分片（默认情况下仅是主分片）之前超时。

我们可以通过设置`index.write.wait_for_active_shards`更改默认值，即只等待主分片开始。(注意，更改此设置还会影响所有后续写操作中的wait_for_active_shards值):

```
//默认值为1，即主分片写入数据后立即返回，最大值为副本数+1，前提是副本分片可分配
PUT test
{
    "settings": {
        "index.write.wait_for_active_shards": "1"
    }
}

PUT test?wait_for_active_shards=2
```

# Delete Index

```
DELETE /twitter
```

上面的例子删除了一个名为twitter的索引。需要指定索引或通配符表达式。别名不能用于删除索引。通配符表达式被解析为只匹配具体的索引。

通过使用逗号分隔的列表，或者通过使用`_all`或`*`作为索引，delete index还可以应用于多个索引。

禁用允许通过通配符或`_all`删除索引，`config/elasticsearch.yml`

```
action.destructive_requires_name：true
```

还可以通过集群更新设置api更改此设置

```
PUT /_cluster/settings?flat_settings=true
{
  "transient": {
    "action.destructive_requires_name": true
  }
}
```



# Get Index

```
GET /twitter
```

上面的示例获取名为twitter的索引的信息，包括别名、映射和设置。需要指定索引、别名或通配符表达式。

get index还可以应用于多个索引，或者通过使用`_all`或`*`作为索引应用于所有索引。



# Indices Exists

用于检查索引(索引)是否存在。例如:

```
HEAD twitter
```

HTTP状态码指示索引是否存在。404表示不存在，200表示存在。

这个请求不区分索引和别名，也就是说，如果别名与该名称存在，也返回状态码200。



# Open/Close Index

一个关闭的索引在集群中几乎没有开销(除了维护它的元数据之外)，并且被阻塞以进行读/写操作。关闭的索引可以打开，然后通过正常的恢复过程。

```
POST /my_index/_close

POST /my_index/_open
```

可以打开和关闭多个索引。如果请求显式地引用关闭的索引，则会抛出错误。可以使用`ignore_unavailable=true`参数禁用此行为。

```
GET test/_search?ignore_unavailable=true
{
  "query": {
    "match_all": {}
  }
}
```

> 查询禁用的关闭的索引不报错

所有索引都可以使用`_all`作为索引名或指定识别它们的模式(例如*)同时打开或关闭。

通过设置配置文件中的`action.destructive_requires_name`配置为true，可以禁用通过通配符或_all标识索引的功能。

关闭索引会消耗大量磁盘空间。关闭的索引会继续占用磁盘空间, 却又不能使用，从而造成磁盘空间的浪费。可以通过集群设置`cluster.indices.close.enable`来禁用关闭索引。启用为false。默认值为true。

```
//禁止关闭索引
PUT /_cluster/settings
{
    "transient" : {
       "cluster.indices.close.enable":false
    }
}
```

因为打开索引会分配它的分片，所以创建索引时的wait_for_active_shards设置也适用于索引打开操作。open index上的wait_for_active_shards设置的默认值是0，这意味着命令不会等待分配shards。

> 打开的索引过多，会造成活跃分片过多，占用大量的JVM空间，造成JVM内存不足

# Type Exists

用于检查一个类型/类型是否存在于索引/索引中。

```
HEAD twitter/_mapping/tweet
```

# 批量索引

用于索引大量数据且并不急于搜索的时候，在批量索引开始之前，使关闭索引的刷新间隔，即不可搜索

```
PUT /twitter/_settings
{
    "index" : {
        "refresh_interval" : "-1"
    }
}
```

>  另一个优化选项是在启动索引时不添加任何副本，然后再添加它们

然后，一旦批量索引完成，设置可以更新(回到默认):

```
PUT /twitter/_settings
{
    "index" : {
        "refresh_interval" : "1s"
    }
}


```

并且强制合并为一个段：

```
POST /twitter/_forcemerge?max_num_segments=5
```



# 更新分词器

```
POST /twitter/_close

PUT /twitter/_settings
{
  "analysis" : {
    "analyzer":{
      "content":{
        "type":"custom",
        "tokenizer":"whitespace"
      }
    }
  }
}

POST /twitter/_open
```



# 获取设置

```
GET /twitter/_settings
GET /_all/_settings
GET /log_2013_-*/_settings/index.number_*
```



# Analyze

对文本执行分析过程，并返回文本的标记分解。

```
GET _analyze
{
  "analyzer" : "standard",
  "text" : "this is a test"
}

GET analyze_sample/_analyze
{
  "text" : "this is a test"
}

GET analyze_sample/_analyze
{
  "field" : "obj1.field1",
  "text" : "this is a test"
}
```

分词计划

```
GET _analyze
{
  "tokenizer" : "standard",
  "filter" : ["snowball"],
  "text" : "detailed output",
  "explain" : true,
  "attributes" : ["keyword"] 
}
```

# Indices Shard Stores

提供索引的分片副本的存储信息。存储信息报告关于哪些节点存在分片副本、分片副本分配ID、每个分片副本的唯一标识符，以及在打开分片索引或早期引擎故障时遇到的任何异常。

默认情况下，列表存储至少一个未分配副本的分片的信息。当集群运行状况状态为黄色时，将列出至少有一个未分配副本的分片的存储信息。当集群运行状况状态为红色时，将列出具有未分配主节点的shard的存储信息。

> 查询未分配分片的列表

```
# return information of only index test
GET /test/_shard_stores

# return information of only test1 and test2 indices
GET /test1,test2/_shard_stores

# return information of all indices
GET /_shard_stores
```

可以通过状态参数更改列出存储信息的shard的范围。默认为黄色和红色。黄色列表存储至少有一个副本未分配的分片信息，红色列表存储主分片未分配的分片信息。使用绿色列出所有已分配副本的分片的存储信息。

```
GET /_shard_stores?status=green
```

响应

```
{
   "indices": {
       "my-index": {
           "shards": {
              "0": {   键是存储信息对应的分片id
                "stores": [   分片的所有副本的存储信息列表
                    {
                        "sPa3OgxLSYGvQ4oPs-Tajw": {  存放存储副本的节点信息，密钥是惟一的节点id。
                            "name": "node_t0",
                            "ephemeral_id" : "9NlXRFGCT1m8tkvYCMK-8A",
                            "transport_address": "local[1]",
                            "attributes": {}
                        },
                        "allocation_id": "2iNySv_OQVePRX-yaRH_lQ", 存储副本的分配id
                        "allocation" : "primary|replica|unused"  存储副本的状态，无论它是作为主副本使用，还是根本没有使用
                        "store_exception": ... 打开分片索引时遇到的任何异常或以前的引擎故障引起的异常
                    }
                ]
              }
           }
       }
   }
}
```



# Clear Cache

清除缓存允许清除所有缓存或与一个或多个索引关联的特定缓存。

```
POST /_cache/clear
POST /twitter/_cache/clear
POST /kimchy,elasticsearch/_cache/clear
```

默认情况下，该请求将清除所有缓存。通过将query、fielddata或request url参数设置为true，可以显式地清理特定的缓存。

```
POST /twitter/_cache/clear?query=true      
POST /twitter/_cache/clear?request=true    
POST /twitter/_cache/clear?fielddata=true   
```

除此之外，还可以通过指定fields url参数来清除与特定字段相关的所有缓存，并使用逗号分隔的应清除字段列表。请注意，提供的名称必须引用具体字段—不支持对象和字段别名。

```
POST /twitter/_cache/clear?fields=foo,bar   
```

# Force Merge

强制合并允许强制合并一个或多个索引。合并与Lucene索引在每个分片中保存的段数有关。强制合并操作允许通过合并它们来减少片段的数量。

此调用将阻塞，直到合并完成。如果http连接丢失，请求将在后台继续，并且任何新的请求将被阻塞，直到前一次强制合并完成。

只能对只读索引调用强制合并。对一个读写索引执行强制合并可能会产生非常大的段(每个段5Gb)，并且合并策略不会再考虑它，直到它主要包含已删除的文档。这可能导致非常大的段保留在分片中。

```
POST /twitter/_forcemerge
POST /kimchy/_forcemerge?only_expunge_deletes=false&max_num_segments=100&flush=true
POST /kimchy,elasticsearch/_forcemerge
POST /_forcemerge

?max_num_segments=1
max_num_segments 要合并到的段的数目。要完全合并索引，请将其设置为1。默认情况下只是检查合并是否需要执行，如果需要，就执行它。


only_expunge_deletes 
在合并进程只删除标记有删除的段。
在Lucene中，文档不是从一个段中删除的，只是标记为删除。在段的合并过程中，将创建一个不包含删除操作的新段。此标志只允许合并已删除的段。默认值为false。注意，这不会覆盖index.merge.policy.expunge_deletes_allowed阈值。

flush 是否在强制合并后执行刷新。默认值为true。
```



在Elasticsearch中，分片是一个Lucene索引，而Lucene索引被分解为多个片段。段是存储索引数据的索引中的内部存储元素，并且是不可变的。较小的段会定期合并为较大的段，以保持索引大小不变，并删除标记删除的内容。

合并过程使用自动调节来平衡合并和其他活动(如搜索)之间硬件资源的使用。

合并调度程序(ConcurrentMergeScheduler)控制需要合并操作时的执行。合并在不同的线程中运行，当达到最大的线程数时，进一步的合并将等待，直到有一个合并线程可用。

`index.merge.scheduler.max_thread_count`

单个分片上可能同时合并的最大线程数。默认为`Math.max(1, Math.min(4, Runtime.getRuntime().availableProcessors() / 2))`它适用于良好的固态磁盘(SSD)。如果你的索引是在旋转磁盘驱动器上，减少到1。



# 索引刷新

索引的刷新过程确保当前只持久化到事务日志中的数据也会永久持久化到Lucene中。这减少了恢复时间，因为在Lucene索引被打开后，不需要从事务日志中重新索引数据。默认情况下，Elasticsearch使用内部机制自动触发刷新。

```
POST _flush
POST twitter/_flush
POST kimchy,elasticsearch/_flush

POST _flush?wait_if_ongoing=true
```

wait_if_ongoing

```
如果设置为true，则刷新操作将阻塞，直到下一个刷新已经被执行。默认值为false，如果已经在运行另一个刷新操作，则会导致在分片级别上抛出异常。
```

force

```
是否应该强制一个不必要的刷新，即使没有任何更改将提交到索引。
强制刷新（该操作为内部操作，谨慎使用）
```



# 同步刷新

Elasticsearch跟踪每个分片的索引活动。5分钟内没有收到任何索引操作的分片将自动标记为非活动。这为Elasticsearch提供了减少分片资源的机会，还可以执行一种特殊的刷新，称为同步刷新。同步刷新执行普通的刷新，然后将生成的惟一标记(sync_id)添加到所有分片。

由于sync id标记是在没有正在进行的索引操作时添加的，它可以用来快速检查两个分片的lucene索引是否相同。这种快速的同步id比较(如果存在)在恢复或重启期间使用，以跳过该过程的第一个和最昂贵的阶段（有助于索引恢复速度的提高）。

在这种情况下，不需要复制段文件，恢复的事务日志重播阶段可以立即开始。注意，由于同步id标记是与刷新一起应用的，因此事务日志很可能为空，从而进一步加速恢复。

这对于拥有大量从未更新或很少更新的索引的用例特别有用，例如基于时间的数据。这个用例通常会生成许多索引，如果没有同步刷新标记，这些索引的恢复将花费很长时间。

要检查一个分片是否有标记：

```
GET twitter/_stats?filter_path=**.commit&level=shards 
```



## 同步刷新请求

同步刷新(滚动)集群重启特别有用，因为可以停止索引，并且不想等待默认的5分钟来自动同步刷新空闲索引。

- 同步刷新是一个很好的操作。但是任何正在进行的索引操作都将导致同步刷新在该分片上失败。这意味着一些分片可能被同步刷新，而另一些则没有。
- 当再次刷新分片时，sync_id标记将被删除。这是因为刷新替换了存储标记的低层lucene提交点。事务日志中的未提交操作不会删除该标记。在实践中，应该考虑对索引的任何索引操作可能会在任何时候触发清除标记。

在进行索引时请求同步刷新是无害的。有些空闲的分片会成功，有些空闲的分片会失败。任何成功的分片都将有更快的恢复时间。

```
POST twitter/_flush/synced
POST kimchy,elasticsearch/_flush/synced
POST _flush/synced
```



## 标记查看

要检查一个分片是否有标记，请查找由indices stats返回的分片统计数据的提交部分:

```
GET twitter/_stats?filter_path=**.commit&level=shards 

//响应
{
  "indices" : {
    "es-7.7.0-2020.10.23.09.13" : {
      "shards" : {
        "0" : [
          {
            "commit" : {
              "id" : "/6+ctWfPT3iIpOzBCGlWcg==",
              "generation" : 6,
              "user_data" : {
                "local_checkpoint" : "2402",
                "max_unsafe_auto_id_timestamp" : "1603415763768",
                "translog_uuid" : "TY7CtKJLTHG0UP0PRB0EPg",
                "history_uuid" : "M9Rn1u5OSNGRIlZa1Z2EYA",
                "translog_generation" : "6",
                "max_seq_no" : "2402"
              },
              "num_docs" : 2403
            }
          }
        ],
        
//同步刷新
POST es-7.7.0-2020.10.23.09.13/_flush/synced

{
  "indices" : {
    "es-7.7.0-2020.10.23.09.13" : {
      "shards" : {
        "0" : [
          {
            "commit" : {
              "id" : "/6+ctWfPT3iIpOzBCGlcVg==",
              "generation" : 8,
              "user_data" : {
                "local_checkpoint" : "2402",
                "max_unsafe_auto_id_timestamp" : "1603415763768",
                "translog_uuid" : "TY7CtKJLTHG0UP0PRB0EPg",
                "history_uuid" : "M9Rn1u5OSNGRIlZa1Z2EYA",
                "sync_id" : "ie7EmOiZTkargLmBCo-IGg",   //sync_id
                "translog_generation" : "7",
                "max_seq_no" : "2402"
              },
              "num_docs" : 2403
            }
          }
        ],
```

该响应包含关于有多少个分片被成功地同步刷新的详细信息和关于任何失败的信息。

当有分片刷新失败时的情况：

```
{
   "_shards": {
      "total": 2,
      "successful": 2,
      "failed": 0
   },
   "twitter": {
      "total": 2,
      "successful": 2,
      "failed": 0
   }
}
```

因为挂起操作而导致一个分片组失败时的情况:

```
{
   "_shards": {
      "total": 4,
      "successful": 2,
      "failed": 2
   },
   "twitter": {
      "total": 4,
      "successful": 2,
      "failed": 2,
      "failures": [
         {
            "shard": 1,
            "reason": "[2] ongoing operations on primary"
         }
      ]
   }
}
```

同步刷新由于并发索引操作而失败时，会出现上述错误。在这种情况下，HTTP状态码将是409 CONFLICT。

有时候失败的副本将不符合快速恢复的条件，但成功的副本仍然符合快速恢复的条件。

```
{
   "_shards": {
      "total": 4,
      "successful": 1,
      "failed": 1
   },
   "twitter": {
      "total": 4,
      "successful": 3,
      "failed": 1,
      "failures": [
         {
            "shard": 1,
            "reason": "unexpected error",
            "routing": {
               "state": "STARTED",
               "primary": false,
               "node": "SZNr2J_ORxKTLUCydGX4zA",
               "relocating_node": null,
               "shard": 1,
               "index": "twitter"
            }
         }
      ]
   }
}
```

当分片副本不能同步刷新时，返回的HTTP状态码将是409冲突。



# 重刷新

该操作可使自上次刷新以来执行的所有操作都可用于搜索。(接近)实时功能取决于所使用的索引引擎。例如，内部调用需要刷新，但默认情况下定期安排刷新。

```
POST /_refresh
POST /twitter/_refresh
POST /kimchy,elasticsearch/_refresh
```

`index.refresh_interval`

执行刷新操作的频率，刷新操作使最近对索引的更改在搜索中可见。默认为1s。可以设置为-1来禁用刷新。



?refresh

索引、更新、删除和批量都支持设置refresh来控制何时对搜索可见此请求所做的更改。

```
支持以下值：

Empty string or true

在操作发生后立即刷新相关的主分片和复制分片(而不是整个索引)，以便更新后的文档立即出现在搜索结果中。从索引和搜索的角度来看，这应该在经过仔细考虑和验证之后才可以进行。

wait_for

在回应之前，等待通过刷新使请求所做的更改可见。这不会强制立即刷新，而是等待刷新发生。Elasticsearch自动刷新每个索引都改变了的分片。refresh_interval默认为1秒。这种设置是动态的。在任何支持刷新API的API上调用刷新API或将刷新设置为true也会导致刷新，从而导致已经运行的Refresh =wait_for请求返回。

false(the default)
不执行刷新相关操作。此请求所做的更改将在请求返回后的某个时刻可见。
```

除非有很好的理由等待更改变得可见，否则始终使用refresh=false，或者(因为这是默认值)将刷新参数保留在URL之外。这是最简单和最快的选择。

如果必须让请求所做的更改与请求同步可见，那么必须在增加Elasticsearch的负载(true)和等待响应的时间(wait_for)之间做出选择。该决定应考虑以下几点:

- 与true相比，对索引进行的更改越多，wait_for保存的工作就越多。在每个索引只更改一次的情况下。refresh_interval则不保存任何工作。
- true将创建效率较低的索引构造(小段)，这些构造必须稍后合并为更高效的索引构造(较大的段)。这意味着true的代价在索引时用于创建小段，在搜索时用于搜索小段，以及在合并时用于生成更大的段。
- 不要在一行中启动多个refresh=wait_for请求。应该使用refresh=wait_for和Elasticsearch将它们批处理成单个批量请求，并并行启动它们，只有当它们全部完成时才返回。
- 如果刷新间隔设置为-1，禁用自动刷新，那么使用refresh=wait_for的请求将无限期地等待，直到某个操作导致刷新。另外，设置index.refresh_interval比默认值短一些，比如200ms，会使refresh=wait_for返回得更快，但仍然会生成效率低下的段。
- refresh=wait_for只影响它所在的请求，但是，通过强制立即刷新，refresh=true将影响其他正在进行的请求。通常，如果您有一个正在运行的系统，您不希望干扰它，那么refresh=wait_for是一个较小的修改。

`refresh=wait_for` 会导致强制刷新

如果在已经有index.max_refresh_listeners（默认为1000）个请求中进入refresh= wait_for请求，则该请求将等待对该分片的刷新，则该请求的行为就好像刷新设置为true一样：它将强制刷新。 这样可以保证，当refresh = wait_for请求返回时，其更改对于搜索是可见的，同时防止阻止的请求未经检查地使用资源。 如果一个请求由于没有足够的侦听器插槽而被强制刷新，则其响应将包含“ forced_refresh”：true。

批量请求在它们所触及的每个分片上只占用一个槽位，无论它们修改分片多少次。

创建一个文档，并立即刷新索引，使其可见:

```
PUT /test/_doc/1?refresh
{"test": "test"}
PUT /test/_doc/2?refresh=true
{"test": "test"}
```

创建一个文档，而不做任何事情，使其稍后可见:

```
PUT /test/_doc/3
{"test": "test"}
PUT /test/_doc/4?refresh=false
{"test": "test"}
```

创建一个文档，并等待可见:

```
PUT /test/_doc/4?refresh=wait_for
{"test": "test"}
```

# 索引排序

当在Elasticsearch中创建一个新的索引时，可以配置每个分片内的片段将如何排序。默认情况下，Lucene不应用任何排序。index.sort.*设置定义了应该使用哪些字段来排序每个段内的文档。

> 警告：嵌套字段与索引排序不兼容，因为它们依赖于假设嵌套文档存储在连续的doc id中，而索引排序可以破坏这些id。如果在包含嵌套字段的索引上激活索引排序，将抛出错误。

```
PUT twitter
{
    "settings" : {
        "index" : {
            "sort.field" : "date", 
            "sort.order" : "desc" 
        }
    },
    "mappings": {
        "_doc": {
            "properties": {
                "date": {
                    "type": "date"
                }
            }
        }
    }
}

PUT twitter
{
    "settings" : {
        "index" : {
            "sort.field" : ["username", "date"], 
            "sort.order" : ["asc", "desc"] 
        }
    },
    "mappings": {
        "_doc": {
            "properties": {
                "username": {
                    "type": "keyword",
                    "doc_values": true
                },
                "date": {
                    "type": "date"
                }
            }
        }
    }
}
```

参数：

```
index.sort.field
index.sort.order 
index.sort.mode 
index.sort.missing 
```

默认情况下，在Elasticsearch中，搜索请求必须访问与查询匹配的每个文档，以检索按指定排序的顶级文档。尽管当索引排序和搜索排序相同时，可以限制每段应该访问的文档数量，以在全局范围内检索N个排名最高的文档。例如，我们有一个索引，它包含按时间戳字段排序的事件:

```
PUT events
{
    "settings" : {
        "index" : {
            "sort.field" : "timestamp",
            "sort.order" : "desc" 
        }
    },
    "mappings": {
        "doc": {
            "properties": {
                "timestamp": {
                    "type": "date"
                }
            }
        }
    }
}

GET /events/_search
{
    "size": 10,
    "sort": [
        { "timestamp": "desc" }
    ]
}
```

Elasticsearch会检测到每个片段的顶级文档已经在索引中排序，并且只会比较每个片段的前N个文档。收集与查询匹配的其余文档，以计算结果的总数并构建聚合。

如果只是在寻找最后10个事件，对匹配查询的文档总数没有兴趣，可以设置track_total_hits为false:

```
GET /events/_search
{
    "size": 10,
    "sort": [ 
        { "timestamp": "desc" }
    ],
    "track_total_hits": false
}
```

这一次，Elasticsearch将不再尝试计算文档的数量，并且能够在每个片段收集到N个文档后立即终止查询。

由于提前终止，匹配查询的总命中数未知。
