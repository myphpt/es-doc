[TOC]

# Cluster（集群）

## health（健康状态）

查看健康状态

```
GET /_cat/health?v
```

响应内容

```
响应内容：
[
  {
    "epoch" : "1604385398",
    "timestamp" : "06:36:38",
    "cluster" : "es65",
    "status" : "yellow",
    "node.total" : "1",
    "node.data" : "1",
    "shards" : "1340",
    "pri" : "1340",
    "relo" : "0",
    "init" : "0",
    "unassign" : "40",
    "pending_tasks" : "0",
    "max_task_wait_time" : "-",
    "active_shards_percent" : "97.1%"
  }
]
```

禁用时间戳查看

```
GET /_cat/health?v&ts=false
```

跟踪集群恢复状态

```
% while true; do curl localhost:9200/_cat/health; sleep 120; done
```

如果恢复的情况持续几个小时，我们将能够看到未分配的碎片急剧下降。如果这个数字保持不变，我们就会认为出现了问题。



## Cluster Health（集群健康）

```
GET _cluster/health
GET /_cluster/health/es-7.7.0-2020.10.23.09.14
```

如果在50秒内集群到达黄色级别则返回(如果在50秒前到达绿色或黄色状态，此时返回)：

```
GET /_cluster/health?wait_for_status=yellow&timeout=50s
```

返回分片级别的信息

```
GET /_cluster/health/twitter?level=shards
```

响应

```
{
  "cluster_name" : "es65",
  "status" : "yellow",
  "timed_out" : false,
  "number_of_nodes" : 1,
  "number_of_data_nodes" : 1,
  "active_primary_shards" : 1113,
  "active_shards" : 1113,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 10,
  "delayed_unassigned_shards" : 0,
  "number_of_pending_tasks" : 0,
  "number_of_in_flight_fetch" : 0,
  "task_max_waiting_in_queue_millis" : 0,
  "active_shards_percent_as_number" : 99.10952804986643
}
```

请求参数

| 参数                            | 描述                                                         |
| ------------------------------- | ------------------------------------------------------------ |
| level                           | 可以是`cluster`, `indices` 或 `shards`之一。控制返回的运行状况信息的详细信息级别。默认为cluster。 |
| wait_for_status                 | `green`, `yellow `或`red`。将等待(直到提供超时)，直到集群状态更改为所提供的状态或更好的状态，即绿色>黄色>红色。默认情况下，不会等待任何状态。 |
| wait_for_no_relocating_shards   | 一个布尔值，用于控制是否等待(直到提供超时)集群不进行分片重定位。默认值为false，这意味着它不会等待重新定位碎片。 |
| wait_for_no_initializing_shards | 一个布尔值，用于控制是否等待(直到提供超时)集群不进行分片初始化。默认值为false，这意味着它将不等待初始化分片。 |
| wait_for_active_shards          | 一个数字，用于控制要等待的活动分片数，all表示要等待集群中所有的活动分片数，或0表示不等待。 默认值为0。 |
| wait_for_nodes                  | 请求一直等待，直到指定的N个节点可用为止。它也接受>=N， <=N， >N和<N。或者，也可以使用ge(N)、le(N)、gt(N)和lt(N)表示法。 |
| timeout                         | 一个基于时间的参数，如果提供了一个wait_for_XXX，则控制等待的时间。默认为30s。 |
| master_timeout                  | 一个基于时间的参数，用于控制在主服务器未被发现或未断开连接时等待的时间。如果没有提供，则使用与超时相同的值。 |
| local                           | 如果为真，则返回本地节点信息，并且不提供来自主节点的状态。默认值:false。 |



## Cluster Stats（集群统计）

允许从整个集群的角度检索统计信息。这个API返回基本的索引指标(分片数、存储大小、内存使用情况)和关于当前集群节点的信息(数量、角色、操作系统、jvm版本、内存使用情况、cpu和已安装的插件)。

```
GET /_cluster/stats?human&pretty
GET /_cluster/stats/nodes/{nodename}
```

响应

```
{
  "_nodes" : {
    "total" : 1,
    "successful" : 1,
    "failed" : 0
  },
  "cluster_name" : "es65",
  "cluster_uuid" : "k0kyodg6RrW5oIOABft_9w",
  "timestamp" : 1603445586119,
  "status" : "yellow",
  "indices" : {
    "count" : 233,
    "shards" : {
      "total" : 1133,
      "primaries" : 1133,
      "replication" : 0.0,
      "index" : {
        "shards" : {
          "min" : 1,
          "max" : 5,
          "avg" : 4.8626609442060085
        },
        "primaries" : {
          "min" : 1,
          "max" : 5,
          "avg" : 4.8626609442060085
        },
        "replication" : {
          "min" : 0.0,
          "max" : 0.0,
          "avg" : 0.0
        }
      }
    },
    "docs" : {
      "count" : 90330372,
      "deleted" : 16459
    },
    "store" : {
      "size" : "29.9gb",
      "size_in_bytes" : 32199971793
    },
    "fielddata" : {
      "memory_size" : "1.7kb",
      "memory_size_in_bytes" : 1776,
      "evictions" : 0
    },
    "query_cache" : {
      "memory_size" : "7.5kb",
      "memory_size_in_bytes" : 7768,
      "total_count" : 28085,
      "hit_count" : 6964,
      "miss_count" : 21121,
      "cache_size" : 9,
      "cache_count" : 22,
      "evictions" : 13
    },
    "completion" : {
      "size" : "0b",
      "size_in_bytes" : 0
    },
    "segments" : {
      "count" : 8111,
      "memory" : "136mb",
      "memory_in_bytes" : 142655371,
      "terms_memory" : "112.9mb",
      "terms_memory_in_bytes" : 118426350,
      "stored_fields_memory" : "11.6mb",
      "stored_fields_memory_in_bytes" : 12234696,
      "term_vectors_memory" : "0b",
      "term_vectors_memory_in_bytes" : 0,
      "norms_memory" : "4.9mb",
      "norms_memory_in_bytes" : 5162048,
      "points_memory" : "1.5mb",
      "points_memory_in_bytes" : 1653993,
      "doc_values_memory" : "4.9mb",
      "doc_values_memory_in_bytes" : 5178284,
      "index_writer_memory" : "4.5mb",
      "index_writer_memory_in_bytes" : 4727320,
      "version_map_memory" : "0b",
      "version_map_memory_in_bytes" : 0,
      "fixed_bit_set" : "82.4kb",
      "fixed_bit_set_memory_in_bytes" : 84392,
      "max_unsafe_auto_id_timestamp" : 1603445527277,
      "file_sizes" : { }
    }
  },
  "nodes" : {
    "count" : {
      "total" : 1,
      "data" : 1,
      "coordinating_only" : 0,
      "master" : 1,
      "ingest" : 1
    },
    "versions" : [
      "6.5.0"
    ],
    "os" : {
      "available_processors" : 4,
      "allocated_processors" : 4,
      "names" : [
        {
          "name" : "Linux",
          "count" : 1
        }
      ],
      "mem" : {
        "total" : "5.8gb",
        "total_in_bytes" : 6256037888,
        "free" : "109.6mb",
        "free_in_bytes" : 114999296,
        "used" : "5.7gb",
        "used_in_bytes" : 6141038592,
        "free_percent" : 2,
        "used_percent" : 98
      }
    },
    "process" : {
      "cpu" : {
        "percent" : 29
      },
      "open_file_descriptors" : {
        "min" : 9262,
        "max" : 9262,
        "avg" : 9262
      }
    },
    "jvm" : {
      "max_uptime" : "2.6h",
      "max_uptime_in_millis" : 9396946,
      "versions" : [
        {
          "version" : "1.8.0_241",
          "vm_name" : "Java HotSpot(TM) 64-Bit Server VM",
          "vm_version" : "25.241-b07",
          "vm_vendor" : "Oracle Corporation",
          "count" : 1
        }
      ],
      "mem" : {
        "heap_used" : "1.6gb",
        "heap_used_in_bytes" : 1776885000,
        "heap_max" : "2.9gb",
        "heap_max_in_bytes" : 3186360320
      },
      "threads" : 78
    },
    "fs" : {
      "total" : "147.5gb",
      "total_in_bytes" : 158399414272,
      "free" : "54.1gb",
      "free_in_bytes" : 58135285760,
      "available" : "46.6gb",
      "available_in_bytes" : 50065444864
    },
    "plugins" : [ ],
    "network_types" : {
      "transport_types" : {
        "security4" : 1
      },
      "http_types" : {
        "security4" : 1
      }
    }
  }
}
```



