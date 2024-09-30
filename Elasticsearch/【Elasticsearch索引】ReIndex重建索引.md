# ReIndex

## 集群升级

Elasticsearch可以读取在以前主要版本中创建的索引。旧索引必须重新索引或删除，Elasticsearch 6可以使用Elasticsearch 5中创建的索引，但不能是在Elasticsearch 2或之前创建的索引。Elasticsearch 5可以使用Elasticsearch 2中创建的索引，但不能是在Elasticsearch1或之前创建的索引。

如果存在不兼容的索引，Elasticsearch节点将无法启动。



## 重建过程

使用reindex手动重新索引旧索引:

- 创建一个新索引，并从旧索引复制映射和设置。

- 将refresh_interval设置为-1，将number_of_replicas设置为0，可以有效地重新索引。

- 使用Reindex将旧索引中的所有文档重新索引到新索引中。

- 将refresh_interval和number_of_replicas重置为旧索引中使用的值。

- 等待索引状态变为绿色。

- 在一个单一的更新别名请求中:

   - 删除旧索引。
   - 将旧索引名的别名添加到新索引中。
   - 将旧索引上存在的别名添加到新索引中。





## 索引重建

> Reindex要求对源索引中的所有文档启用_source。
>

> Reindex自动设置目标索引，但是不复制源索引的设置。 应该在运行_reindex操作之前设置目标索引，包括设置映射、分片计数、副本等。
>

reindex最基本的形式只是将文档从一个索引复制到另一个索引。这将把文档从twitter索引复制到new_twitter索引中:

```
POST _reindex
{
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter"
  }
}
```

就像update_by_query一样，reindex获取源索引的快照，但是它的目标必须是一个不同的索引，这样就不太可能出现版本冲突。可以像新建索引那样配置dest子句来控制乐观并发控制。忽略version_type或将其设置为internal会导致Elasticsearch盲目地将文档转储到目标中，覆盖任何恰巧具有相同类型和id的文档:

```
POST _reindex
{
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter",
    "version_type": "internal"
  }
}
```

将version_type设置为external会导致Elasticsearch保存源文件的版本，创建任何缺失的文档，并更新目标索引中版本比源索引中版本更旧的文档:

```
POST _reindex
{
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter",
    "version_type": "external"
  }
}
```

设置op_type为create将导致_reindex只在目标索引中创建缺少的文档。所有现有文档将导致版本冲突:

```
POST _reindex
{
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter",
    "op_type": "create"
  }
}

错误示例：
"[_doc][2]: version conflict, document already exists (current version [2])"
```

默认情况下，版本冲突中止reindex进程，但你可以通过设置“conflicts”:“proceed”忽略冲突继续执行:

```
POST _reindex
{
  "conflicts": "proceed",
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter",
    "op_type": "create"
  }
}
```

可以通过向源添加类型或添加查询来限制文档。这将只复制匹配kimchy的文档到new_twitter中:

```
POST _reindex
{
  "source": {
    "index": "twitter",
    "type": "_doc",
    "query": {
      "term": {
        "user": "kimchy"
      }
    }
  },
  "dest": {
    "index": "new_twitter"
  }
}
```

source中的索引和类型都可以是列表，允许 在一个请求中从许多源进行复制。这将从twitter的_doc类型中和blog索引的post类型中复制文档。

```
POST _reindex
{
  "source": {
    "index": ["twitter", "blog"],
    "type": ["_doc", "post"]
  },
  "dest": {
    "index": "all_together",
    "type": "_doc"
  }
}
```

> Reindex 不充分的处理ID冲突，因此最新的文档将“获胜”，但顺序通常是不可预测的，因此依赖这种行为不是一个好主意。相反，应该使用脚本确保id是惟一的。
>

还可以通过设置size来限制已处理文档的数量。这只会将一个文档从twitter复制到new_twitter:

```
POST _reindex
{
  "size": 1,
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter"
  }
}
```

如果 想要从twitter索引中获得一组特定的文档，则需要使用排序。排序会降低滚动的效率，但在某些情况下，这样做是值得的。如果可能的话，请选择更具选择性的查询而不是size和sort。这将从twitter复制10000个文档到new_twitter:

```
POST _reindex
{
  "size": 10000,
  "source": {
    "index": "twitter",
    "sort": { "date": "desc" }
  },
  "dest": {
    "index": "new_twitter"
  }
}
```

