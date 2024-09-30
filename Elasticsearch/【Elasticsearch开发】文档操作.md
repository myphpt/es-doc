# 读写模式

## 概述

Elasticsearch中的每个索引都被划分为分片，每个分片可以有多个副本。这些副本称为复制组，在添加或删除文档时必须保持同步。如果我们不这样做，从一个副本读取将导致非常不同的结果从另一个。保持分片副本同步并从其中读取数据的过程称为数据复制模型。

Elasticsearch的数据复制模型是基于主备模型的，并且在Microsoft Research的PacificA论文中进行了很好的描述。该模型基于从复制组中获得一个副本充当主分片。其他副本称为副本分片。主分片用作所有索引操作的主入口点。它负责验证它们并确保它们是正确的。一旦索引操作被master接受，master还负责将该操作复制到其他副本。



## 写入模式

Elasticsearch中的每个索引操作首先使用路由解析到一个复制组(通常基于文档ID)。一旦确定了复制组，操作将在内部转发到组的当前主分片。主分片负责验证操作并将其转发给其他副本。由于副本可以离线，所以主分片不需要复制到所有副本。

另外，Elasticsearch维护一个接收操作的分片副本列表。这个列表称为同步副本，由master维护。顾名思义，这些是一组“良好的”分片副本，保证处理了所有已向用户确认的索引和删除操作。master负责维护此不变量，因此必须将所有操作复制到此集合中的每个副本。

主分片遵循以下基本流程:

1. 验证传入操作，如果结构上无效就拒绝它(例如:有一个对象字段，其实需要一个数字)
2. 在本地执行操作，例如索引或删除相关文档。这也将验证字段的内容，并在需要时拒绝(例如:keyword值对于Lucene索引来说太长)。
3. 将操作转发给当前同步副本集中的每个副本。如果有多个副本，则并行执行。
4. 一旦所有副本都成功地执行了操作并响应了master，master就会向客户端确认请求的成功完成。



## 写入失败处理

索引过程中会出现很多问题——磁盘可能损坏，节点之间可能断开连接，或者一些配置错误可能导致在副本上的操作失败，尽管它在主分片上是成功的。这种情况并不常见，但是主分片必须对它们做出反应。

在主分片 本身失败的情况下，托管主分片 的节点将向master发送关于它的消息。索引操作将等待master将其中一个replicas 提升为新的主分片(默认情况下最多1分钟)。然后，该操作将被转发到新的主分片 进行处理。请注意，master还监视节点的运行状况，当持有主分片的节点由于网络问题与集群隔离时，决定是否主动降级主分片。

一旦在主分片上成功执行了该操作，当在副本分片分片上执行主分片操作时，主分片就必须处理潜在的故障。 这可能是由于副本分片上的实际故障或由于网络问题导致操作无法到达副本分片（或阻止副本分片进行响应）引起的。 所有这些都具有相同的最终结果：作为同步副本集一部分的副本分片错过了将要确认的操作。 即主副本的数据同步失败。

为了避免违反一致性，主分片 向master 发送一条消息，请求从同步副本集中删除有问题的分片。 master 仅在确认分片移除后，主分片 才确认操作。 请注意，master 还将指示另一个节点开始构建新的分片副本，以将系统恢复到正常状态。

在将操作转发到replicas时，主分片 将使用replicas 来验证它自己仍然是活动的主分片。 如果主分片 由于网络分区（或较长的GC）而被隔离，则它可能会继续处理传入的索引操作，然后再意识到已被降级。 来自陈旧的主分片的操作将被replicas拒绝。 当主分片 收到来自副本分片的响应，因为它不再是主分片 而拒绝了它的请求时，它将与master 联系，并得知已被替换。 然后，该操作将路由到新的主分片。



## 如果没有副本会发生什么？

假设一个极端场景，由于索引配置导致所有副本都失败，在这种情况下，主分片 在处理操作时没有任何外部验证，这将导致很多问题。

因为，主分片 不能自己让其他分片失败，而要请求master 代表它这样做。这意味着master 知道主分片 是唯一一个好的副本。因此，我们可以保证master 不会将任何其他(过时的)分片副本提升为新的主分片 ，并且任何索引到主分片 的操作都不会丢失。当然，由于此时我们只使用数据的单一副本运行，物理硬件问题可能会导致数据丢失。



## 读取模式

在Elasticsearch中的读取可以是非常轻量级的ID查找，也可以是使用复杂聚合的大型搜索请求，占用大量CPU资源。主备模型的优点之一是，它保持所有分片副本完全相同(未提交的操作除外)。因此，一个同步副本就足以满足读请求。

当节点接收到读取请求时，该节点负责将其转发到持有相关分片的节点，整理响应，并响应客户端。我们称该节点为该请求的协调节点。基本流程如下:

