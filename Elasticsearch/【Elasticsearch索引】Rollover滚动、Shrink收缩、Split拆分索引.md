#  Rollover index

当现有索引被认为太大或太旧时，滚动索引将别名转到新索引。

> 即滚动索引表示的是索引别名与索引的相对应关系
>
> 1、别名只能指向一个索引
>
> 2、如果索引名是"-" 加 数字结尾。例如，logs-000001 ，那么新索引的名称将遵循相同的模式，递增编号(logs-000002)。无论旧索引名是什么，数字都用6的长度进行零填充。

该请求接受一个别名和一组条件。要使rollover请求有效，别名必须指向写索引。有两种方法可以实现这一点，根据配置，别名元数据将以不同的方式更新。

两种情况如下:

1、别名仅指向没有配置is_write_index的单个索引(默认为null)。

在这个场景中，原始索引的滚动别名将被添加到新创建的索引中，并从原始(滚动)索引中删除。

> 索引滚动的过程不是自动执行的，需要在到达条件后手动执行，才可以达到索引滚动的目的。
>

## 应用场景

当需要管理基于时间设置的索引时，这个功能比较有用。



## 设置滚动索引

```
PUT /logs-000001 
{
  "aliases": {
    "logs_write": {}
  }
}
# Add > 1000 documents to logs-000001
POST /logs_write/_rollover 
{
  "conditions": {
    "max_age":   "7d",
    "max_docs":  1000,
    "max_size":  "5gb"
  }
}

如果logs_write指向的索引是在7天或更早之前创建的，或者包含1,000个或更多文档，或者索引大小至少在5GB左右，那么将创建logs-000002索引，并更新logs_write别名以指向logs-000002。
```



## 新索引自定义命名

```
GET /_alias/logs
POST /logs/_rollover/my_new_index_name
{
  "conditions": {
    "max_docs":  1
  }
}
```



## 时序索引管理

使用Date Math根据索引滚动的日期来命名滚动索引，例如logstash-2016.02.03。索引rollover 支持Date 计算，但要求索引名以破折号和数字结尾，例如logstash-2016.02.03-1，每当索引被滚转时，该数字递增。例如:

```
# PUT /<logs-{now/d}-1> with URI encoding:
PUT /%3Clogs-%7Bnow%2Fd%7D-1%3E 
{
  "aliases": {
    "logs_write": {}
  }
}

PUT logs_write/_doc/1
{
  "message": "a dummy log"
}

POST logs_write/_refresh

# Wait for a day to pass
POST /logs_write/_rollover 
{
  "conditions": {
    "max_docs":   "1"
  }
}

滚动到带有今天日期的新索引，例如，如果立即运行，日志-2016.10.31-000002;如果24小时后运行，日志-2016.11.01-000002
```

然后可以按照date math文档中的描述引用这些索引。例如，要搜索过去三天创建的索引，您可以执行以下操作:

```
# GET /<logs-{now/d}-*>,<logs-{now/d-1d}-*>,<logs-{now/d-2d}-*>/_search
GET /%3Clogs-%7Bnow%2Fd%7D-*%3E%2C%3Clogs-%7Bnow%2Fd-1d%7D-*%3E%2C%3Clogs-%7Bnow%2Fd-2d%7D-*%3E/_search
```



## 自定义设置新索引

新索引的设置、映射和别名取自任何匹配的索引模板。另外，您可以在请求的主体中指定设置、映射和别名，就像create index一样。请求中指定的值将覆盖在匹配索引模板中设置的任何值。例如，下面的滚动请求将覆盖索引。number_of_shards设置:

```
PUT /logs-000001
{
  "aliases": {
    "logs_write": {}
  }
}

POST /logs_write/_rollover
{
  "conditions" : {
    "max_age": "7d",
    "max_docs": 1000,
    "max_size": "5gb"
  },
  "settings": {
    "index.number_of_shards": 2
  }
}
```



## dry_run（演示）

支持dry_run（演示）模式，在这种模式下，无需执行实际的翻转，就可以检查请求条件:

```
PUT /logs-000001
{
  "aliases": {
    "logs_write": {}
  }
}

POST /logs_write/_rollover?dry_run
{
  "conditions" : {
    "max_age": "7d",
    "max_docs": 1000,
    "max_size": "5gb"
  }
}
```



## 写索引行为

在滚动一个`is_write_index`显式设置为`true`的写索引时，滚动别名不会在滚动操作期间交换。由于将别名指向多个索引在区分哪一个是要滚动的正确写索引方面是不明确的，因此滚动指向多个索引的别名是无效的。因此，默认行为是交换面向写的别名指向的索引。

在上面的一些示例中，由于设置is_write_index使别名可以指向多个索引，同时还可以明确地确定滚动应该针对哪个写索引，因此没有必要从已滚动的索引中删除别名。通过设置一个别名同时作为使用滚动管理的索引的写别名和读别名，从而简化了滚动过程。

在下面的示例中查看别名的滚动，其中在滚过的索引上设置了is_write_index。

```
PUT my_logs_index-000001
{
  "aliases": {
    "logs": { "is_write_index": true } 
  }
}

PUT logs/_doc/1
{
  "message": "a dummy log"
}

POST logs/_refresh

POST /logs/_rollover
{
  "conditions": {
    "max_docs":   "1"
  }
}

PUT logs/_doc/2 
{
  "message": "a newer log"
}
```

滚动之后，两个索引的别名元数据将使用is_write_index设置来反映每个索引的角色，并使用新创建的索引作为写索引。

```
{
  "my_logs_index-000002": {
    "aliases": {
      "logs": { "is_write_index": true }
    }
  },
  "my_logs_index-000001": {
    "aliases": {
      "logs": { "is_write_index" : false }
    }
  }
}
```



# Shrink index

1、收缩索引允许将现有索引收缩为具有更少主分片的新索引。

2、目标索引中请求的主分片数量必须是源索引中分片数量的因数。

例如，一个有8个主分片的索引可以缩小到4、2或1个主分片，或者一个有15个主分片的索引可以缩小到5、3或1。如果索引中的分片数是质数，那么它只能收缩为一个主分片。在收缩之前，索引中每个分片的(主或副本)副本必须存在于同一个节点上。

> 收缩后的新索引处于写阻塞状态，需手动将其修改为读写状态
>
> ```
> PUT /target_index/_settings
> {
> "settings": {
> "index.blocks.write": null
> }
> }
> ```



## 收缩流程

1. 首先，它创建一个新的目标索引，其定义与源索引相同，但主分片的数量更少。
2. 然后，它将段从源索引硬链接到目标索引。(如果文件系统不支持硬链接，则将所有段复制到新索引中，这是一个非常耗时的过程。)
3. 最后，它恢复目标索引，就像它是一个刚刚重新打开的关闭索引一样。



## 收缩条件

索引只有满足以下要求时才能缩小:

- 目标索引必须不存在
- 索引必须比目标索引拥有更多的主分片。
- 目标索引中的主分片数量必须是源索引中的主分片数量的因数。源索引必须比目标索引拥有更多的主分片。
- 索引不能包含超过2,147,483,519个文档，这些文档将被压缩成目标索引上的单个分片，因为这是单个分片所能容纳的最大文档数。
- 处理收缩进程的节点必须有足够的空闲磁盘空间来容纳现有索引的第二个副本。



## 准备工作

为了缩小索引，必须将索引标记为只读，并且必须将索引中每个分片的(主或副本)副本重新定位到相同的节点，并保持绿色运行状态。

这两个条件可以通过以下请求来实现:

```
PUT /my_source_index/_settings
{
  "settings": {
    "index.routing.allocation.require._name": "shrink_node_name", //：强制将每个分片的副本重新定位到名称为shrink_node_name的节点。
    "index.blocks.write": true  //防止对该索引的写操作，同时仍然允许元数据更改，如删除索引。
  }
}
```

重新定位源索引可能需要一段时间。



## 收缩请求

要将my_source_index缩小为一个名为my_target_index的新索引，发出以下请求:

```
POST my_source_index/_shrink/my_target_index?copy_settings=true
{
  "settings": {
    "index.routing.allocation.require._name": null,  //清除从源索引复制的分配需求。
    "index.blocks.write": null 
  }
}
```

一旦目标索引被添加到集群状态，上面的请求立即返回—它不等待收缩操作开始。



## 自定义设置收缩请求

shrink请求接受目标索引的设置和别名参数:

```
POST my_source_index/_shrink/my_target_index?copy_settings=true
{
  "settings": {
    "index.number_of_replicas": 1,
    "index.number_of_shards": 1,   //目标索引中的分片数。这必须是源索引中分片数量的一个因素。
    "index.codec": "best_compression"   //最佳压缩仅在对索引进行新写操作时生效，例如将分片强制合并到单个段时。
  },
  "aliases": {
    "my_search_indices": {}
  }
}
```

> 映射不能在_shrink请求中指定。

> 默认情况下，除了`index.analysis`, `index.similarity`和`index.sort`设置外，在收缩操作期间不会复制源索引上的索引设置。除了不可复制的设置外，可以通过向请求添加URL参数copy_settings=true将源索引中的设置复制到目标索引中。注意，不能将copy_settings设置为false。参数copy_settings将在8.0.0中删除





## 监控收缩进程

恢复情况

```
GET _cat/recovery?v&index=es-7.7.0-2020.10.23.17.40
```

集群健康状况

```
GET _cluster/health
GET _cluster/health?wait_for_no_relocating_shards=true
```

新旧索引数量

```
GET my_target_index2/_count
GET es-7.7.0-2020.10.23.09.13/_count
```

一旦目标索引被添加到集群状态中，在分配任何分片之前，_shrink请求就会返回。此时，所有分片都处于未分配状态。如果由于任何原因，无法在收缩节点上分配目标索引，那么它的主分片将保持未分配状态，直到可以在该节点上分配它为止。

一旦分配了主分片，它就转移到状态初始化，并开始收缩过程。当收缩操作完成时，分片将成为活动分片。同时Elasticsearch将尝试分配副本，并可能决定将主分片重新定位到另一个节点。



## 等待活跃分片

因为收缩操作创建一个新索引来收缩 分片，所以在创建索引时的等待活动分片设置（`index.write.wait_for_active_shards`）也适用于收缩索引操作。



# Split index

1、拆分索引允许将现有索引拆分为新索引，其中，在新索引中，每个原始主分片被拆分为两个或多个主分片。

2、split要求用特定的`number_of_routing_shards`创建源索引，以便将来进行拆分。这个设置已经在Elasticsearch 7.0中删除。

3、索引可以拆分的次数(以及每个原始分片可以拆分成的分片的数量)由索引决定。设置参数为`index.number_of_routing_shards`。

4、分片的路由根据hash值进行分配。

例如，number_of_routing_shards设置为30 (5 x 2 x 3)的5分片索引可以被2或3的倍数拆分。换句话说，可以拆分为:

- 5→10→30(先除以2，再除以3)
- 5→15→30(先被3拆分，再被2拆分)
- 5→30(除以6)



## 拆分流程

1. 首先，它创建一个新的目标索引，其定义与源索引相同，但具有更多的主分片。
2. 然后，它将段从源索引硬链接到目标索引。(如果文件系统不支持硬链接，则将所有段复制到新索引中，这是一个非常耗时的过程。)
3. 创建低级文件后，所有文档将再次散列以删除属于不同 分片的文档。
4. 最后，它恢复目标索引，就像它是一个刚刚重新打开的关闭索引一样。



## 拆分条件

只有满足以下要求，索引才能被拆分:

- 目标索引必须不存在
- 索引的主分片必须少于目标索引。
- 目标索引中的主分片数量必须是源索引中的主分片数量的因数或倍数。
- 处理拆分进程的节点必须有足够的空闲磁盘空间来容纳现有索引的第二个副本。



## 为什么Elasticsearch不支持增量重新分片?

从N个分片到N+1个分片，也就是增量重新分片确实是许多K-V存储所支持的特性。

