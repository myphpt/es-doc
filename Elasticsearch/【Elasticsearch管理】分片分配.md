[TOC]

# 索引级分片分配

## 分片分配过滤

可以在启动时为每个节点分配任意的元数据属性。例如，可以给节点分配机架和size属性

```
bin/elasticsearch -Enode.attr.rack=rack1 -Enode.attr.size=big  

也可以在 elasticsearch.yml配置文件中设置
```



这些元数据属性可以与`index.routing.allocation.*` 一起使用，为特定节点组分配索引的设置。

例如，我们可以将索引测试移动到大节点或中节点:

```
PUT test/_settings
{
  "index.routing.allocation.include.size": "big,medium"
}
```

或者，我们可以使用exclude规则将索引test远离small节点:

```
PUT test/_settings
{
  "index.routing.allocation.exclude.size": "small"
}
```

可以指定多个规则，在这种情况下，必须满足所有条件。例如，我们可以将索引test移动到rack1中的big节点，操作如下:

```
PUT test/_settings
{
  "index.routing.allocation.include.size": "big",
  "index.routing.allocation.include.rack": "rack1"
}
```

如果某些条件不能满足，那么分片将不会被移动。

以下设置是动态的，允许活动索引从一组节点移动到另一组节点:

```
index.routing.allocation.include.{attribute}
将索引分配给{attribute}至少有一个逗号分隔值的节点。

index.routing.allocation.require.{attribute} 
将索引分配给{attribute}具有所有逗号分隔值的节点。

index.routing.allocation.exclude.{attribute} 
将索引分配给{attribute}不包含逗号分隔值的节点。


{attribute}属性值支持：_name _host_ip _publish_ip ip _host 
```

支持通配符

```
PUT test/_settings
{
  "index.routing.allocation.include._ip": "192.168.2.*"
}
```



## 节点下线时的延迟分配

当一个节点出于任何原因离开集群时，master 的反应:

- 将replica 分片提升为primary ，以替换节点上的任何primaries 。
- 分配replica 分片以替换丢失的副本(假设有足够的节点)。
- 在剩余节点之间均匀地重新平衡分片。

通过确保尽快完全复制每个分片，这些操作旨在保护集群免受数据丢失。



尽管我们在节点级和集群级都限制了并发恢复，但这种“分片转移”仍然会给集群增加大量额外的负载，如果丢失的节点可能很快就会返回，这可能是不必要的。设想一下这样的情景:

1. 节点5失去了网络连接。
2. 对于节点5上的每个primary ，master 将一个replica 分片提升为primary 。
3. master 将新的副本分配给集群中的其他节点。
4. 每个新replica 在网络上生成primary 分片的整个副本。
5. 将更多的分片移动到不同的节点以重新平衡集群。
6. 节点5在几分钟后返回。
7. 主服务器通过向节点5分配分片来重新平衡集群。



如果master 只等待了几分钟，那么丢失的分片就可以被重新分配到节点5，并且具有最小的网络流量。对于已经自动同步刷新的空闲分片(没有接收索引请求的分片)，这个过程会更快。

由于一个节点已经离开而没有分配的复制分片的分配可以通过index.unassigned.node_left.delayed_timeout动态设置延迟，默认为1m。

```
PUT _all/_settings
{
  "settings": {
    "index.unassigned.node_left.delayed_timeout": "5m"
  }
}

//立即进行重新分配
PUT _all/_settings
{
  "settings": {
    "index.unassigned.node_left.delayed_timeout": "0"
  }
}
```

启用延迟分配后，上面的场景变为如下所示:

1. 节点5失去了网络连接。
2. 对于节点5上的每个primary ，master 将一个replica分片提升到primary 。
3. master会记录一条消息，说明未分配分片的分配已经被延迟，以及延迟了多长时间。
4. 集群仍然是黄色的，因为有未分配的副本分片。
5. 节点5在超时结束前几分钟返回。
6. 丢失的副本被重新分配到节点5(同步刷新的分片几乎立即恢复)。



此设置不会影响将副本提升到primaries，也不会影响以前未分配的副本的分配。特别是，延迟分配在整个集群重新启动后不会生效。此外，在master 故障转移情况下，会忘记经过的延迟时间(即重置为完整的初始延迟)。



如果延迟分配超时，master 将丢失的分片分配给另一个节点，该节点将开始恢复。如果丢失的节点重新加入集群，并且它的分片仍然具有与primary相同的同步id，则分片重新定位将被取消，而同步的分片将用于恢复。