1. 将读请求解析到相关的分片。注意，由于大多数搜索将被发送到一个或多个索引，它们通常需要从多个分片读取数据，每个分片表示数据的不同子集。
2. 从分片复制组中选择每个相关分片的活动副本。这可以是主分片，也可以是副本。默认情况下，Elasticsearch将简单地在分片副本之间循环。
3. 向所选副本发送分片级读取请求。
4. 合并结果并响应。注意，在通过ID查找的情况下，只有一个分片是相关的，可以跳过这一步。



## 读取失败处理

当一个分片未能响应读取请求时，协调节点将从同一复制组中选择另一个副本，并将分片级别搜索请求发送给该副本。重复的失败会导致没有可用的分片副本。在某些情况下， Elasticsearch 不会等待问题得到解决，而是直接响应部分结果，并在响应的_shards头中显示，比如search。



## 一些简单的含义

这些基本流中的每一个都决定了Elasticsearch作为读写系统的行为方式。此外，由于读和写请求可以并发执行，这两个基本流彼此交互。这有一些内在的含义:

1. 在正常操作下，每个读操作对每个相关的复制组执行一次。只有在失败的情况下，才执行相同分片的多个副本执行相同的搜索。
2. 由于主分片先在本地建立索引，然后复制请求，因此并发读取可能在确认更改之前就已经看到了更改。
3. 当只维护数据的两个副本时，此模型可以是容错的。这与基于quorum的系统形成了对比，在基于quorum的系统中，用于容错的最小副本数为3。



## 失败

失败的情况可能有以下两种：

1、一个慢分片拖慢整个索引

由于主分片 等待在每次操作期间设置的同步副本中的所有副本，因此一个缓慢的分片可能会降低整个复制组的速度。这是我们为读取效率所付出的代价。当然，一个缓慢的分片也会减慢已经被路由到它的不走运的搜索。

2、脏读

独立的主分片 可以公开未被确认的写操作。这是因为隔离的主分片 只有在向其副本发送请求或向master发送请求时才会意识到它是隔离的。此时，操作已经被索引到主分片 中，可以通过并发读取进行读取。Elasticsearch通过每秒ping master (默认情况下)和在不知道master 的情况下拒绝索引操作来减轻这种风险。



# index（插入）

## 插入

```
PUT twitter/_doc/1
{
    "user" : "kimchy",
    "post_date" : "2009-11-15T14:12:12",
    "message" : "trying out Elasticsearch"
}
```

在successful至少为1的情况下，索引操作成功。成功完成索引操作后，副本分片可能不会全部启动（默认情况下，仅需要主分片，但是可以更改此行为）。

在这种情况下，基于number_of_replicas设置，total将等于总分片，而successful将等于已启动的分片的数目。 如果没有失败，则失败为0。

```
{
  "_index" : "twitter",
  "_type" : "_doc",
  "_id" : "2",
  "_version" : 1,
  "result" : "created",
  "_shards" : {
    "total" : 2,   //指示索引操作应该在多少个分片副本(主分片和复制分片)上执行。
    "successful" : 1,
    "failed" : 0
  },
  "_seq_no" : 0,
  "_primary_term" : 1
}

```

## 自动创建

如果索引不存在，索引操作会自动创建索引，并应用已配置的任何索引模板。索引操作还会为指定的类型创建动态类型映射(如果还不存在)。默认情况下，如果需要，指定类型的映射定义将自动添加新的字段和对象。

自动索引创建由`action.auto_create_index`设置控制。 

1、此设置默认为true，这意味着总是自动创建索引。 

2、通过将此设置的值更改为模式的逗号分隔列表，可以仅对匹配某些模式的索引自动创建索引。 

3、通过在列表中的模式前面加上+或-来明确允许和禁止使用它。 

4、通过将此设置更改为false来完全禁用它。

```
PUT _cluster/settings
{
    "persistent": {
        "action.auto_create_index": "twitter,index10,-index1*,+ind*" 
    }
}

PUT _cluster/settings
{
    "persistent": {
        "action.auto_create_index": "false" 
    }
}

//true默认值
PUT _cluster/settings
{
    "persistent": {
        "action.auto_create_index": "true" 
    }
}
```

## version（版本号）

每个索引文档都有一个版本号。关联的版本号作为对索引请求的响应的一部分返回。当指定版本参数时，控制操作要针对的文档的版本。

版本控制用例的一个很好的例子是执行事务性的先读后更新。从最初读取的文档指定一个版本，可以确保在此期间没有发生任何更改(在读取以进行更新时，建议将preference设置为_primary)。

```
PUT twitter/_doc/1?version=2
{
    "message" : "elasticsearch now has versioning support, double cool!"
}
```

注意:版本控制是完全实时的，不受搜索操作接近实时方面的影响。如果没有提供版本，则在不进行任何版本检查的情况下执行操作。

> 版本只是记录对数据的操作次数，并不对数据进行校验，因此，插入相同数据时，版本号依然递增。

默认情况下，使用内部版本控制，从1开始，随着每次更新和删除而递增。另外，版本号可以用外部值补充(例如，如果在数据库中维护)。要启用此功能，`version_type`应该设置为`external`。