## Cluster State（集群状态）

允许获得整个集群的全面状态信息。

```
GET /_cluster/state?human&pretty=true&flat_settings=true
```

响应提供集群名称、集群状态的总压缩大小(序列化以便在网络上传输时的大小)和集群状态本身，可以对其进行筛选，以只检索感兴趣的部分。

除了元数据部分之外，集群的cluster_uuid也作为顶级响应的一部分返回。(6.4.0)。当集群仍在形成时，cluster_uuid可能是_na_，集群状态的版本可能是-1。

默认情况下，集群状态请求被路由到主节点，以确保返回最新的集群状态。出于调试的目的，可以通过向查询字符串添加local=true来检索特定节点的本地集群状态。

```
GET /_cluster/state/{metrics}/{indices}
GET /_cluster/state/metadata,routing_table/foo,bar
GET /_cluster/state/_all/{index_name}
GET /_cluster/state/blocks
```

响应Json的主节点：

| 节点          | 描述                                                         |
| ------------- | ------------------------------------------------------------ |
| version       | 显示集群状态版本。                                           |
| master_node   | 显示响应的master_node部分                                    |
| nodes         | 显示响应的nodes部分                                          |
| routing_table | 显示响应的routing_table部分。如果您提供一个以逗号分隔的索引列表，则返回的输出将只包含列出的索引。 |
| metadata      | 显示响应的metadata部分。如果您提供一个以逗号分隔的索引列表，则返回的输出将只包含列出的索引。 |
| blocks        | 显示响应的blocks部分                                         |

# Allocation（分配）

## allocation（空间分配）

提供一个快照，显示为每个数据节点分配了多少分片，以及它们使用了多少磁盘空间。

```
GET /_cat/allocation?v
```

响应

```
shards disk.indices disk.used disk.avail disk.total disk.percent host        ip          node
  1296       36.7gb    50.6gb     96.8gb    147.5gb           34 192.168.0.1 192.168.0.1 node02
    26                                                                                   UNASSIGNED
```

集群为单节点集群，node选项提示有26个分片未分配



## fielddata（元数据占用堆内存）

fielddata显示集群中每个数据节点上的fielddata当前使用了多少堆内存。

```
GET /_cat/fielddata?v

id                     host        ip          node   field size
B-M3lfhbQfS88kIq64pECQ 192.168.0.1 192.168.0.1 node02 type  552b
```

显示单个字段所占用的内存空间

```
GET /_cat/fielddata?v&fields=type
```



## count（活动文档计数）

```
GET /_cat/count?v
GET /_cat/count/twitter?v
```

文档计数表示活动文档的数量，不包括尚未被合并进程清理的已删除文档。

响应格式

```
epoch      timestamp count
1603765843 02:30:43  109846234
```



## Cluster Allocation Explain

对集群中的分片分配提供解释。对于未分配的分片，提供解释说明为什么该分片未分配。对于已分配的分片，提供解释，说明为什么切分保留在当前节点上，而没有移动或重新平衡到另一个节点。当试图诊断为什么没有分配一个分片，或者为什么分片在您可能期望的情况下仍然保留在当前节点上时，这个API非常有用。

```
GET /_cluster/allocation/explain
{
  "index": "myindex",
  "shard": 0,
  "primary": true
}
```

当前节点

```
GET /_cluster/allocation/explain
{
  "index": "myindex",
  "shard": 0,
  "primary": false,
  "current_node": "nodeA"       //碎片0当前具有副本的节点                   
}
```

查询集群中第一个未分配分片解释信息

```
GET /_cluster/allocation/explain
```

包含磁盘信息

```
GET /_cluster/allocation/explain?human&include_disk_info=true
```

包含决策信息（大量冗余）

```
GET /_cluster/allocation/explain?include_yes_decisions=true
```

# Node（节点）

## Node specification（节点规范说明）

一些集群级命令可以对节点的子集进行操作，可以用节点筛选器指定这些子集。例如，任务管理、节点状态和节点信息都可以报告一组经过筛选的节点的结果，而不是所有节点的结果。

```
# 没有给出过滤器，默认选择所有节点
GET /_nodes

# 选择所有节点
GET /_nodes/_all

# 选择本地节点
GET /_nodes/_local

# 选择主节点
GET /_nodes/_master

# 通过节点名选择节点，支持通配符
GET /_nodes/node_name_goes_here
GET /_nodes/node_name_goes_*

# 通过IP选择节点，支持通配符
GET /_nodes/10.0.0.3,10.0.0.4
GET /_nodes/10.0.0.*

# 通过角色选择节点
GET /_nodes/_all,master:false
GET /_nodes/data:true,ingest:true
GET /_nodes/coordinating_only:true

# 通过自定义属性选择节点 (e.g. with something like `node.attr.rack: 2` in the configuration file)
GET /_nodes/rack:2
GET /_nodes/ra*:2
GET /_nodes/ra*:2*
```