## 索引恢复优先级

在可能的情况下，将按优先级顺序恢复未分配的分片。索引按优先次序排列如下:

- 可选的index.priority设置(先高后低)
- 索引创建日期(先高后低)
- 索引名(先高后低)

这意味着，在默认情况下，较新的索引将在较旧的索引之前恢复。

使用每个索引动态更新index.priority设置，用于定制索引优先级顺序，此设置接受一个整数，并可以动态更新，例如:

```
PUT index_1

PUT index_2

PUT index_3
{
  "settings": {
    "index.priority": 10
  }
}

PUT index_4
{
  "settings": {
    "index.priority": 5
  }
}
```

在上面的例子中：

- index_3将首先被恢复，因为它具有最高的index.priority。
- index_4下一个将被恢复，因为它具有下一个最高优先级。
- 接下来将恢复index_2，因为它是最近创建的。
- index_1将最后恢复。



## 节点的总分片数

集群级分片分配器试图将单个索引的分片分散到尽可能多的节点上。然而，根据您有多少个分片和索引以及它们有多大，可能并不总是能够均匀地分布分片。

下面的动态设置允许您指定一个对每个节点允许的单个索引的分片总数的硬限制:

```
index.routing.allocation.total_shards_per_node 
将分配给单个节点的最大分片数(副本和主节点)。默认为无限。
```

您还可以限制一个节点可以拥有的分片的数量，而不考虑索引:

```
cluster.routing.allocation.total_shards_per_node 
全局分配给单个节点的最大分片数(副本和主节点)。默认值为unbounded(-1)。
```

这些设置施加了硬限制，这可能导致一些分片没有被分配。谨慎使用。



# 集群级分片分配策略

 `Shard Allocation`是向节点分配分片的过程。可能发生在初始恢复、副本分配、重新平衡或添加或删除节点时。

master的主要角色之一是决定将哪些分片分配给哪些节点，以及何时在节点之间移动分片以重新平衡集群。

有许多设置可用来控制分片分配过程:

- 集群级分片分配列出了控制分配和重新平衡操作的设置。

- 基于磁盘的分片分配解释了Elasticsearch如何考虑可用磁盘空间和相关设置。

- 分片分配感知和强制感知控制如何跨不同机架或可用性区域分布分片。

- 分片分配过滤允许某些节点或节点组被排除在分配之外，以便它们可以退役。

  

## 分片分配设置

```
cluster.routing.allocation.enable 

启用或禁用特定类型的分片分配:
all -(默认)允许为所有类型的分片分配分片。
primaries ——只允许为主分片分配分片。
new_primary—只允许对新索引的主分片进行分片分配。
none—对于任何索引都不允许任何类型的分片分配。

当重新启动节点时，此设置不影响本地主分片的恢复。拥有未分配主分片副本的重新启动节点将立即恢复该主分片，假设其分配id与集群状态中的一个活动分配id匹配。
```

其他参数：

```
cluster.routing.allocation.node_concurrent_incoming_recoveries 
在一个节点上允许发生多少个并发传入分片恢复。传入恢复是指在节点上分配目标分片(很可能是副本，除非分片被重新定位)的恢复。默认为2。

cluster.routing.allocation.node_concurrent_outgoing_recoveries 
在一个节点上允许发生多少并发传出分片恢复。传出恢复是指在节点上分配源分片(很可能是主分片，除非分片被重新定位)的恢复。默认为2。

cluster.routing.allocation.node_concurrent_recoveries 
设置以上两个值的快捷方式

cluster.routing.allocation.node_initial_primaries_recoveries 
虽然通过网络恢复副本，但在节点重启后恢复未分配的primary将使用来自本地磁盘的数据。这些操作应该很快，这样更多的初始primary恢复就可以在同一个节点上并行进行。默认为4。

cluster.routing.allocation.same_shard.host 
允许执行检查，以防止基于主机名和主机地址在一台主机上分配同一个shard的多个实例。默认值为false，表示默认情况下不执行检查。此设置仅适用于在同一台机器上启动多个节点的情况。
```



## 分片平衡设置

以下动态设置可用于控制跨集群的分片重新平衡:

```
cluster.routing.rebalance.enable 
	为特定类型的分片启用或禁用重新平衡:

	all -(默认)允许对所有类型的分片进行分片平衡。
	primaries ——只允许主分片进行分片平衡。
	replicas -只允许副本分片平衡。
	none -任何索引都不允许任何类型的分片平衡。

cluster.routing.allocation.allow_rebalance 
	指定何时允许分片再平衡:

	always 
	indices_primaries_active   仅当集群中的所有primaries都已分配。
	indices_all_active   (默认)仅当集群中的所有分片(主分片和副本)都已分配。

cluster.routing.allocation.cluster_concurrent_rebalance 

允许控制集群范围内允许多少并发分片重平衡。默认为2。
注意，此设置仅控制由于集群中不平衡而导致的并发分片重定位的数量。此设置不限制由于 allocation filtering或forced awareness而导致的分片重定位。
```



## 分片平衡因子

以下设置共同确定将每个分片放置在何处。当没有允许的重新平衡操作使任何节点的权重更接近任何其他节点的权重超过balance.threshold时，集群即达到平衡。

```
cluster.routing.allocation.balance.shard 
定义在节点上分配的分片总数的权重因子(浮点数)。默认为0.45f。提高这个值会导致集群中所有节点上的分片数量趋于均衡。

cluster.routing.allocation.balance.index 
定义在特定节点上分配的每个索引的分片数的权重因子(浮点数)。默认为0.55f。提高这个值会导致集群中所有节点的每个索引的分片数趋于相等。

cluster.routing.allocation.balance.threshold 
应该执行的操作的最小优化值(非负浮点数)。默认为1.0f。提高这个值将导致集群在优化分片平衡方面不那么积极。
```

无论平衡算法的结果如何，由于forced awareness或 allocation filtering导致的操作都不允许再平衡。





# 基于磁盘的分片分配策略

Elasticsearch会考虑节点上的可用磁盘空间，然后再决定是将新分片分配给该节点，还是主动将分片从该节点重新定位。

```
cluster.routing.allocation.disk.threshold_enabled  
	(动态)默认为true。若设置为false，则禁用磁盘分配决定器。
cluster.routing.allocation.disk.watermark.low  
	（动态）磁盘水位线，不使用超过该水位线的空间，默认是85%，也可以设置值（500m）。此设置对新创建的索引的主分片没有影响，特别是对以前从未分配过的分片没有影响。
cluster.routing.allocation.disk.watermark.high  
	(动态)磁盘高水位线，超过该水位线的分片将重新定位。此设置将影响所有分片的分配，无论之前是否分配。
cluster.routing.allocation.disk.watermark.enable_for_single_data_node 
	（静态）默认是单节点中忽略磁盘水位线，设置为true，启用该设置
cluster.routing.allocation.disk.watermark.flood_stage  
	（静态）最高水位线，默认值95%，强制使索引变为只读索引块(index.blocks.read_only_allow_delete)，禁止任何的写入请求。这是为了防止耗尽单机磁盘容量的最后手段。这是防止节点耗尽磁盘空间的最后一种手段。一旦有足够的可用磁盘空间允许索引操作继续，就必须手动释放索引块。

cluster.info.update.interval 
	（动态）节点磁盘检查频率，默认30s
```

不能在这些设置中混合使用百分比值和字节值。要么全部设置为百分比值，要么全部设置为字节值。这样我们就可以验证设置在内部是否一致(即，低磁盘阈值不超过高磁盘阈值，而高磁盘阈值不超过泛滥阶段阈值)。

重置只读索引块：

```
PUT /twitter/_settings
{
  "index.blocks.read_only_allow_delete": null
}
```

举个栗子：

```
PUT _cluster/settings
{
  "transient": {
    "cluster.routing.allocation.disk.watermark.low": "100gb",
    "cluster.routing.allocation.disk.watermark.high": "50gb",
    "cluster.routing.allocation.disk.watermark.flood_stage": "10gb",
    "cluster.info.update.interval": "1m"
  }
}
```

百分比值指的是已使用的磁盘空间，而字节值指的是空闲磁盘空间。这可能会令人困惑，因为它颠倒了high和low的含义。例如，将低水印设置为10gb，将高水印设置为5gb是合理的，但反之则不然。



## 其他设置

```
cluster.routing.allocation.disk.include_relocations 
默认为true，这意味着Elasticsearch在计算节点的磁盘使用情况时将考虑当前正在重定位到目标节点的分片。 但是，考虑到重定位分片的大小，可能意味着在高端方面错误地估计了节点的磁盘使用情况，因为重定位可能已完成90％，并且最近检索到的磁盘使用情况将包括重定位分片的总大小。 以及正在运行的重定位已使用的空间。
```





# 分片自动感知