提供的值必须是大于或等于0的long数值，并且小于9.2e+18。在使用外部版本类型时，系统不会检查匹配的版本号，而是检查传递给索引请求的版本号是否大于当前存储的文档的版本。如果为真，将索引文档并使用新版本号。如果提供的值小于或等于存储的文档的版本号，则会发生版本冲突，索引操作将失败。

另一个好处是，不需要严格地维护因更改源数据库而执行的异步索引操作的顺序，只要使用源数据库的版本号即可。如果使用外部版本控制，即使使用数据库中的数据更新Elasticsearch索引的简单情况也会得到简化，因为如果索引操作出于某种原因而出现顺序混乱，则只会使用最新版本。



### 版本类型

`internal`：只有给定版本与存储文档的版本相同时，才索引文档。

**`external` or `external_gt`**  ：只有在给定的版本严格高于存储文档的版本或者没有现有文档时，才索引文档。给定的版本将作为新版本使用，并与新文档存储在一起。提供的版本必须是非负的long数值。

**`external_gte`**  ：只有在给定版本等于或大于存储文档的版本时才索引文档。如果没有现有文档，操作也会成功。给定的版本将作为新版本使用，并与新文档存储在一起。提供的版本必须是非负的long数值。

注意:external_gte版本类型用于特殊用例，应该谨慎使用。如果使用不当，可能会导致数据丢失。还有另一种选项force，但不赞成使用它，因为它会导致主分片和副本分片分离。



## 操作类型

索引操作还接受一个op_type，该op_type可用于强制执行create操作，从而允许“put-if-absent”行为。当使用create时，如果索引中已经存在该id的文档，则索引操作将失败。

```
PUT twitter/_doc/1?op_type=create
{
    "user" : "kimchy",
    "post_date" : "2009-11-15T14:12:12",
    "message" : "trying out Elasticsearch"
}
PUT twitter/_doc/1/_create
{
    "user" : "kimchy",
    "post_date" : "2009-11-15T14:12:12",
    "message" : "trying out Elasticsearch"
}
```

参数：create 和 index



## ID自动生成

索引操作可以在不指定id的情况下执行。在这种情况下，将自动生成一个id。另外，op_type将自动设置为create。下面是一个例子(注意这里用的POST代替PUT):

```
POST twitter/_doc/
{
    "user" : "kimchy",
    "post_date" : "2009-11-15T14:12:12",
    "message" : "trying out Elasticsearch"
}
```



## Routing（路由）

默认情况下，通过使用文档id值的hash来控制分片位置(或路由)。对于更显式的控制，可以使用路由参数根据每项操作直接指定发送到分片使用的hash值。

```
POST twitter/_doc?routing=kimchy
{
    "user" : "kimchy",
    "post_date" : "2009-11-15T14:12:12",
    "message" : "trying out Elasticsearch"
}
```

在设置显式映射时，可以选择使用routing字段来指导索引操作从文档本身提取路由值。这需要额外的文档解析过程(非常小的)开销。如果定义了_routing映射并将其设置为required，那么如果没有提供或提取路由值，索引操作将失败。

```
PUT /twitter
{
  "mappings": {
    "_doc": {
      "_routing": {
        "required": "true"
      },
      "properties": {
        "message": {
          "type": "keyword"
        }
      }
    }
  }
}
```



## 分布式

索引操作根据主分片的路由(请参阅上面的路由部分)被定向到主分片，并在包含该分片的实际节点上执行。主分片完成操作后，如果需要，更新将被分发给适用的副本。



## 等待活跃分片

> 默认index.write.wait_for_active_shards值为1，即只等待主分片响应即可

为了提高系统写操作的弹性，可以将索引操作配置为在继续操作之前等待一定数量的活动副本分片。如果没有所需数量的活动副本分片，则写操作必须等待并重试，直到所需的分片副本启动或出现超时。

默认情况下，写操作只等待主分片处于活动状态后再继续(即`wait_for_active_shards=1`)。这个默认值可以通过设置`index.write.wait_for_active_shards`在索引设置中动态覆盖。要更改每个操作的这种行为，可以使用wait_for_active_shards请求参数。

有效值是所有或任何正整数，直到索引中每个分片配置的副本总数(number_of_replicas+1)为止。指定负数或大于分片副本数量的数字将抛出错误。

例如，假设我们有一个包含三个节点(A、B和C)的集群，我们创建一个副本数设置为3的索引(产生4个副本分片，比节点多一个副本)。如果我们尝试索引操作，默认情况下，该操作将只确保每个分片的主副本在继续之前可用。这意味着，即使B和C崩溃，而A承载了主分片副本，索引操作仍将只处理数据的一个副本。

如果wait_for_active_shards设置请求3，然后索引操作应满足3个副本分片活跃的要求,因为有三个活跃集群中的节点拥有每一个分片的副本。但是，如果我们将wait_for_active_shards设置为all(或者设置为4，这是相同的)，索引操作将不会继续进行，因为我们在索引中没有每个shard活动的所有4个副本。该操作将超时，除非集群中出现一个新节点来承载分片的第四个副本。