## master（主节点基本信息）

master没有任何额外的选项。它只是显示主机的节点ID、绑定的IP地址和节点名称。

```
GET /_cat/master?format=json
```

响应：

```
[
  {
    "id" : "B-M3lfhbQfS88kIq64pECQ",
    "host" : "192.168.0.1",
    "ip" : "192.168.0.1",
    "node" : "node02"
  }
]
```



## nodeattrs（节点属性）

nodeattrs命令显示定制的节点属性。

```
GET /_cat/nodeattrs?v
```

前几列(节点、主机、ip)为每个节点提供基本信息，attr和value列为自定义节点属性，每行一个。

查看指定属性

```
GET /_cat/nodeattrs?v&h=name,pid,attr,value
```

| Header  | Alias        | Appear by Default | Description          | Example   |
| :------ | :----------- | :---------------- | :------------------- | :-------- |
| `node`  | `name`       | Yes               | 节点名称             | DKDM97B   |
| `id`    | `nodeId`     | No                | 唯一 node ID         | k0zy      |
| `pid`   | `p`          | No                | Process ID           | 13061     |
| `host`  | `h`          | Yes               | Host name            | n1        |
| `ip`    | `i`          | Yes               | IP address           | 127.0.1.1 |
| `port`  | `po`         | No                | 绑定的transport port | 9300      |
| `attr`  | `attr.name`  | Yes               | Attribute name       | rack      |
| `value` | `attr.value` | Yes               | Attribute value      | rack123   |



## nodes（节点信息）

显示集群拓扑，各个节点的相关信息

```
GET /_cat/nodes?v
```

响应格式

```
ip          heap.percent ram.percent cpu load_1m load_5m load_15m node.role master name
192.168.0.1           47          98   1    0.07    0.21     0.17 mdi       *      node02
```

前几列(ip、heap百分比、ram百分比、cpu、load_*)告诉您节点的位置，并提供性能统计。

