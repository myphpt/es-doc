# 索引恢复

索引恢复提供了对正在进行的索引分片恢复的洞察。恢复状态可以针对特定的索引报告，也可以在集群范围内报告。



## 恢复列表

recovery命令是索引分片恢复的视图，包括正在进行的和已经完成的。

```
GET _cat/recovery?v
```



## 获取恢复信息

```
GET index1,index2/_recovery?human
GET /_recovery?human
```

## 响应

该索引总大小130M，有5个主分片

```
{
  "es-7.7.0-2020.10.23.11.50" : {
    "shards" : [
      {
        "id" : 3,   
        "type" : "EXISTING_STORE",   
        "stage" : "DONE",    
        "primary" : true,   
        "start_time" : "2020-10-23T06:56:58.414Z",  
        "start_time_in_millis" : 1603436218414,
        "stop_time" : "2020-10-23T06:56:58.533Z",
        "stop_time_in_millis" : 1603436218533,
        "total_time" : "119ms",     
        "total_time_in_millis" : 119,
        "source" : {
          "bootstrap_new_history_uuid" : false
        },
        "target" : {
          "id" : "B-M3lfhbQfS88kIq64pECQ",
          "host" : "10.253.4.67",
          "transport_address" : "10.253.4.67:9300",
          "ip" : "10.253.4.67",
          "name" : "node02"
        },
        "index" : {
          "size" : {
            "total" : "26.2mb",
            "total_in_bytes" : 27533706,
            "reused" : "26.2mb",
            "reused_in_bytes" : 27533706,
            "recovered" : "0b",
            "recovered_in_bytes" : 0,
            "percent" : "100.0%"
          },
          "files" : {
            "total" : 67,
            "reused" : 67,
            "recovered" : 0,
            "percent" : "100.0%"
          },
          "total_time" : "10ms",
          "total_time_in_millis" : 10,
          "source_throttle_time" : "-1",
          "source_throttle_time_in_millis" : 0,
          "target_throttle_time" : "-1",
          "target_throttle_time_in_millis" : 0
        },
        "translog" : {
          "recovered" : 0,
          "total" : 0,
          "percent" : "100.0%",
          "total_on_start" : 0,
          "total_time" : "100ms",
          "total_time_in_millis" : 100
        },
        "verify_index" : {
          "check_index_time" : "0s",
          "check_index_time_in_millis" : 0,
          "total_time" : "0s",
          "total_time_in_millis" : 0
        }
      },
     。。。

```



## 详细信息

```
GET es-7.7.0-2020.10.23.11.50/_recovery?human&detailed=true
```

与以上信息相似



## 正在进行的恢复

```
GET _recovery?human&active_only=true
```



## 响应解析

| 字段                   | 描述                                                         |
| ---------------------- | ------------------------------------------------------------ |
| `id`                   | Shard ID                                                     |
| `type`                 | 恢复类型：                                                                                                                1、store                                                                                                                    2、snapshot                                                                                                             3、replica                                                                                                                 4、 relocating |
| `stage`                | 恢复阶段:                                                                                                                  init:    初始化                                                                                                              index:    读取索引元数据并将数据从源复制到目标                                                                    start:    开启索引，并提供使用                                                                                translog: 回放事务日志                                                                                            finalize: 清理                                                                                                         done:     完成 |
| `primary`              | 是否主分片                                                   |
| `start_time`           | 恢复开始时间                                                 |
| `stop_time`            | 恢复结束时间                                                 |
| `total_time_in_millis` | 恢复耗时                                                     |
| `source`               | 恢复源:                                                                                                                                     存储库描述：如果是从快照恢复的话                                                                                     源节点描述 |
| `target`               | 目标节点                                                     |
| `index`                | 关于物理索引恢复的统计信息                                   |
| `translog`             | 关于事务日志恢复的统计信息                                   |
| `start`                | 关于打开和启动索引时间的统计信息                             |



## 高级设置

可以设置以下专家设置来管理恢复策略。（动态更新）

```
PUT _cluster/settings
{
  "transient": {
    "indices.recovery.max_bytes_per_sec": "40mb"
  }
}

默认 40mb. 
```

# 本地分片恢复

该模块在整个集群重启期间存储集群状态和分片数据。

本地网关模块在整个集群重启期间存储集群状态和分片数据。