需要注意的是，此设置极大地减少了写操作未写入所需数量的分片副本的可能性，但它并不能完全消除这种可能性，因为此检查发生在写操作开始之前。一旦进行了写操作，仍然可能在任意数量的分片副本上失败，但在主分片上仍然成功。写操作响应的_shards部分显示了复制成功/失败的分片副本的数量。



## 重刷新

控制此请求所做的更改何时对搜索可见。

> 默认重刷新间隔为1s



## Noop更新

当使用Index更新文档时，即使文档没有改变，也会创建文档的新版本。如果不能接受，可以使用将`detect_noop`设置为`true`的update请求。该选项在索引请求上不可用，因为索引请求不获取旧源，并且不能将其与新源进行比较。

没有硬性规定什么时候noop更新是不可接受的。它是许多因素的组合，比如数据源发送更新(实际上是noops)的频率，以及在接收更新时，Elasticsearch每秒在分片上运行多少次查询。



## timeout（超时）

在执行索引操作时，分配给执行索引操作的主分片可能不可用。造成这种情况的一些原因可能是主分片当前正在从网关恢复或正在进行重新定位。可以使用timeout参数显式地指定等待的时间。

> 默认情况下，索引操作将等待主分片变为可用的时间最长为1分钟，然后失败并以错误响应。

```
PUT twitter/_doc/1?timeout=5m
{
    "user" : "kimchy",
    "post_date" : "2009-11-15T14:12:12",
    "message" : "trying out Elasticsearch"
}
```



# Bulk（批量插入）



## 从文件导入（shell）

文件内容

```
action_and_meta_data\n
optional_source\n
action_and_meta_data\n
optional_source\n
....
action_and_meta_data\n
optional_source\n
```

注意:数据的最后一行必须以换行符\n结束。每个换行字符前面可以有一个回车\r。当向这个端点发送请求时，Content-Type头应该设置为application/x-ndjson。

如果要向curl提供文本文件输入，则必须使用——data-binary标志，而不是纯的-d。后者不保留新行。例子:

```
$ cat requests
{ "index" : { "_index" : "test", "_type" : "_doc", "_id" : "1" } }
{ "field1" : "value1" }

$ curl -s -H "Content-Type: application/x-ndjson" -XPOST localhost:9200/_bulk --data-binary "@requests"; echo
```



## 批量请求

```
POST _bulk
{ "index" : { "_index" : "test", "_type" : "_doc", "_id" : "1" } }
{ "field1" : "value1" }
{ "delete" : { "_index" : "test", "_type" : "_doc", "_id" : "2" } }
{ "create" : { "_index" : "test", "_type" : "_doc", "_id" : "3" } }
{ "field1" : "value3" }
{ "update" : {"_id" : "1", "_type" : "_doc", "_index" : "test"} }
{ "doc" : {"field2" : "value2"} }

格式：
/_bulk
/{index}/_bulk
{index}/{type}/_bulk
```

批量操作的响应是一个大型JSON结构，其中包含执行的每个操作的单个结果。单个操作的失败不会影响其他操作。



## 注意事项

1. 为尽可能快地进行处理，由于一些操作将被重定向到其他节点上的其他分片，因此在接收节点端只解析action_meta_data。使用此协议的客户机应该尝试在客户端做类似的事情，并尽可能减少缓冲。
2. 在单个批量调用中没有要执行的“正确”操作数量。您应该试验不同的设置，以找到适合您特定工作负载的最佳大小。
3. 如果使用HTTP方式，请确保客户端不发送HTTP块，因为这会降低速度。
4. 每个大容量项都可以使用version字段包含版本值。它根据_version映射自动执行索引/删除操作的行为。它还支持version_type
5. 每个批量项可以包含使用routing字段的路由值。它根据_routing映射自动遵循索引/删除操作的行为。
6. 在进行批量调用时，您可以设置wait_for_active_shards参数，以要求在开始处理批量请求之前，活动的副本分片的最小数量。
7. 只有接收大容量请求的分片会受到refresh的影响。想象一个bulk?refresh=wait_for请求，其中包含三个文档，恰好路由到包含5个分片的索引中的不同分片。请求将只等待这三个分片刷新。其他两个组成索引的分片根本不参与_bulk请求。



## 更新

在使用 `update` 操作时，retry_on_conflict可以作为操作本身中的字段(不在有效负载中)，以指定在版本冲突的情况下应该重试更新的次数。

update操作有效负载支持以下选项:doc(部分文档)、upsert、doc_as_upsert、script、params(脚本)、lang(脚本)和_source。