在添加新的分片的时候并将新数据推入这个新的分片是不可行的:这可能会成为索引瓶颈，并且在给定`_id`的情况下，确定文档属于哪个分片(get、delete和update请求必须使用`_id`)将变得相当复杂。这意味着需要使用不同的hash方案来重新平衡现有数据。

K-V存储高效实现此目的的最常见方法是使用一致的hash。当shard的数量从N增加到N+1时，一致性hash只需要重新分配1/N个键。然而Elasticsearch的存储单元shards是Lucene索引。由于其面向搜索的数据结构，在Lucene索引中占很大一部分，即使只有5%的文档，删除它们并在另一个分片上重新索引它们通常要比使用K-V存储花费高得多。

如上所述，当分片成倍增长时，此成本是合理的：这允许Elasticsearch在本地执行拆分，这进而允许在索引级别执行拆分，而不是通过索引 移动，以及使用硬链接进行有效的文件复制方式进行重新索引文档。

对于仅添加的数据，可以通过创建新索引并将新数据推入其中来获得更大的灵活性，同时为读操作添加一个覆盖旧索引和新索引的别名。假设旧索引和新索引分别有M和N个分片，这与搜索一个有M+N个分片的索引相比没有任何额外开销。



## 设置索引可拆分

创建一个带有路由分片因数的索引:

```
PUT my_source_index
{
    "settings": {
        "index.number_of_shards" : 1,
        "index.number_of_routing_shards" : 4   //允许将索引拆分成4的因数或倍数个分片，换句话说，它允许一次拆分操作。
    }
}
```



## 标记索引只读

为了拆分索引，索引必须标记为只读，并且运行状况为绿色。

```
PUT /my_source_index/_settings
{
  "settings": {
    "index.blocks.write": true  //防止对该索引的写操作，同时仍然允许元数据更改，如删除索引。
  }
}
```



## 拆分请求

要将my_source_index拆分为一个名为my_target_index的新索引，发出以下请求:

```
POST my_source_index/_split/my_target_index?copy_settings=true
{
  "settings": {
    "index.number_of_shards": 2
  }
}
```

一旦目标索引被添加到集群状态，上面的请求立即返回—它不等待拆分操作开始。



## 自定义拆分请求

自定义新索引设置：

```
POST my_source_index/_split/my_target_index?copy_settings=true
{
  "settings": {
    "index.number_of_shards": 5   //目标索引中的分片数。这必须是源索引中分片数量的一个因素。
  },
  "aliases": {
    "my_search_indices": {}
  }
}
```

Mapping不能在_split请求中指定。

> 默认情况下，除了`index.analysis`,` index.similarity`和`index.sort`设置之外，在拆分操作期间不会复制源索引上的索引设置。除了不可复制的设置外，可以通过向请求添加URL参数copy_settings=true将源索引中的设置复制到目标索引中。注意，不能将copy_settings设置为false。参数copy_settings将在8.0.0中删除



## 监控拆分进程

恢复情况

```
GET _cat/recovery?v&index=es-7.7.0-2020.10.23.17.40
```

集群健康状况

```
GET _cluster/health
GET _cluster/health?wait_for_status=yellow
GET _cluster/health?wait_for_no_relocating_shards=true
```

新旧索引数量

```
GET my_target_index2/_count
GET es-7.7.0-2020.10.23.09.13/_count
```

一旦目标索引被添加到集群状态中，在分配任何分片之前，`_split`请求就返回。此时，所有分片都处于unassigned状态。如果由于任何原因无法分配目标索引，它的主分片将保持unassigned状态，直到可以在该节点上分配它为止。

一旦分配了主分片，它就转移到状态initializing，拆分过程就开始了。当拆分操作完成时，分片将变为active。同时，Elasticsearch将尝试分配副本，并可能决定是否将主分片重新定位到另一个节点。

## 等待活跃分片

因为拆分操作创建了一个新索引来拆分 分片，所以在创建索引时等待活动 分片设置（index.write.wait_for_active_shards）也适用于拆分索引操作。



推荐阅读：

https://www.elastic.co/cn/blog/managing-time-based-indices-efficiently