source部分支持搜索请求中支持的所有元素。例如，只有原始文档中字段的子集也可以使用如下源过滤重新索引:

```
POST _reindex
{
  "source": {
    "index": "twitter",
    "_source": ["user", "_doc"]
  },
  "dest": {
    "index": "new_twitter"
  }
}
```

与update_by_query一样，reindex支持修改文档的脚本。与_update_by_query不同，允许脚本修改文档的元数据。这个例子与源文档的版本冲突:

```
POST _reindex
{
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter",
    "version_type": "external"
  },
  "script": {
    "source": "if (ctx._source.foo == 'bar') {ctx._version++; ctx._source.remove('foo')}",
    "lang": "painless"
  }
}
```



 可以使用以下请求将公司名称为cat的源索引中的所有文档复制到路由设置为cat的dest索引中。

```
POST _reindex
{
  "source": {
    "index": "source",
    "query": {
      "match": {
        "company": "cat"
      }
    }
  },
  "dest": {
    "index": "dest",
    "routing": "=cat"
  }
}
```

默认情况下，reindex使用1000的滚动批。 可以更改size批大小字段在源元素:

```
POST _reindex
{
  "source": {
    "index": "source",
    "size": 100
  },
  "dest": {
    "index": "dest",
    "routing": "=cat"
  }
}
```

Reindex还可以通过这样指定pipeline来使用Ingest节点特性:

```
POST _reindex
{
  "source": {
    "index": "source"
  },
  "dest": {
    "index": "dest",
    "pipeline": "some_ingest_pipeline"
  }
}
```



## 远端集群

Reindex支持从一个远程Elasticsearch集群重建索引:

```
POST _reindex
{
  "source": {
    "remote": {
      "host": "http://otherhost:9200",
      "username": "user",
      "password": "pass"
    },
    "index": "source",
    "query": {
      "match": {
        "test": "data"
      }
    }
  },
  "dest": {
    "index": "dest"
  }
}
```



host参数必须包含一个连接方式，主机，端口(例如:`https://otherhost:9200`)和可选路径(例如:`https://otherhost:9200/proxy`)。username,和password参数是可选的，当它们出现时，reindex将使用基本身份验证连接到远程Elasticsearch节点。在使用基本身份验证时，请确保使用https，否则密码将以纯文本形式发送。

远程主机必须使用`reindex.remote.whitelist`在elasticsearch.yaml中显式白名单。可以将其设置为允许的远程主机和端口组合(例如otherhost:9200, another:9200, 127.0.10.*:9200, localhost:\*)的逗号分隔列表。只需设置主机和端口即可（连接方式忽略-），例如:

```
reindex.remote.whitelist: "otherhost:9200, another:9200, 127.0.10.*:9200, localhost:*"
```

必须在协调重建索引的每一个节点上配置白名单。

这个特性应该适用于 可能找到的任何版本的Elasticsearch的远程集群。这将允许 从任何版本的Elasticsearch升级到当前版本，方法是对旧版本的集群进行索引重建。

为了使查询能够发送到旧版本的Elasticsearch，查询参数将直接发送到远程主机，而不需要进行验证或修改。

> 从远程集群重新索引不支持手动或自动切片。
>

从远程服务器重新索引使用堆上缓冲区，默认最大为100mb。如果远程索引包含非常大的文档，则需要使用较小的批处理大小。下面的示例将批处理大小设置为10，这非常非常小。

```
POST _reindex
{
  "source": {
    "remote": {
      "host": "http://otherhost:9200"
    },
    "index": "source",
    "size": 10,
    "query": {
      "match": {
        "test": "data"
      }
    }
  },
  "dest": {
    "index": "dest"
  }
}
```

还可以使用socket_timeout字段在远程连接上设置套接字读取超时，使用connect_timeout字段设置连接超时。两者都默认为30秒。这个例子将套接字读取超时设置为1分钟，连接超时设置为10秒:

```
POST _reindex
{
  "source": {
    "remote": {
      "host": "http://otherhost:9200",
      "socket_timeout": "1m",
      "connect_timeout": "10s"
    },
    "index": "source",
    "query": {
      "match": {
        "test": "data"
      }
    }
  },
  "dest": {
    "index": "dest"
  }
}
```



## URL参数

除了像pretty这样的标准参数外，Reindex还支持refresh、wait_for_completion、wait_for_active_shards、timeout、scroll和requests_per_second。