多个vm上运行节点时,在相同的物理服务器上,在多个机架,或跨多个区域或领域,更有可能是两个节点在同一物理服务器上,在同一架,或在同一区域或域会崩溃在同一时间,而不是两个无关的节点同时崩溃。

如果Elasticsearch了解硬件的物理配置，它可以确保主分片及其复制分片分散在不同的物理服务器、机架或区域，从而最大限度地降低同时丢失所有分片副本的风险。

分片分配感知设置允许您告诉Elasticsearch您的硬件配置。

例如，假设我们有几个机架。当我们启动一个节点时，我们可以通过给它分配一个名为rack_id的任意元数据属性来告诉它它在哪个机架上——我们可以使用任何属性名称。例如:

```
./bin/elasticsearch -Enode.attr.rack_id=rack_one 
也可以在elasticsearch.yml 设置
```





## 自动感知属性

```
cluster.routing.allocation.awareness.attributes: rack_id
```

有了这个配置之后，我们假设用node.attr.rack_id：rack_one启动两个节点，然后创建一个包含5个主分片和每个主分片1个副本的索引。在这两个节点上分配所有的主节点和副本。

现在，如果我们用node.attr.rack_id：rack_two再启动两个节点, Elasticsearch将把分片移动到新节点，确保(如果可能)同一分片的两个副本不会出现在同一机架上。然而，如果rack_two失败，关闭了它的两个节点，Elasticsearch仍然会将丢失的分片副本分配给rack_one中的节点。

当执行搜索或获取请求时，启用了分片感知，Elasticsearch将倾向于使用本地分片(同一感知组中的分片)来执行请求。这通常比跨机架或跨区域边界更快。

```
//设置节点的自动感知属性
node.attr.rack_id: rack_one
cluster.routing.allocation.awareness.attributes: rack_id

自动感知同一网段、同一机架、同一机房的物理机，最大限度的动态分配分片位置。则集群分片只在这个两个节点之间复制。
```



## 混合感知

可以指定多个感知属性，在这种情况下，在决定将分片分配到何处时，将分别考虑每个属性。

```
cluster.routing.allocation.awareness.attributes: rack_id,zone
```

在使用感知属性时，将不会将分片分配给没有为这些属性设置值的节点。

在具有相同感知属性值的特定节点组上分配的分片的主/副本数量由属性值的数量决定。当组中的节点数量不平衡，并且有许多副本时，可能会留下未分配的副本分片。



## 强制感知

假设您有两个区域，这两个区域上有足够的硬件来承载所有的主分片和复制分片。但是，一个区域中的硬件，虽然足以承载一半的分片，但可能无法承载所有的分片。

在一般情况下，如果一个区域与另一个区域失去联系，Elasticsearch将把所有丢失的复制分片分配到一个区域。但是在本例中，这种突然的额外负载会导致剩余区域中的硬件过载。

强制感知通过不允许将同一分片的副本分配到同一区域来解决这个问题。

例如，假设我们有一个名为zone的感知属性，并且我们知道我们将有两个区域，zone1和zone2。下面是我们如何强制感知一个节点:

```
cluster.routing.allocation.awareness.force.zone.values: zone1,zone2 
cluster.routing.allocation.awareness.attributes: zone
我们必须列出区域属性可能拥有的所有值。
```

现在，如果我们用 `node.attr.zone`：zone1开始两个节点，并创建具有5个分片和1个副本的索引。将创建索引，但只分配5个主分片(不分配副本)。只有当我们使用node.attr.zone：zone2启动更多节点时将分配副本。





# 分片分配过滤器

索引分片分配提供了每个索引的设置来控制对节点的分片分配，而集群级分片分配过滤允许您允许或不允许从任何索引向特定节点分配分片。

## 属性设置

```
cluster.routing.allocation.include.{attribute} 
将分片分配给{attribute}至少有一个逗号分隔值的节点。

cluster.routing.allocation.require.{attribute} 
仅将分片分配给{attribute}具有所有逗号分隔值的节点。

cluster.routing.allocation.exclude.{attribute} 
不要为{attribute}具有任何逗号分隔值的节点分配分片。

{attribute}属性值：_name  _ip   _host 
```



## 节点退役

集群范围的分片分配筛选的典型用例是当您想要退役一个节点，并且您想要在关闭该节点之前将分片从该节点移动到集群中的其他节点。

```
PUT _cluster/settings
{
  "transient" : {
    "cluster.routing.allocation.exclude._ip" : "10.0.0.1"
  }
}
```