> 该模块配置一般用于大型集群

以下静态设置，必须在每个主节点上设置，控制一个新选出的主应该等待多长时间，在它试图恢复集群状态和集群的数据:

```
gateway.expected_nodes 
预计在集群中的(数据或主)节点的数量。一旦预期数量的节点加入集群，本地分片的恢复就会开始。默认值为0

gateway.expected_master_nodes 
预计在集群中的主节点的数量。一旦预期的主节点数量加入集群，本地分片的恢复就会开始。默认值为0

gateway.expected_data_nodes 
预期在集群中的数据节点的数量。一旦预期数量的数据节点加入集群，本地分片的恢复就会开始。默认值为0

gateway.recover_after_time 
如果没有达到预期的节点数量，恢复进程将等待配置的时间，然后再尝试恢复，这与恢复无关。如果配置了expected_nodes设置之一，则默认为5m。
```

一旦recover_after_time持续时间超时，只要满足以下条件，恢复就会启动:

```
gateway.recover_after_nodes 
要有这么多数据或主节点加入集群，就可以恢复。

gateway.recover_after_master_nodes 
只要这么多主节点加入了集群，就可以恢复。

gateway.recover_after_data_nodes 
只要有这么多数据节点加入集群，就可以恢复。
```

这些设置只在完整的集群重新启动时生效。



# 事务日志

对Lucene的更改只会在Lucene提交期间持久化到磁盘上，这是一个相对昂贵的操作，因此不能在每次索引或删除操作之后执行。当进程退出或硬件出现故障时，在一次提交之后或之前发生的更改将被Lucene从索引中删除。

因为Lucene提交的开销太大，无法在每个单独的更改上执行，所以每个分片副本都有一个与之关联的事务日志，称为translog。所有的索引和删除操作在被内部Lucene索引处理之后，但是在它们被确认之前，都被写到translog中。在崩溃的情况下，当分片恢复时，已经确认但在上次Lucene提交中还没有包含的最近事务可以从translog中恢复。

Elasticsearch刷新是执行Lucene提交并启动新的跨日志的过程。刷新是在后台自动执行的，以确保translog不会增长得太大，否则在恢复过程中会花费相当长的时间来重播它的操作。手动执行刷新的能力也通过API公开，尽管很少需要这样做。

默认情况下，如果Elasticsearch每5秒进行fsyncs和提交translog。持久性设置为async，或者在每个索引、删除、更新或批量请求的末尾设置为request(默认)。

更准确地说，如果设置为request, Elasticsearch只会在跨日志在主服务器和每个分配的副本上成功地同步并提交之后，向客户端报告索引、删除、更新或批量请求的成功。

```
index.translog.sync_interval
	translog多长时间同步到磁盘并提交一次，而不考虑写操作。默认为5s。不允许小于100ms。

index.translog.durability 
	是否在每个索引、删除、更新或批量请求后fsync和提交translog。此设置接受以下参数:
	request (默认)fsync和提交后，每个请求。在发生硬件故障时，所有已确认的写操作都已提交到磁盘。
	async：fsync和在后台提交每个sync_interval。在发生硬件故障时，自上次自动提交以来所有已确认的写操作都将被丢弃。

index.translog.flush_threshold_size 
	translog存储了所有还没有安全地保存在Lucene中的操作(也就是说，它们不是Lucene提交点的一部分)。尽管这些操作可用于读取，但如果分片要关闭并必须恢复，则需要对它们重新建立索引。此设置控制这些操作的最大总大小，以防止恢复时间过长。一旦达到最大大小，刷新就会发生，生成一个新的Lucene提交点。默认为512 mb。

index.translog.retention.size 
	要保存的跨日志文件的总大小。在恢复副本时，保留更多的translog文件会增加执行基于同步操作的机会。如果translog文件不够，复制恢复将退回到基于文件的同步。默认为512 mb。7.4后不建议设置，未来会被废弃

index.translog.retention.age 
	保存translog文件的最大持续时间。默认为12h。7.4后不建议设置，未来会被废弃
```

可以考虑的优化设置：

```
    "settings": {
          "translog": {
            "flush_threshold_size": "1gb",//内容容量到达1gb异步刷新
            "sync_interval": "30s",//间隔30s异步刷新（设置后无法更改）
            "durability": "async"//异步刷新
          }
        }
      }
```