发送refresh参数将导致刷新所有索引的写请求。这与Index的refresh参数不同，后者只会刷新接收到新数据的分片。另外，与Index不同，它不支持wait_for。

如果请求包含wait_for_completion=false，那么Elasticsearch将进行一些执行前检查，启动请求，然后返回一个任务，该任务可用于task来取消或获得该任务的状态。Elasticsearch还将在`.tasks/task/${taskId}`处创建该任务的记录作为文档。你可以自主决定保留或删除。当你完成或删除它时，使用的空间将被回收。

wait_for_active_shards控制在继续进行重建索引之前必须激活一个分片的多少个副本。timeout控制每个写请求等待不可用分片变为可用的时间。两者的工作方式与它们在Bulk中的工作方式完全相同。由于_reindex使用scroll搜索，你也可以指定滚动参数来控制它保持“搜索上下文”存活的时间(例如?scroll=10m)。默认值是5分钟。

可以将requests_per_second设置为任何正的十进制数(1.4、6、1000等)，并通过填充每个批处理的等待时间来调节_reindex发出批索引操作的速度。可以通过将requests_per_second设置为-1来禁用限流。

限流是通过在批之间等待来完成的，这样_reindex在内部使用的scroll就可以获得一个数据索引的时间。该时间是批处理大小除以requests_per_second与花费在写索引上的时间的差。默认情况下批大小为1000，因此如果将requests_per_second设置为500:

```
target_time = 1000 / 500 per second = 2 seconds
wait_time = target_time - write_time = 2 seconds - 0.5 seconds = 1.5 seconds
```

由于批处理是作为单个_bulk请求发出的，因此较大的批处理将导致Elasticsearch创建多个请求，然后在开始下一组请求之前等待一段时间。默认值是-1。



## 任务

查找执行中的ReIndex任务

```
GET _tasks?human&detailed=true&actions=*reindex
```

根据TaskID查找：

```
GET /_tasks/r1A2WoRbTwKZ516z6NEs5A:36619
```

取消任务：

```
POST _tasks/r1A2WoRbTwKZ516z6NEs5A:36619/_cancel
```



## 限流修改

```
POST _reindex/r1A2WoRbTwKZ516z6NEs5A:36619/_rethrottle?requests_per_second=-1
```

就像在Reindex请求上设置时一样，requests_per_second可以为-1来禁用，也可以为任何十进制数(如1.7或12)来限制到该级别。比修改值大的requests_per_second将立即生效，而修改值小的requests_per_second将在完成当前批处理后生效。这可以防止滚动超时。



## 字段重命名

_reindex可用于构建具有重命名字段的索引副本。假设你创建了一个包含如下文档的索引:

```
POST test/_doc/1?refresh
{
  "text": "words words",
  "flag": "foo"
}
```

但是 不喜欢flag这个名字，想用tag替换它。reindex可以为 创建另一个索引:

```
POST _reindex
{
  "source": {
    "index": "test"
  },
  "dest": {
    "index": "test2"
  },
  "script": {
    "source": "ctx._source.tag = ctx._source.remove(\"flag\")"
  }
}
```

新文档：

```
GET test2/_doc/1

{
  "found": true,
  "_id": "1",
  "_index": "test2",
  "_type": "_doc",
  "_version": 1,
  "_source": {
    "text": "words words",
    "tag": "foo"
  }
}

```



## 切片

Reindex支持切片滚动以并行化重建索引。这种并行化可以提高效率，并提供一种方便的方法来将请求分解成更小的部分。

### 手动切片

手动切片一个重建索引请求，对每个请求提供一个切片id和切片总数:

```
POST _reindex
{
  "source": {
    "index": "twitter",
    "slice": {
      "id": 0,
      "max": 2
    }
  },
  "dest": {
    "index": "new_twitter"
  }
}

POST _reindex
{
  "source": {
    "index": "twitter",
    "slice": {
      "id": 1,
      "max": 2
    }
  },
  "dest": {
    "index": "new_twitter"
  }
}
```

验证：

```
GET _refresh
POST new_twitter/_search?size=0&filter_path=hits.total
```



### 自动切片

还可以使用切片滚动在_uid上进行切片，让_reindex自动并行化。使用切片来指定要使用的切片数量:

```
POST _reindex?slices=5&refresh
{
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter"
  }
}
```