最后(node.role、master和name列提供辅助信息，在查看整个集群(尤其是大型集群)时，这些信息通常非常有用。比如我有多少主节点。

是否显示全部ID

```
GET /_cat/nodes?v&h=id,ip,port,v,m&full_id=true
```

显示全部字段

```
GET /_cat/nodes?v&h=*&format=json&human
```

响应：

```
[
  {
    "id" : "B-M3",
    "pid" : "3805",
    "ip" : "192.168.0.1",
    "port" : "9300",
    "http_address" : "192.168.0.1:9200",
    "version" : "6.5.0",
    "flavor" : "default",
    "type" : "tar",
    "build" : "816e6f6",
    "jdk" : "1.8.0_241",
    "disk.total" : "147.5gb",
    "disk.used" : "101gb",
    "disk.avail" : "46.5gb",
    "disk.used_percent" : "68.47",
    "heap.current" : "1.3gb",
    "heap.percent" : "46",
    "heap.max" : "2.9gb",
    "ram.current" : "5.6gb",
    "ram.percent" : "97",
    "ram.max" : "5.8gb",
    "file_desc.current" : "26921",
    "file_desc.percent" : "20",
    "file_desc.max" : "131072",
    "cpu" : "3",
    "load_1m" : "0.52",
    "load_5m" : "0.40",
    "load_15m" : "0.26",
    "uptime" : "1.9h",
    "node.role" : "mdi",
    "master" : "*",
    "name" : "node02",
    "completion.size" : "0b",
    "fielddata.memory_size" : "552b",
    "fielddata.evictions" : "0",
    "query_cache.memory_size" : "0b",
    "query_cache.evictions" : "0",
    "request_cache.memory_size" : "1.6kb",
    "request_cache.evictions" : "0",
    "request_cache.hit_count" : "666",
    "request_cache.miss_count" : "2",
    "flush.total" : "1411",
    "flush.total_time" : "311ms",
    "get.current" : "0",
    "get.time" : "162ms",
    "get.total" : "1340",
    "get.exists_time" : "112ms",
    "get.exists_total" : "673",
    "get.missing_time" : "50ms",
    "get.missing_total" : "667",
    "indexing.delete_current" : "0",
    "indexing.delete_time" : "0s",
    "indexing.delete_total" : "0",
    "indexing.index_current" : "0",
    "indexing.index_time" : "1.2m",
    "indexing.index_total" : "1269704",
    "indexing.index_failed" : "0",
    "merges.current" : "0",
    "merges.current_docs" : "0",
    "merges.current_size" : "0b",
    "merges.total" : "164",
    "merges.total_docs" : "2373182",
    "merges.total_size" : "695.8mb",
    "merges.total_time" : "1m",
    "refresh.total" : "5987",
    "refresh.time" : "44.8s",
    "refresh.listeners" : "0",
    "script.compilations" : "4",
    "script.cache_evictions" : "0",
    "search.fetch_current" : "0",
    "search.fetch_time" : "380ms",
    "search.fetch_total" : "4718",
    "search.open_contexts" : "0",
    "search.query_current" : "0",
    "search.query_time" : "865ms",
    "search.query_total" : "4784",
    "search.scroll_current" : "0",
    "search.scroll_time" : "0s",
    "search.scroll_total" : "0",
    "segments.count" : "9606",
    "segments.memory" : "181.2mb",
    "segments.index_writer_memory" : "0b",
    "segments.version_map_memory" : "0b",
    "segments.fixed_bitset_memory" : "1.5mb",
    "suggest.current" : "0",
    "suggest.time" : "0s",
    "suggest.total" : "0"
  }
]
```



## Nodes Stats（节点统计）

允许检索一个或多个(或全部)集群节点的统计信息。

```
GET /_nodes/stats?human&pretty
GET /_nodes/nodeId1,nodeId2/stats
```

包含指定信息

```
GET /_nodes/stats/indices?human&pretty
GET /_nodes/stats/os,process
GET /_nodes/10.0.0.1/stats/process
```

所有字段：indices、fs、http、jvm、os、process、thread_pool、transport、breaker、discovery、ingest、adaptive_selection（自适应副本的选择，根据设置的副本选择最佳的搜索策略）

### 文件系统（fs）

```
GET /_nodes/stats/fs?human&pretty
```

响应

```
{
  "_nodes" : {
    "total" : 1,
    "successful" : 1,
    "failed" : 0
  },
  "cluster_name" : "es65",
  "nodes" : {
    "B-M3lfhbQfS88kIq64pECQ" : {
      "timestamp" : 1603784688049,
      "name" : "node02",
      "transport_address" : "192.168.0.1:9300",
      "host" : "192.168.0.1",
      "ip" : "192.168.0.1:9300",
      "roles" : [
        "master",
        "data",
        "ingest"
      ],
      "attributes" : {
        "ml.machine_memory" : "6256037888",
        "xpack.installed" : "true",
        "ml.max_open_jobs" : "20",
        "ml.enabled" : "true"
      },
      "fs" : {
        "timestamp" : 1603784688049,   //最近一次文件系统统计刷新的时间
        "total" : {
          "total" : "147.5gb",    //文件系统总大小
          "total_in_bytes" : 158399414272,
          "free" : "103.8gb",     //空闲
          "free_in_bytes" : 111544238080,
          "available" : "96.3gb",   //可用
          "available_in_bytes" : 103474397184
        },
        "least_usage_estimate" : {
          "path" : "/opt/elastic/elasticsearch-6.5.0/data/nodes/0",
          "total" : "147.5gb",
          "total_in_bytes" : 158399414272,
          "available" : "96.3gb",
          "available_in_bytes" : 103477952512,
          "used_disk_percent" : 34.672768212191784
        },
        "most_usage_estimate" : {
          "path" : "/opt/elastic/elasticsearch-6.5.0/data/nodes/0",
          "total" : "147.5gb",
          "total_in_bytes" : 158399414272,
          "available" : "96.3gb",
          "available_in_bytes" : 103477952512,
          "used_disk_percent" : 34.672768212191784
        },
        "data" : [   //所有文件存储的列表
          {
            "path" : "/opt/elastic/elasticsearch-6.5.0/data/nodes/0",
            "mount" : "/opt (/dev/sdb)",
            "type" : "ext4",
            "total" : "147.5gb",
            "total_in_bytes" : 158399414272,
            "free" : "103.8gb",
            "free_in_bytes" : 111544238080,
            "available" : "96.3gb",
            "available_in_bytes" : 103474397184
          }
        ],
        "io_stats" : {
          "devices" : [
            {
              "device_name" : "sdb",
              "operations" : 243909,
              "read_operations" : 152239,
              "write_operations" : 91670,
              "read_kilobytes" : 36075760,
              "write_kilobytes" : 5976780
            }
          ],
          "total" : {
            "operations" : 243909,
            "read_operations" : 152239,
            "write_operations" : 91670,
            "read_kilobytes" : 36075760,
            "write_kilobytes" : 5976780
          }
        }
      }
    }
  }
}

```



### 内存

```
GET /_nodes/stats/os?human&pretty
```

响应

```
{
  "_nodes" : {
    "total" : 1,
    "successful" : 1,
    "failed" : 0
  },
  "cluster_name" : "es65",
  "nodes" : {
    "B-M3lfhbQfS88kIq64pECQ" : {
      "timestamp" : 1603784991984,
      "name" : "node02",
      "transport_address" : "192.168.0.1:9300",
      "host" : "192.168.0.1",
      "ip" : "192.168.0.1:9300",
      "roles" : [
        "master",
        "data",
        "ingest"
      ],
      "attributes" : {
        "ml.machine_memory" : "6256037888",
        "xpack.installed" : "true",
        "ml.max_open_jobs" : "20",
        "ml.enabled" : "true"
      },
      "os" : {
        "timestamp" : 1603784991022,
        "cpu" : {
          "percent" : 1,  //最近整个系统的CPU使用量，如果不支持，则为-1
          "load_average" : {  
            "1m" : 0.01,  //系统上的一分钟平均负载(如果一分钟平均负载不可用，则不存在此字段)
            "5m" : 0.03,
            "15m" : 0.05
          }
        },
        "mem" : {
          "total" : "5.8gb",   //物理内存总量
          "total_in_bytes" : 6256037888,
          "free" : "201.3mb",
          "free_in_bytes" : 211091456,
          "used" : "5.6gb",
          "used_in_bytes" : 6044946432,
          "free_percent" : 3,   //可用内存百分比
          "used_percent" : 97
        },
        "swap" : {
          "total" : "819.9mb",   //交换空间总量
          "total_in_bytes" : 859828224,
          "free" : "808.4mb",
          "free_in_bytes" : 847761408,
          "used" : "11.5mb",
          "used_in_bytes" : 12066816
        },
        "cgroup" : {
          "cpuacct" : {
            "control_group" : "/",
            "usage_nanos" : 1549473094112   //同一cgroup中所有任务在Elasticsearch过程中消耗的总CPU时间(以纳秒为单位)
          },
          "cpu" : {
            "control_group" : "/",   //Elasticsearch进程所属的cpu控制组
            "cfs_period_micros" : 100000,  
            "cfs_quota_micros" : -1,
            "stat" : {
              "number_of_elapsed_periods" : 0,
              "number_of_times_throttled" : 0,
              "time_throttled_nanos" : 0
            }
          },
          "memory" : {
            "control_group" : "/",
            "limit_in_bytes" : "9223372036854771712",
            "usage_in_bytes" : "5601808384"
          }
        }
      }
    }
  }
}

```

### 进程

```
GET /_nodes/stats/process?human&pretty
```

响应

```
{
  "_nodes" : {
    "total" : 1,
    "successful" : 1,
    "failed" : 0
  },
  "cluster_name" : "es65",
  "nodes" : {
    "B-M3lfhbQfS88kIq64pECQ" : {
      "timestamp" : 1603785283470,
      "name" : "node02",
      "transport_address" : "192.168.0.1:9300",
      "host" : "192.168.0.1",
      "ip" : "192.168.0.1:9300",
      "roles" : [
        "master",
        "data",
        "ingest"
      ],
      "attributes" : {
        "ml.machine_memory" : "6256037888",
        "xpack.installed" : "true",
        "ml.max_open_jobs" : "20",
        "ml.enabled" : "true"
      },
      "process" : {
        "timestamp" : 1603785283471,
        "open_file_descriptors" : 6789,
        "max_file_descriptors" : 131072,
        "cpu" : {
          "percent" : 4,
          "total" : "23.5m",
          "total_in_millis" : 1412200
        },
        "mem" : {
          "total_virtual" : "43.7gb",  //提供对正在运行的进程可用的虚拟内存的大小
          "total_virtual_in_bytes" : 46930673664
        }
      }
    }
  }
}

```



### 索引统计

```
# fielddata
GET /_nodes/stats/indices/fielddata?human&pretty

# level=indices
GET /_nodes/stats/indices/fielddata?level=indices

# level=shards
GET /_nodes/stats/indices/fielddata?level=shards

# field
GET /_nodes/stats/indices/fielddata?fields=field*
```



### 指标名称

支持的指标名称：

- `completion` 
- `docs` 
- `fielddata` 
- `flush` 
- `get` 
- `indexing` 
- `merge` 
- `query_cache` 
- `recovery` 
- `refresh` 
- `request_cache` 
- `search` 
- `segments` 
- `store` 
- `translog` 
- `warmer` 



### 搜索组

```
GET /_nodes/stats?groups=_all
GET /_nodes/stats/indices?groups=foo,bar
```



## Nodes Info

允许检索一个或多个(或全部)集群节点信息。

```
GET /_nodes
GET /_nodes/nodeId1,nodeId2
```

基本信息

```
  "nodes" : {
    "B-M3lfhbQfS88kIq64pECQ" : {
      "name" : "node02",
      "transport_address" : "192.168.0.1:9300",
      "host" : "192.168.0.1",
      "ip" : "192.168.0.1",
      "version" : "6.5.0",
      "build_flavor" : "default",
      "build_type" : "tar",
      "build_hash" : "816e6f6",
      "total_indexing_buffer" : 318636032,
      "roles" : [
        "master",
        "data",
        "ingest"
      ],
      "attributes" : {
        "ml.machine_memory" : "6256037888",
        "xpack.installed" : "true",
        "ml.max_open_jobs" : "20",
        "ml.enabled" : "true"
      },
```

其他信息

 `settings`, `os`, `process`, `jvm`,`thread_pool`, `transport`, `http`, `plugins`, `ingest` and `indices`:

```
GET /_nodes/process
```



## Nodes usage

检索关于每个节点特性使用情况的信息。

```
GET _nodes/usage
GET _nodes/nodeId1,nodeId2/usage
```

获取各种操作的使用次数：

```
{
  "_nodes" : {
    "total" : 1,
    "successful" : 1,
    "failed" : 0
  },
  "cluster_name" : "es65",
  "nodes" : {
    "B-M3lfhbQfS88kIq64pECQ" : {
      "timestamp" : 1603786339724,
      "since" : 1603763314565,
      "rest_actions" : {
        "nodes_usage_action" : 1,
        "nodes_info_action" : 18336,
        "get_index_template_action" : 347,
        "cat_alias_action" : 8,
        "get_mapping_action" : 347,
        "get_indices_action" : 8,
        "cat_count_action" : 4,
        "nodes_stats_action" : 16,
        "get_all_aliases_action" : 347,
        "cat_snapshot_action" : 3,
        "cat_segments_action" : 6,
        "cat_health_action" : 4,
        "xpack_info_action" : 1535,
        "field_capabilities_action" : 1,
        "cat_fielddata_action" : 24,
        "document_get_action" : 4626,
        "main_action" : 9167,
        "count_action" : 4,
        "cat_templates_action" : 4,
        "cat_recovery_action" : 8,
        "cat_shards_action" : 5,
        "cat_repositories_action" : 1,
        "cat_indices_action" : 12,
        "cat_pending_cluster_tasks_action" : 1,
        "cat_nodes_action" : 15,
        "xpack_monitoring_bulk_action" : 2300,
        "cluster_stats_action" : 2,
        "search_action" : 38305,
        "get_aliases_action" : 2,
        "cat_allocation_action" : 3,
        "cat_master_action" : 1,
        "cat_threadpool_action" : 8,
        "cat_node_attrs_action" : 2
      }
    }
  }
}

```



# Indices （索引）



## Indices Stats（索引统计）

 索引级统计信息提供关于在索引上发生的不同操作的统计信息。提供了关于索引级别作用域的统计信息(尽管也可以使用节点级别作用域检索大多数统计信息)。

下面返回所有索引的高级聚合和索引级统计信息:

```
GET /_stats
GET /index1,index2/_stats
```

默认情况下，会返回所有的统计信息，也可以在URI中指定只返回特定的统计信息。

### 统计信息分类

| 指标            | 描述                                                         |
| --------------- | ------------------------------------------------------------ |
| `docs`          | 文档/已删除文档(未合并的文档)的数量。注意，受刷新索引的影响。 |
| `store`         | 索引的大小。                                                 |
| `indexing`      | 索引统计信息，可以与逗号分隔的types列表结合使用，以提供文档类型级别的统计信息。 |
| `get`           | 获取get统计信息，包括丢失的统计信息                          |
| `search`        | 搜索统计数据，包括建议统计。您可以通过添加额外的“groups”参数来包含自定义组的统计信息(搜索操作可以与一个或多个组相关联)。“groups”参数接受以逗号分隔的组名称列表。使用' _all '返回所有组的统计信息。 |
| `segments`      | 检索开放段的内存使用情况。还可以选择设置' include_segment_file_size '标志，报告每个Lucene索引文件的磁盘使用情况。 |
| `completion`    | 完成显示统计数据。                                           |
| `fielddata`     | Fielddata统计数据。                                          |
| `flush`         | Flush统计                                                    |
| `merge`         | Merge 统计.                                                  |
| `request_cache` | Shard request cache统计.                                     |
| `refresh`       | Refresh 统计.                                                |
| `warmer`        | Warmer 统计.                                                 |
| `translog`      | Translog 统计.                                               |

一些统计数据允许每个字段的粒度，它接受包含字段的逗号分隔列表。默认情况下，包括所有字段：

| 字段                | 描述                                                         |
| ------------------- | ------------------------------------------------------------ |
| `fields`            | 要包含在统计数据中的字段列表。除非提供了更具体的字段列表(参见下面)，否则将使用此列表作为默认列表。 |
| `completion_fields` | 要包含在完成建议统计中的字段列表。                           |
| `fielddata_fields`  | 将包括在Fielddata统计中的字段列表                            |

### 查询格式

```
# Get back stats for merge and refresh only for all indices
GET /_stats/merge,refresh
# Get back stats for type1 and type2 documents for the my_index index
GET /my_index/_stats/indexing?types=type1,type2
# Get back just search stats for group1 and group2
GET /_stats/search?groups=group1,group2
```

返回的统计信息是在索引级别聚合的，包含初选和总聚合，其中初选仅是主分片的值，而total是主分片和复制分片的累计值。

注意，当分片在集群中移动时，它们在其他节点上创建的状态将被清除。另一方面，即使一个分片“保留”了一个节点，该节点仍将保留分片所贡献的统计信息。



### 分片统计信息

为了获得分片级别统计信息，请将级别参数设置为shards。

```
GET out-7.7.0-2020.10.29/_stats/merge?level=shards
```



## Indices（查看索引列表）

```
GET /_cat/indices?v
```

我们可以很快地知道有多少分片组成一个索引、文档的数量、已删除文档、主存储大小和总存储大小(包括副本在内的所有分片)。所有这些公开的指标都直接来自Lucene。

- 由于文档和已删除文档的数量都在lucene级别，所以它也包括了所有隐藏文档(比如嵌套文档)。
- 要在Elasticsearch级别获得实际的文档计数，推荐的方法是使用cat计数或count API



### 按照索引名排序

```
GET /_cat/indices?v&s=index
```



### 获取黄色索引

```
GET /_cat/indices?v&health=yellow
```



### 获取红色索引

```
GET /_cat/indices?v&health=red
```



### 查看拥有最大数量文档的索引

```
GET /_cat/indices?v&s=docs.count:desc
```



### 获取占用磁盘最大的索引

```
GET /_cat/indices?v&s=store.size:desc
```



### twitter的分片完成了多少次合并操作?

```
GET /_cat/indices/twitter?pri&v&h=health,index,pri,rep,docs.count,mt
```



### 查看每个索引使用的内存

```
GET /_cat/indices?v&h=i,tm&s=tm:desc
```



### 查询索引相关指标（完全展示）

```
GET /_cat/indices/out-7.7.0-2020.10.29?pri&v&h=*&format=json

```

### 所有字段示例如下

```json
[
  {
    "health" : "yellow",
    "status" : "open",
    "index" : "out-7.7.0-2020.10.29",
    "uuid" : "DSwheo_eQM2kTblsiVkUMQ",
    "pri" : "5",
    "rep" : "1",
    "docs.count" : "1282748",
    "docs.deleted" : "0",
    "creation.date" : "1603951688411",
    "creation.date.string" : "2020-10-29T06:08:08.411Z",
    "store.size" : "443.1mb",
    "pri.store.size" : "443.1mb",
    "pri.store.size" : "443.1mb",
    "completion.size" : "0b",
    "pri.completion.size" : "0b",
    "pri.completion.size" : "0b",
    "fielddata.memory_size" : "0b",
    "pri.fielddata.memory_size" : "0b",
    "pri.fielddata.memory_size" : "0b",
    "fielddata.evictions" : "0",
    "pri.fielddata.evictions" : "0",
    "pri.fielddata.evictions" : "0",
    "query_cache.memory_size" : "0b",
    "pri.query_cache.memory_size" : "0b",
    "pri.query_cache.memory_size" : "0b",
    "query_cache.evictions" : "0",
    "pri.query_cache.evictions" : "0",
    "pri.query_cache.evictions" : "0",
    "request_cache.memory_size" : "3.4kb",
    "pri.request_cache.memory_size" : "3.4kb",
    "pri.request_cache.memory_size" : "3.4kb",
    "request_cache.evictions" : "0",
    "pri.request_cache.evictions" : "0",
    "pri.request_cache.evictions" : "0",
    "request_cache.hit_count" : "0",
    "pri.request_cache.hit_count" : "0",
    "pri.request_cache.hit_count" : "0",
    "request_cache.miss_count" : "5",
    "pri.request_cache.miss_count" : "5",
    "pri.request_cache.miss_count" : "5",
    "flush.total" : "5",
    "pri.flush.total" : "5",
    "pri.flush.total" : "5",
    "flush.total_time" : "0s",
    "pri.flush.total_time" : "0s",
    "pri.flush.total_time" : "0s",
    "get.current" : "0",
    "pri.get.current" : "0",
    "pri.get.current" : "0",
    "get.time" : "0s",
    "pri.get.time" : "0s",
    "pri.get.time" : "0s",
    "get.total" : "0",
    "pri.get.total" : "0",
    "pri.get.total" : "0",
    "get.exists_time" : "0s",
    "pri.get.exists_time" : "0s",
    "pri.get.exists_time" : "0s",
    "get.exists_total" : "0",
    "pri.get.exists_total" : "0",
    "pri.get.exists_total" : "0",
    "get.missing_time" : "0s",
    "pri.get.missing_time" : "0s",
    "pri.get.missing_time" : "0s",
    "get.missing_total" : "0",
    "pri.get.missing_total" : "0",
    "pri.get.missing_total" : "0",
    "indexing.delete_current" : "0",
    "pri.indexing.delete_current" : "0",
    "pri.indexing.delete_current" : "0",
    "indexing.delete_time" : "0s",
    "pri.indexing.delete_time" : "0s",
    "pri.indexing.delete_time" : "0s",
    "indexing.delete_total" : "0",
    "pri.indexing.delete_total" : "0",
    "pri.indexing.delete_total" : "0",
    "indexing.index_current" : "0",
    "pri.indexing.index_current" : "0",
    "pri.indexing.index_current" : "0",
    "indexing.index_time" : "0s",
    "pri.indexing.index_time" : "0s",
    "pri.indexing.index_time" : "0s",
    "indexing.index_total" : "0",
    "pri.indexing.index_total" : "0",
    "pri.indexing.index_total" : "0",
    "indexing.index_failed" : "0",
    "pri.indexing.index_failed" : "0",
    "pri.indexing.index_failed" : "0",
    "merges.current" : "0",
    "pri.merges.current" : "0",
    "pri.merges.current" : "0",
    "merges.current_docs" : "0",
    "pri.merges.current_docs" : "0",
    "pri.merges.current_docs" : "0",
    "merges.current_size" : "0b",
    "pri.merges.current_size" : "0b",
    "pri.merges.current_size" : "0b",
    "merges.total" : "0",
    "pri.merges.total" : "0",
    "pri.merges.total" : "0",
    "merges.total_docs" : "0",
    "pri.merges.total_docs" : "0",
    "pri.merges.total_docs" : "0",
    "merges.total_size" : "0b",
    "pri.merges.total_size" : "0b",
    "pri.merges.total_size" : "0b",
    "merges.total_time" : "0s",
    "pri.merges.total_time" : "0s",
    "pri.merges.total_time" : "0s",
    "refresh.total" : "15",
    "pri.refresh.total" : "15",
    "pri.refresh.total" : "15",
    "refresh.time" : "0s",
    "pri.refresh.time" : "0s",
    "pri.refresh.time" : "0s",
    "refresh.listeners" : "0",
    "pri.refresh.listeners" : "0",
    "pri.refresh.listeners" : "0",
    "search.fetch_current" : "0",
    "pri.search.fetch_current" : "0",
    "pri.search.fetch_current" : "0",
    "search.fetch_time" : "0s",
    "pri.search.fetch_time" : "0s",
    "pri.search.fetch_time" : "0s",
    "search.fetch_total" : "0",
    "pri.search.fetch_total" : "0",
    "pri.search.fetch_total" : "0",
    "search.open_contexts" : "0",
    "pri.search.open_contexts" : "0",
    "pri.search.open_contexts" : "0",
    "search.query_current" : "0",
    "pri.search.query_current" : "0",
    "pri.search.query_current" : "0",
    "search.query_time" : "0s",
    "pri.search.query_time" : "0s",
    "pri.search.query_time" : "0s",
    "search.query_total" : "5",
    "pri.search.query_total" : "5",
    "pri.search.query_total" : "5",
    "search.scroll_current" : "0",
    "pri.search.scroll_current" : "0",
    "pri.search.scroll_current" : "0",
    "search.scroll_time" : "0s",
    "pri.search.scroll_time" : "0s",
    "pri.search.scroll_time" : "0s",
    "search.scroll_total" : "0",
    "pri.search.scroll_total" : "0",
    "pri.search.scroll_total" : "0",
    "segments.count" : "47",
    "pri.segments.count" : "47",
    "pri.segments.count" : "47",
    "segments.memory" : "1.2mb",
    "pri.segments.memory" : "1.2mb",
    "pri.segments.memory" : "1.2mb",
    "segments.index_writer_memory" : "0b",
    "pri.segments.index_writer_memory" : "0b",
    "pri.segments.index_writer_memory" : "0b",
    "segments.version_map_memory" : "0b",
    "pri.segments.version_map_memory" : "0b",
    "pri.segments.version_map_memory" : "0b",
    "segments.fixed_bitset_memory" : "0b",
    "pri.segments.fixed_bitset_memory" : "0b",
    "pri.segments.fixed_bitset_memory" : "0b",
    "warmer.current" : "0",
    "pri.warmer.current" : "0",
    "pri.warmer.current" : "0",
    "warmer.total" : "5",
    "pri.warmer.total" : "5",
    "pri.warmer.total" : "5",
    "warmer.total_time" : "0s",
    "pri.warmer.total_time" : "0s",
    "pri.warmer.total_time" : "0s",
    "suggest.current" : "0",
    "pri.suggest.current" : "0",
    "pri.suggest.current" : "0",
    "suggest.time" : "0s",
    "pri.suggest.time" : "0s",
    "pri.suggest.time" : "0s",
    "suggest.total" : "0",
    "pri.suggest.total" : "0",
    "pri.suggest.total" : "0",
    "memory.total" : "1.2mb",
    "pri.memory.total" : "1.2mb",
    "pri.memory.total" : "1.2mb"
  }
] 

```

# Shards（分片）

## 详细视图

提供什么节点包含哪些分片的详细视图。它将告诉您它是主分片还是副本、文档的数量、它在磁盘上占用的字节数以及它所在的节点。

```
GET _cat/shards?v
GET _cat/shards/twitt*
```

## 未分配分片

```
GET _cat/shards?h=index,shard,prirep,state,unassigned.reason
```



# Segments（段）



## 底层信息

提供有关索引分片中的段的底层信息。

```
GET /_cat/segments?v
```

响应格式

```
  {
    "index" : "es-7.7.0-2020.10.23.17.40",
    "shard" : "0",
    "prirep" : "p",   //此段属于主分片还是复制分片。
    "ip" : "192.168.0.1",
    "segment" : "_1g",   //从生成的段派生出的段名。该名称在内部用于在此段所属的切分目录中生成文件名。
    "generation" : "52",  //生成号随着写入的每个段而增加。段的名称派生自这个代号。
    "docs.count" : "48536",   //存储在此段中的未删除文档的数量。请注意，这些都是Lucene文档，因此计数将包括隐藏文档(例如来自嵌套类型的文档)。
    "docs.deleted" : "0",  //存储在此段中的已删除文档的数量。如果这个数大于0，那么当这个段被合并时，空间将被回收。
    "size" : "16.3mb",    //此段所使用的磁盘空间。
    "size.memory" : "43287",  //段将一些数据存储到内存中，以便有效地进行搜索。此列显示所使用的内存字节数。
    "committed" : "true", //该段是否已在磁盘上同步。提交的段可以在重启的时候存活。无需担心false，未提交段的数据也存储在事务日志中，以便Elasticsearch能够在下一次开始时重播更改。
    "searchable" : "true",  //如果片段是可搜索的，则为true。值为false很可能意味着该段已被写入磁盘，但此后未发生刷新以使其可搜索。
    "version" : "7.5.0",  //用于编写此段的Lucene版本。
    "compound" : "false"    //该段是否存储在复合文件中。当为true时，这意味着Lucene将该段中的所有文件合并为一个文件，以保存文件描述符。
    }
```



## 详细信息

提供关于分片和索引状态的更多信息，可能还有优化信息、删除时“浪费”的数据，等等。

```
GET /test/_segments
GET /test1,test2/_segments
GET /_segments
```

响应解析

```
{
  "_shards" : {
    "total" : 5,
    "successful" : 5,
    "failed" : 0
  },
  "indices" : {
    "es-7.7.0-2020.10.23.09.13" : {
      "shards" : {
        "0" : [
          {
            "routing" : {
              "state" : "STARTED",
              "primary" : true,
              "node" : "B-M3lfhbQfS88kIq64pECQ"
            },
            "num_committed_segments" : 3,
            "num_search_segments" : 3,
            "segments" : {
              "_0" : {    //JSON文档的键是段的名称。此名称用于生成文件名:切分目录中以此段名称开头的所有文件都属于此段。
                "generation" : 0,   //当需要写入新段时，生成号基本上是递增的。段名派生自这个代号。
                "num_docs" : 745,   //存储在此段中的未删除文档的数量。
                "deleted_docs" : 0,   //存储在此段中的已删除文档的数量。如果这个数大于0，那么当这个段被合并时，空间将被回收。
                "size_in_bytes" : 381443,   //此段使用的磁盘空间量，以字节为单位。
                "memory_in_bytes" : 6500,    //段需要存储一些数据到内存中，以便有效地搜索。这个数字返回用于此目的的字节数。值为-1表示Elasticsearch不能计算这个数字。
                "committed" : true,     //该段是否已在磁盘上同步。提交的段可以在硬重新引导中存活。无需担心false，未提交段的数据也存储在事务日志中，以便Elasticsearch能够在下一次开始时重播更改。
                "search" : true,   //该片段是否可搜索。值为false很可能意味着该段已被写入磁盘，但此后未发生刷新以使其可搜索。
                "version" : "7.5.0",  //用于编写此段的Lucene版本。
                "compound" : true,    //该段是否存储在复合文件中。当为true时，这意味着Lucene将该段中的所有文件合并为一个文件，以保存文件描述符。
                "attributes" : {   //包含有关是否启用了高压缩的信息
                  "Lucene50StoredFieldsFormat.mode" : "BEST_SPEED"
                }
              },
              "_1" : {
                "generation" : 1,
                "num_docs" : 1253,
                "deleted_docs" : 0,
                "size_in_bytes" : 593668,
                "memory_in_bytes" : 8111,
                "committed" : true,
                "search" : true,
                "version" : "7.5.0",
                "compound" : true,
                "attributes" : {
                  "Lucene50StoredFieldsFormat.mode" : "BEST_SPEED"
                }
              },
              "_2" : {
                "generation" : 2,
                "num_docs" : 405,
                "deleted_docs" : 0,
                "size_in_bytes" : 209748,
                "memory_in_bytes" : 6518,
                "committed" : true,
                "search" : true,
                "version" : "7.5.0",
                "compound" : true,
                "attributes" : {
                  "Lucene50StoredFieldsFormat.mode" : "BEST_SPEED"
                }
              }
            }
          }
        ],
        。。。
```



## 调试信息

若要添加可用于调试的其他信息，请使用verbose标志。

```
GET /test/_segments?verbose=true
```



# Cluster Settings（集群配置）



## 获取配置

```
GET /_cluster/settings
GET /_cluster/settings?include_defaults=true
```

## 持久配置

```
PUT /_cluster/settings
{
    "persistent" : {
        "indices.recovery.max_bytes_per_sec" : "50mb"
    }
}
```

## 临时配置

```
PUT /_cluster/settings?flat_settings=true
{
    "transient" : {
        "indices.recovery.max_bytes_per_sec" : "20mb"
    }
}
```

## 重置配置

```
PUT /_cluster/settings
{
    "transient" : {
        "indices.recovery.max_bytes_per_sec" : null
    }
}
```

## 更新配置

```
PUT /_cluster/settings
{
    "persistent" : {
        "indices.recovery.max_bytes_per_sec" : "50mb"
    }
}
```

## 优先级

集群配置应用的优先级顺序：

1、临时配置

2、持久配置

3、elasticsearch.yml文件中的配置

建议使用动态配置的方式对集群进行设置，可以确保各个节点的配置一致

# Snapshots（快照）

## repositories

repositories命令显示在集群中注册的快照存储库。

```
GET /_cat/repositories?v
```

## snapshots

显示属于特定存储库的所有快照。要查询可用的存储库列表，可以使用命令`/_cat/repositories`。然后查询名为repo1的存储库的快照，

```
GET /_cat/snapshots/repo1?v&s=id
```

每个快照都包含有关启动和停止时间的信息。启动和停止时间戳有两种格式。HH:MM:SS的输出只是为了快速的阅读。纪元时间保留更多信息，包括日期，如果快照进程跨度为天，那么纪元时间可以由机器排序。



# Task（任务）



## pending_tasks

等待任务列表

```
GET /_cat/pending_tasks?v
```



## Pending cluster tasks

cluster tasks API返回尚未执行的任何集群级别更改(例如创建索引、更新映射、分配或失败分片)的列表。

这个API返回集群状态中所有未执行更新的列表。这些任务不同于Task Management API报告的任务，后者包括周期性任务和用户发起的任务，如节点状态、搜索查询或创建索引请求。但是，如果用户发起的任务(比如create index命令)导致集群状态更新，则 task api 和 pending cluster tasks API都可能报告该任务的活动。

```
GET /_cluster/pending_tasks
```

通常这会返回一个空列表，因为集群级别的更改通常很快。但是，如果有任务排队，输出将是这样的:

```
{
   "tasks": [
      {
         "insert_order": 101,
         "priority": "URGENT",
         "source": "create-index [foo_9], cause [api]",
         "time_in_queue_millis": 86,
         "time_in_queue": "86ms"
      },
      {
         "insert_order": 46,
         "priority": "HIGH",
         "source": "shard-started ([foo_2][1], node[tMTocMvQQgGCkj7QDHl3OA], [P], s[INITIALIZING]), reason [after recovery from shard_store]",
         "time_in_queue_millis": 842,
         "time_in_queue": "842ms"
      },
      {
         "insert_order": 45,
         "priority": "HIGH",
         "source": "shard-started ([foo_2][0], node[tMTocMvQQgGCkj7QDHl3OA], [P], s[INITIALIZING]), reason [after recovery from shard_store]",
         "time_in_queue_millis": 858,
         "time_in_queue": "858ms"
      }
  ]
}
```



## Task Management

允许检索关于集群中一个或多个节点上当前执行的任务的信息。

```
//检索集群中所有节点上当前运行的所有任务。
GET _tasks 
//检索在节点nodeId1和nodeId2上运行的所有任务。
GET _tasks?nodes=nodeId1,nodeId2 
//检索在节点nodeId1和nodeId2上运行的所有与集群相关的任务。
GET _tasks?nodes=nodeId1,nodeId2&actions=cluster:* 
```

列出任务

```
GET _cat/tasks
GET _cat/tasks?detailed
```

根据TaskID获取

```
GET _tasks/oTUltX4IQMOUUVeiohTt8A:124
```

获取一个特定任务的所有子任务

```
GET _tasks?parent_task_id=oTUltX4IQMOUUVeiohTt8A:123
```

还可以使用详细的请求参数来获取关于正在运行的任务的更多信息。这对于区分任务是有用的，但是执行成本更高。例如，使用详细请求参数获取所有搜索:

```
GET _tasks?actions=*search&detailed
```

阻塞10秒，或者直到id为oTUltX4IQMOUUVeiohTt8A:12345的任务完成。

```
GET _tasks/oTUltX4IQMOUUVeiohTt8A:12345?wait_for_completion=true&timeout=10s
```

等待所有的重新索引任务完成

```
GET _tasks?actions=*reindex&wait_for_completion=true&timeout=10s
```

取消任务

```
POST _tasks/oTUltX4IQMOUUVeiohTt8A:12345/_cancel
POST _tasks/_cancel?nodes=nodeId1,nodeId2&actions=*reindex
```

任务组

```
GET _tasks?group_by=parents
```

禁用分组

```
GET _tasks?group_by=none
```



# Thread（线程）

## thread_pool

thread_pool命令显示每个节点的集群范围的线程池统计信息。默认情况下，将返回所有线程池的活动、队列和拒绝统计信息。

```
GET /_cat/thread_pool?v
```

自定义字段查询

```
GET /_cat/thread_pool/generic?v&h=id,name,active,rejected,completed
```



## Nodes hot_threads

热点线程

```
GET /_nodes/hot_threads
GET /_nodes/nodeId1,nodeId2/hot_threads
```

# Plugins（插件）

跨节点的插件列表

```
GET /_cat/plugins?v&s=component&h=name,component,version,description
```



# Remote Cluster（远程集群）

## Remote Cluster Info

允许检索所有配置的远程集群信息。

```
GET /_remote/info
```