只有在不破坏另一个路由约束的情况下，如永远不将主分片和复制分片分配给同一个节点，分片才会被重新分配。





# 杂项设置

## 元数据设置

```
cluster.blocks.read_only 
	（动态）设置整个集群只读
cluster.blocks.read_only_allow_delete 
	（动态）集群只读，可以删除
```

不要依赖此设置来防止对集群的更改。任何能够访问集群更新设置API的用户都可以再次对集群进行读写操作。

索引设置

```
PUT /my-index-000001/_settings
{
  "index.blocks.read_only_allow_delete": null
}
```



## 集群分片限制

在Elasticsearch 7.0及以后版本中，将根据集群中的节点数量对集群中的分片数量进行软限制。这样做的目的是防止可能无意中破坏集群稳定的操作。在7.0之前，会导致集群超过限制的操作将发出弃用警告。

如果集群已经超过极限,由于在节点加入或环境变化,所有操作,创建或打开指数将发出警告,直到增加如下所述的极限,或一些指数已经关闭或删除分片下面的数量限制。

如果创建新索引、恢复索引快照或打开已关闭索引等操作将导致集群中的分片数量超过此限制，该操作将发出弃用警告。

副本会达到这个限制，但是关闭的索引不会。包含5个主分片和2个副本的索引将被计算为15个分片。任何关闭的索引都被计数为0，无论它包含多少个分片和副本。

默认限制为每个节点1000个分片，可以使用以下属性动态调整:

```
cluster.max_shards_per_node 
	（动态）控制每个data node的最大分片数量
```

例如，具有默认设置的3节点集群将允许跨所有打开的索引共3000个shard。如果将上述设置更改为1,500，那么集群总共将允许4,500个分片。

当超过单节点所能容纳的最大分片数量的上限值时

```
PUT test/_doc/1
{
  "message":"test"
}
```

会发出软警告，该警告并不会让你的操作无效，具体的机器可以承载的分片数仍然视机器性能而定，并不做强制限制

```
#! Deprecation: In a future major version, this request will fail because this action would add [10] total shards, but this cluster currently has [1303]/[1000] maximum shards open. Before upgrading, reduce the number of shards in your cluster or adjust the cluster setting [cluster.max_shards_per_node].
```



## 自定义集群元数据

用户定义的元数据可以使用集群设置API存储和检索。这可以用于存储关于集群的不经常更改的任意数据，而不需要创建索引来存储这些数据。此数据可以使用任何前缀为cluster.metadata的键存储。例如，将集群管理员的电子邮件地址存储在密钥cluster.metadata.administrator下，发出此请求:

```
PUT /_cluster/settings
{
  "persistent": {
    "cluster.metadata.administrator": "sysadmin@example.com"
  }
}
```

用户定义的集群元数据不用于存储敏感或机密信息。任何存储在用户定义的集群元数据中的信息都可以被任何访问集群Get Settings API的人看到，并记录在Elasticsearch日志中。



## Index tombstone

集群状态维护索引tombstone以显式地表示已删除的索引。集群状态下维护的tombstone数量由以下属性控制，不能动态更新:

```
cluster.indices.tombstones.size 

当删除发生时，索引tombstone防止不属于集群的节点加入集群并重新导入索引，就像删除从未发出过一样。为了防止集群状态变得过大，我们只保留最后的cluster.indices.tombstones.size删除，默认值为500。如果您希望集群中没有节点并且遗漏超过500个删除操作，那么可以增加这个值。我们认为这是罕见的，因此默认。tombstones不会占用太多空间，但我们也认为像5万这样的数字可能太大了。
```



## 日志

```
PUT /_cluster/settings
{
  "transient": {
    "logger.org.elasticsearch.indices.recovery": "DEBUG"
  }
}
```



## 持久任务

插件可以创建一种称为持久任务的任务。这些任务通常是长期存在的任务，并以集群状态存储，从而允许在整个集群重新启动后恢复这些任务。

每次创建持久任务时，主节点负责将任务分配给集群的一个节点，然后被分配的节点将挑选任务并在本地执行。为节点分配持久任务的过程由以下属性控制，可以动态更新:

```
cluster.persistent_tasks.allocation.enable 
启用或禁用持久任务分配:
	all （default）允许将持久任务分配给节点
	none	对于任何类型的持久任务都不允许分配
```

此设置不会影响正在执行的持久任务。只有新创建的持久任务或必须重新分配的任务(例如，在节点离开集群之后)才会受到此设置的影响。