验证：

```
POST new_twitter/_search?size=0&filter_path=hits.total
```



将slices设置为auto，将让Elasticsearch选择切片的数量。该设置将为每个分片使用一个片，但不超过一定的限制。如果有多个源索引，它将根据具有最小分片数量的索引来选择切片的数量。

在ReIndex中使用slices将自动完成上述的手动部分，并创建子请求，但是这也意味着它有一些不一样的地方：

-  可以使用Tasks命令来看到这些请求。这些子请求是带有slices的请求的任务的“子”任务。
- 为带有slices的请求获取任务的状态只包含已完成的切片的状态。
- 这些子请求可以针对取消和重新throttling（限流）等事件单独寻址。
- 重新调整包含slices的请求将按比例重新调整未完成的子请求。
- 取消使用slices的请求将取消每个子请求
- 由于slices的性质，每个子请求不会完全均匀地得到文档的一部分。所有文档都将被寻址，但是一些切片可能比其他的更大。更大的切片将有一个更均匀的分布。
- 带有slices的请求中的requests_per_second和size等参数按比例分布于每个子请求。结合上面关于分布不均匀的观点， 应该可以得出结论，使用size和slices可能不会导致同样大小的文档被' _reindex ' 。
- 每个子请求都获得一个源索引的略有不同的快照，尽管这些快照几乎是同时获得的。



### 选择切片的数量

如果自动切片，将slices设置为auto将为大多数索引选择一个合理的数字。如果手动切片或调优自动切片，请使用以下指导原则。

当切片的数量与索引中的分片数量相等时，查询性能的效率最高。如果这个数字很大(例如500)，则选择较低的数字，因为太多的切片会影响性能。设置大于分片数量的切片通常不会提高效率，而且会增加开销。

索引性能与可用资源的切片数成线性关系。

查询或索引性能在运行时的主要因素为被重新索引的文档和集群资源。



## 重建多个索引

如果 有许多索引要重建，通常最好一次一个，而不是使用一个全局模式来重建许多索引。这样，如果有任何错误， 可以通过删除部分完成的索引并在该索引处重新开始来恢复该过程。它还使得并行化过程相当简单:分割索引列表以重新索引并并行地运行每个列表。

bash 脚本：

```
for index in i1 i2 i3 i4 i5; do
  curl -HContent-Type:application/json -XPOST localhost:9200/_reindex?pretty -d'{
    "source": {
      "index": "'$index'"
    },
    "dest": {
      "index": "'$index'-reindexed"
    }
  }'
done
```



## 重建日期索引

尽管有上述建议，但 可以结合reindex和Painless来重建日期索引，从而将新模板应用到现有文档。

文档内容：

```
PUT metricbeat-2016.05.30/_doc/1?refresh
{"system.cpu.idle.pct": 0.908}
PUT metricbeat-2016.05.31/_doc/1?refresh
{"system.cpu.idle.pct": 0.105}
```

metricbeat-*索引的新模板已经加载到Elasticsearch中，但它只适用于新创建的索引。Painless可用于重新索引现有文档并应用新模板。

下面的脚本从索引名称中提取日期，并创建一个附加了-1的新索引。所有来自metricbeat-2016.05.31的数据将被重新索引到metricbeat-2016.05.31-1中。

```
POST _reindex
{
  "source": {
    "index": "metricbeat-*"
  },
  "dest": {
    "index": "metricbeat"
  },
  "script": {
    "lang": "painless",
    "source": "ctx._index = 'metricbeat-' + (ctx._index.substring('metricbeat-'.length(), ctx._index.length())) + '-1'"
  }
}
```

查询：

```
GET metricbeat-2016.05.30-1/_doc/1
GET metricbeat-2016.05.31-1/_doc/1
```

前面的方法还可以与更改字段的名称一起使用，以便仅将现有数据加载到新索引中，并在需要时重命名任何字段。



## 抽取随机文档

reindex可以用来提取一个索引的随机子集用于测试:

```
POST _reindex
{
  "size": 10,
  "source": {
    "index": "twitter",
    "query": {
      "function_score" : {
        "query" : { "match_all": {} },
        "random_score" : {}
      }
    },
    "sort": "_score"    
  },
  "dest": {
    "index": "random_twitter"
  }
}

reindex默认是按_doc排序的，所以random_score将没有任何效果，除非 将排序重写为_score。
```