```
POST _bulk
{ "update" : {"_id" : "1", "_type" : "_doc", "_index" : "index1", "retry_on_conflict" : 3} }
{ "doc" : {"field" : "value"} }
{ "update" : { "_id" : "0", "_type" : "_doc", "_index" : "index1", "retry_on_conflict" : 3} }
{ "script" : { "source": "ctx._source.counter += params.param1", "lang" : "painless", "params" : {"param1" : 1}}, "upsert" : {"counter" : 1}}
{ "update" : {"_id" : "2", "_type" : "_doc", "_index" : "index1", "retry_on_conflict" : 3} }
{ "doc" : {"field" : "value"}, "doc_as_upsert" : true }
{ "update" : {"_id" : "3", "_type" : "_doc", "_index" : "index1", "_source" : true} }
{ "doc" : {"field" : "value"} }
{ "update" : {"_id" : "4", "_type" : "_doc", "_index" : "index1"} }
{ "doc" : {"field" : "value"}, "_source": true}
```

# Get（获取）

## 获取一个文档

```
GET twitter/_doc/0
```



## 验证是否存在

```
HEAD twitter/_doc/0
```



## 实时

默认情况下，get请求是实时的，不受索引refresh速率的影响(当数据对搜索可见时)。如果文档已经更新，但还没有刷新，那么get请求将发出一个刷新调用，使文档可见。这还将使自上次刷新以来所更改的其他文档可见。为了禁用实时GET，可以将realtime参数设置为false。

> 调用GET获取一个文档时，会隐式的调用一个refresh，使数据可搜索。
>
> GET twitter/_doc/1?realtime=false



## source获取

```
GET twitter/_doc/1/_source
GET twitter/_doc/1/_source?_source_include=*.id&_source_exclude=entities'
```

注意，source端点还有一个HEAD变体，可以有效地测试文档_source是否存在。如果在映射中禁用了_source，则现有文档将没有source。

```
HEAD twitter/_doc/1/_source
```

默认情况下，get操作返回source字段的内容，除非您使用了stored_fields参数，或者source字段被禁用。您可以关闭source检索使用source参数:

```
GET twitter/_doc/0?_source=false
```

如果您只需要完整_source中的一个或两个字段，您可以使用_source_include和_source_exclude参数来包含或过滤您需要的部分。这对于大型文档尤其有用，因为部分检索可以节省网络开销。两个参数都采用逗号分隔的字段列表或通配符表达式。

```
GET twitter/_doc/0?_source_include=*.id&_source_exclude=entities
```

也可以这么写:

```
GET twitter/_doc/1?_source=user
```

## 存储字段

get操作允许指定一组存储字段，这些字段将通过传递stored_fields参数返回。如果未存储所请求的字段，则将忽略它们。

```
PUT twitter
{
   "mappings": {
      "_doc": {
         "properties": {
            "counter": {
               "type": "integer",
               "store": false
            },
            "tags": {
               "type": "keyword",
               "store": true
            }
         }
      }
   }
}
```

不标注存储的字段，GET时自动忽略

```
GET twitter/_doc/1?stored_fields=tags,counter
```

从文档本身获取的字段值总是作为数组返回。由于没有存储counter字段，所以get请求在尝试获取stored_fields时简单地忽略它。

## 路由

当索引使用外部值控制路由时，为了获得一个文档，也应该提供路由值。

```
PUT twitter/_doc/2?routing=user
{
    "user" : "kimchy",
    "post_date" : "2009-11-15T14:12:12",
    "message" : "trying out Elasticsearch"
}

//获取路由文档
GET twitter/_doc/2?routing=user
```

上面的内容将获得id为2的文档，但将根据user进行路由。注意，在没有正确路由的情况下发出get将导致无法获取文档。



## 首选

控制要在哪个分片副本上执行get请求的首选项。默认情况下，该操作在分片副本之间随机分配。

首选项可以设置为:

```
_primary（过时，7.0删除）
_local 
自定义
将使用一个自定义值来确保将相同的分片用于相同的自定义值。当在不同的刷新状态中碰到不同的分片时，这可以帮助实现“跳值”。示例值可以是web会话id或用户名之类的东西。
```

根据首选搜索：

```
GET twitter/_doc/1?preference=_local
```





## Refresh

可以将refresh参数设置为true，以便在get操作之前刷新相关的分片，并使其可搜索。在将其设置为true之前，应该仔细考虑并确认这不会导致系统负载过重(并降低索引速度)。

```
GET twitter/_doc/1?refresh=false
```



## 分布式

get操作被hash到一个特定的分片id中，然后被重定向到该分片id中的一个副本，并返回结果。副本集是主分片及其在该分片id组中的副本。这意味着我们拥有的副本越多，GET效果就越好。



## 版本支持

只有当文档的当前版本等于指定的版本时，才能使用version参数来检索文档。此行为对于所有版本类型都是相同的，只有版本类型FORCE例外，它总是检索文档。注意，强制版本类型是不赞成的。

在内部，Elasticsearch将旧文档标记为已删除，并添加一个全新的文档。旧版本的文档不会立即消失，尽管您无法访问它。当您继续索引更多数据时，Elasticsearch会在后台清理已删除的文档。





# Multi Get（批量获取）

Multi GET允许基于索引、类型(可选)和id(可能还有路由)获取多个文档。响应包括一个文档数组，其中包含与原始multi-get请求相对应的所有已获取文档(如果某个特定get失败，则在响应中包含包含此错误的对象)。

```
GET /_mget
{
    "docs" : [
        {
            "_index" : "test",
            "_type" : "_doc",
            "_id" : "1"
        },
        {
            "_index" : "test",
            "_type" : "_doc",
            "_id" : "2"
        }
    ]
}
```

也可以这么写：

```
GET /test/_doc/_mget
{
    "ids" : ["1", "2"]
}
```

或者：

```
GET /test/_doc/_mget
{
    "docs" : [
        {
            "_id" : "1"
        },
        {
            "_id" : "2"
        }
    ]
}
```



## Source过滤

默认情况下，将为每个文档(如果存储)返回source字段。与get请求类似，您可以使用source参数只检索source的一部分(或者根本不检索)。您还可以使用url参数source、_source_include和_source_exclude来指定默认值，当没有针对每个文档的指令时将使用这些默认值。

```
GET /_mget
{
    "docs" : [
        {
            "_index" : "test",
            "_type" : "_doc",
            "_id" : "1",
            "_source" : false
        },
        {
            "_index" : "test",
            "_type" : "_doc",
            "_id" : "2",
            "_source" : ["field3", "field4"]
        },
        {
            "_index" : "test",
            "_type" : "_doc",
            "_id" : "3",
            "_source" : {
                "include": ["user"],
                "exclude": ["user.location"]
            }
        }
    ]
}
```

可以指定每个文档获取的特定存储字段，类似于get的stored_fields参数。

```
GET /_mget
{
    "docs" : [
        {
            "_index" : "test",
            "_type" : "_doc",
            "_id" : "1",
            "stored_fields" : ["field1", "field2"]
        },
        {
            "_index" : "test",
            "_type" : "_doc",
            "_id" : "2",
            "stored_fields" : ["field3", "field4"]
        }
    ]
}
```

或者，您可以在查询字符串中指定stored_fields参数作为应用于所有文档的默认值。

```
GET /test/_doc/_mget?stored_fields=field1,field2
{
    "docs" : [
        {
            "_id" : "1" 
        },
        {
            "_id" : "2",
            "stored_fields" : ["field3", "field4"] 
        }
    ]
}
```

## 路由

您也可以指定路由值作为参数:

```
GET /_mget?routing=key1
{
    "docs" : [
        {
            "_index" : "test",
            "_type" : "_doc",
            "_id" : "1",
            "routing" : "key2"
        },
        {
            "_index" : "test",
            "_type" : "_doc",
            "_id" : "2"
        }
    ]
}
```

`document test/_doc/2`将从对应于路由密钥key1的shard中获取，而`document test/_doc/1`将从对应于路由密钥key2的shard中获取。



# Update（更新）

该操作从索引中获取文档(与分片并置)，运行脚本(使用可选的脚本语言和参数)，并返回结果索引(也允许删除或忽略操作)。它使用版本控制来确保在“get”和“reindex”期间没有发生更新。



## 更新请求

注意，此操作仍然意味着对文档进行完整的reindex ，它只是删除了一些网络往返，并减少了get和索引之间版本冲突的机会。要使用此特性，需要启用_source字段。

```
PUT test/_doc/1
{
    "counter" : 1,
    "tags" : ["red"]
}
```



## 更新部分文档

```
POST test/_doc/1/_update
{
    "doc" : {
        "name" : "new_name"
    }
}
```



## 检测Noop更新

如果在发送请求之前名称是new_name，那么整个更新请求将被忽略。如果请求被忽略，则响应中的result元素返回noop。

```
POST test/_doc/1/_update
{
    "doc" : {
        "name" : "new_name"
    },
    "detect_noop": false
}
```



## 参数

### retry_on_conflict

在更新的get和indexing阶段之间，另一个进程可能已经更新了同一文档。默认情况下，更新将失败，并出现版本冲突异常。retry_on_conflict参数控制在最终引发异常之前重试更新的次数。

```
POST twitter/_doc/1/_update?retry_on_conflict=3
{
  "doc": {
    "message": "trying out"
  }
}
```

或者

```
POST twitter/_doc/1/_update
{
  "retry_on_conflict": 2,
  "doc": {
    "message": "trying out"
  }
}
```



### routing 

路由用于将更新请求路由到正确的分片，并在被更新的文档不存在时为upsert请求设置路由。不能用于更新现有文档的路由。

### timeout 

等待分片可用的超时。

### wait_for_active_shards 

在继续更新操作之前需要活动的副本分片的数量

### refresh 

控制此请求所做的更改何时对搜索可见

### _source 

控制是否以及如何在响应中返回更新的源。默认情况下，更新后的源不会返回。

### version 

更新请求在内部使用了Elasticsearch的版本控制支持，以确保文档在更新期间不会发生变化。您可以使用version参数来指定只有当文档的版本与指定的版本相匹配时才应该更新文档。



> 更新请求不支持外部(版本类型External & external_gte)或强制(版本类型force)版本控制，因为这会导致Elasticsearch版本号与外部系统不同步

# Update By Query（批量更新）

使用查询DSL限制_update_by_query。这将为用户kimchy更新twitter索引中的所有文档:

```
POST twitter/_update_by_query?conflicts=proceed
{
  "query": { 
    "term": {
      "user": "kimchy"
    }
  }
}
```

基本用法参照Delete_by_query 使用

# Delete（删除）

```
DELETE /twitter/_doc/1
```

索引的每个文档都有版本。在删除文档时，可以指定版本，以确保我们试图删除的相关文档实际上已经被删除，并且在此期间没有发生更改。对文档执行的每个写操作(包括删除操作)都会导致其版本增加。删除后的文档的版本号在短时间内仍然可用，以便控制并发操作。

被删除文档的版本仍然可用的时间长度由`index.gc_deletes`索引设置决定，默认值为60秒。

```
DELETE /twitter/_doc/1?routing=kimchy
```

在发出删除请求时，您可以设置`wait_for_active_shards`参数，以要求在开始处理删除请求之前，活动的分片副本的最小数量。

```
DELETE /twitter/_doc/1?timeout=5m
```

适用参数：

```
wait_for_active_shards：活跃分片
?refresh：重刷新
?timeout：超时   默认为1分钟
```



# delete_by_query（批量删除）

## 查询并删除

```
POST twitter/_delete_by_query
{
  "query": { 
    "match": {
      "message": "some message"
    }
  }
}
```

当索引启动时，`_delete_by_query`获取它的快照，并使用`internal`版本删除它发现的内容。这意味着，如果文档在捕获快照和处理删除请求之间发生更改，您将会遇到版本冲突。当版本匹配时，删除文档。

由于internal版本不支持值0作为有效版本号，因此不能使用_delete_by_query删除版本为0的文档，因此请求将失败。

在执行delete_by_query期间，将顺序执行多个搜索请求，以便找到所有要删除的匹配文档。每当发现一批文档时，就会执行相应的批量请求来删除所有这些文档。如果搜索或批量请求被拒绝，delete_by_query依赖默认策略重试被拒绝的请求(最多10次)。

达到最大重试限制将导致_delete_by_query中止，并在响应的失败中返回所有失败。已经执行的删除仍然保留。换句话说，进程没有回滚，只是中止了。当第一个失败导致中止时，失败的大容量请求返回的所有失败都在failed元素中返回;因此，有可能会有很多失败的实体。

## 容许失败

如果您想计数版本冲突而不是导致它们中止，那么在url上设置conflicts=proceed或在请求主体中设置“conflicts”:“proceed”。

```
POST twitter/_doc/_delete_by_query?conflicts=proceed
{
  "query": {
    "match_all": {}
  }
}
```

也可以同时删除多个索引和多种类型的文档，就像search请求一样:

```
POST twitter,blog/_docs,post/_delete_by_query
{
  "query": {
    "match_all": {}
  }
}
```

## 路由

如果您提供routing，那么routing被复制到scroll query，限制进程到匹配该路由值的分片:

```
POST twitter/_delete_by_query?routing=1
{
  "query": {
    "range" : {
        "age" : {
           "gte" : 10
        }
    }
  }
}
```

## 批次大小

默认情况下，_delete_by_query使用1000的滚动批。您可以更改批大小与scroll_size URL参数:

```
POST twitter/_delete_by_query?scroll_size=5000
{
  "query": {
    "term": {
      "user": "kimchy"
    }
  }
}
```



## 参数

除了像pretty这样的标准参数外，Delete By Query API还支持refresh、wait_for_completion、wait_for_active_shards、timeout和scroll。



### refresh

发送refresh将在请求完成后刷新delete by查询中涉及的所有分片。这与Delete API的刷新参数不同，后者只会刷新接收到删除请求的分片。另外，与Delete API不同，它不支持`wait_for`。



### wait_for_completion

如果请求包含`wait_for_completion=false`，那么Elasticsearch将执行一些检查，启动请求，然后返回一个任务，该任务可用于task请求来取消或获得该任务的状态。Elasticsearch还将在.tasks/task/${taskId}处创建该任务的记录作为文档。你可以选择保留或删除。当任务完成或被删除时，Elasticsearch收回它使用的空间。



### wait_for_active_shards

`wait_for_active_shards`控制在继续处理请求之前必须激活一个shard的多少个副本分片。timeout控制每个写请求等待不可用分片变为可用的时间。两者的工作方式与它们在Bulk中的工作方式完全相同。



### scroll

由于delete_by_query使用滚动搜索，您还可以指定scroll参数来控制它保持“搜索上下文”存活的时间，例如`?scroll=10m`，默认为5分钟。



### requests_per_second（吞吐率）

`requests_per_second`可以设置为任何正的十进制数(1.4、6、1000等)，并通过填充每个批处理的等待时间来调节_delete_by_query发出批删除操作的速率。可以通过将requests_per_second设置为-1来禁用。

限流是通过在批处理之间等待来完成的，以便可以给_delete_by_query内部使用的滚动提供一个考虑请求的超时。 请求时间是批大小除以requests_per_second与花费的时间之间的差。 默认情况下，批处理大小为1000，因此，如果requests_per_second设置为500：

```
吞吐率 = 总请求数 / 处理这些请求的总完成时间
target_time = 1000 / 500 per second = 2 seconds
wait_time = target_time - write_time = 2 seconds - 0.5 seconds = 1.5 seconds
```

因为批处理是作为单个_bulk请求发出的，所以大批处理会导致Elasticsearch创建许多请求，然后在开始下一组请求之前等待一段时间。默认值是-1。

## 响应格式

```json
{
  "took" : 147,
  "timed_out": false,   //是否超时，true
  "total": 119,
  "deleted": 119,
  "batches": 1,
  "version_conflicts": 0,
  "noops": 0,   //对于delete by查询，该字段总是等于0。它的存在只是为了使按查询删除、按查询更新和重索引api返回具有相同结构的响应。
  "retries": {     //通过“按删除”查询尝试的重试次数。批量是重试的批量操作的数量，搜索是重试的搜索操作的数量。
    "bulk": 0,
    "search": 0
  },
  "throttled_millis": 0, //请求休眠的毫秒数，以符合requests_per_second。
  "requests_per_second": -1.0,   //在delete by查询期间每秒有效执行的请求数。
  "throttled_until_millis": 0,//在_delete_by_query响应中，该字段应该始终等于零。它只有在使用Task API时才有意义，其中它表示下一次(以纪元以来的毫秒为单位)将再次执行一个经过调整的请求，以符合requests_per_second。
  "failures" : [ ] //如果在过程中出现任何不可恢复的错误，则会出现一系列失败。如果非空，则请求会因为这些失败而中止。使用批处理实现按查询删除，任何失败都会导致整个进程中止，但当前批处理中的所有失败都会收集到数组中。您可以使用conflicts选项来防止在版本冲突时终止重新索引。
}
```



## 任务查询

获取任何运行的按查询删除请求的状态与任务:

```
GET _tasks?detailed=true&actions=*/delete/byquery
```

此对象包含实际状态。它就像响应json一样，添加了重要的total字段。total是重新索引期望执行的操作总数。您可以通过添加更新的、创建的和删除的字段来估计进度。当它们的总和等于字段总数时，请求将完成。

根据task id获取（阻塞直到完成）

```
GET _tasks/B-M3lfhbQfS88kIq64pECQ:51016?wait_for_completion=false
```

取消

```
POST _tasks/B-M3lfhbQfS88kIq64pECQ:51016/_cancel
```



## 设置限流

```
POST _delete_by_query/r1A2WoRbTwKZ516z6NEs5A:36619/_rethrottle?requests_per_second=-1
```



## Slice  ID删除

按查询删除支持Slice 滚动，以并行化删除。这种并行化可以提高效率，并提供一种方便的方法来将请求分解成更小的部分。

通过提供Slice  id和每个请求的Slice 总数，手动按查询删除:

```
POST twitter/_delete_by_query
{
  "slice": {
    "id": 0,
    "max": 2
  },
  "query": {
    "range": {
      "likes": {
        "lt": 10
      }
    }
  }
}

//验证
GET _refresh
POST twitter/_search?size=0&filter_path=hits.total
{
  "query": {
    "range": {
      "likes": {
        "lt": 10
      }
    }
  }
}

//获得的响应
{
  "hits": {
    "total": 0
  }
}
```



## Slice 滚动删除

还可以使用Slice 滚动在_uid上进行分片，让按查询删除自动并行化。使用`slices`来指定要使用的Slice 数量:

```
POST twitter/_delete_by_query?refresh&slices=5
{
  "query": {
    "range": {
      "likes": {
        "lt": 10
      }
    }
  }
}

//验证
POST twitter/_search?size=0&filter_path=hits.total
{
  "query": {
    "range": {
      "likes": {
        "lt": 10
      }
    }
  }
}

//响应
{
  "hits": {
    "total": 0
  }
}
```



## 选择合适的slice数量

如果自动分片，将slices设置为auto将为大多数索引选择一个合理的数字。如果您是手动分片或调优自动分片，请使用这些指导原则：

- 当slices的数量与索引中的分片数量相等时，查询性能的效率最高。如果这个数字很大(例如，500)，则选择较低的数字，因为太多的slices会影响性能。设置大于分片数量的slices通常不会提高效率，而且会增加开销。
- 删除性能随可用资源的slices线性变化。
- 查询或删除性能在运行时主要取决于被重新索引的文档和集群资源。