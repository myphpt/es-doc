[TOC]

# 备份和恢复

## 快照和恢复

快照是从正在运行的Elasticsearch集群中获取的备份。可以获取单个索引或整个集群的快照，并将其存储在共享文件系统上的存储库中，支持S3、HDFS、Azure、谷歌云存储等远程存储库。

快照是递增的。这意味着在创建索引快照时，Elasticsearch将避免复制存储在存储库中作为同一索引的早期快照的一部分的任何数据。因此，非常频繁地为集群进行快照是非常有效的。

可以通过恢复命令将快照恢复到正在运行的集群中。在恢复索引时，可以更改恢复的索引的名称及其一些设置，从而在如何使用快照和恢复功能方面提供了很大的灵活性。

仅通过获取所有节点的数据目录的副本来备份Elasticsearch集群是不可取的。Elasticsearch在运行时可能会更改其数据目录的内容，这意味着复制其数据目录不能获得一致的数据备份。试图从这样的备份中恢复集群可能会失败，报告损坏和/或丢失文件，或者悄无声息地丢失一些数据。备份集群的唯一可靠方法是使用快照和恢复功能。



## 版本兼容性

快照包含组成索引的磁盘上数据结构的副本。这意味着快照只能恢复到Elasticsearch版本，以便读取索引:

5中创建的索引的快照。可以恢复到6。

具体版本的兼容性请参考要恢复版本的官网说明。



## 存储库

在执行快照和恢复操作之前，必须先注册快照存储库。我们建议为每个主要版本创建一个新的快照存储库。有效的存储库设置取决于存储库类型。

如果将相同的快照存储库注册为多个集群，则只有一个集群应该具有对该存储库的写访问权。连接到该存储库的所有其他集群应该将存储库设置为readonly模式。

> 快照格式可以在主要版本之间更改，因此，如果在不同版本上的集群试图编写相同的存储库，那么由一个版本编写的快照可能对另一个版本不可见，存储库可能会被破坏。虽然将存储库设置为只读(除了一个集群之外)应该可以用于多个主要版本不同的集群，但它不是受支持的配置。

```
PUT /_snapshot/my_backup
{
  "type": "fs",
  "settings": {
    "location": "my_backup_location"
  }
}
```

要检索关于已注册存储库的信息，请使用GET请求:

```
GET /_snapshot/my_backup
```

若要检索有关多个存储库的信息，请指定以逗号分隔的存储库列表。在指定存储库名称时，还可以使用*通配符。例如，以下请求检索关于所有以repo启动或包含备份的快照存储库的信息:

```
GET /_snapshot/repo*,*backup*
```

要检索关于所有已注册快照存储库的信息，请省略存储库名称或指定_all:

```
GET /_snapshot
GET /_snapshot/_all
```



## 共享文件系统

共享文件系统存储库(“type”:“fs”)使用共享文件系统存储快照。为了注册共享文件系统存储库，有必要将相同的共享文件系统挂载到所有主节点和数据节点上的相同位置。此位置(或其父目录之一)必须在该路径中注册。所有主节点和数据节点上的repo设置。

假设共享文件系统被挂载到/mount/backup /my_fs_backup_location，那么应该在`elasticsearch.yml` 文件中添加以下设置

```
path.repo: ["/mount/backups", "/mount/longterm_backups"]
```

path.repo设置支持microsoftwindows UNC路径，只要至少服务器名和共享被指定为前缀和反斜杠被正确转义:

```
path.repo: ["\\\\MY_SERVER\\Snapshots"]
```

重启所有节点后，可以使用以下命令注册名为my_fs_backup的共享文件系统存储库:

```
PUT /_snapshot/my_fs_backup
{
    "type": "fs",
    "settings": {
        "location": "/mount/backups/my_fs_backup_location",
        "compress": true
    }
}
```

如果存储库位置被指定为一个相对路径，那么这个路径将根据path.repo中指定的第一个路径来解析:

```
PUT /_snapshot/my_fs_backup
{
    "type": "fs",
    "settings": {
        "location": "my_fs_backup_location",
        "compress": true
    }
}
```



## 快照设置

```
location 
快照的位置。强制性的。

compress 
打开快照文件的压缩。压缩仅应用于元数据文件(索引映射和设置)。数据文件没有被压缩。默认值为true。

chunk_size 
如果需要，大文件可以在快照期间被分解成块。块大小可以以字节或使用大小值表示法来指定，即1g, 10m, 5k。默认值为null(不限块大小)。

max_restore_bytes_per_sec 
设置每个节点的恢复速率。默认值为每秒40mb。

max_snapshot_bytes_per_sec 
设置每个节点快照速率。默认值为每秒40mb。

readonly 
设置存储库只读。默认值为false。
```



## 只读存储库

URL存储库(“type”:“URL”)可以用作访问共享文件系统存储库创建的数据的另一种只读方式。在URL参数中指定的URL应该指向共享文件系统存储库的根。支持以下设置:

```
url  快照的位置。强制性的。
```

URL存储库支持以下协议:“http”、“https”、“ftp”、“file”和“jar”。带有http:、https:和ftp: URL的URL存储库必须通过在 `repositories.url.allowed_urls`中指定允许的URL白名单。此设置支持在主机、路径、查询和片段中使用通配符。例如:

```
repositories.url.allowed_urls: ["http://www.example.org/root/*", "https://*.mydomain.com/*?*#*"]
```

带有文件的URL存储库:URL只能指向路径中注册的位置。repo设置类似于共享文件系统存储库。



## 仅源快照

通过源存储库，可以创建最小的、仅限源的快照，这些快照最多可以减少50%的磁盘空间。仅源快照包含存储的字段和索引元数据。它们不包括索引或文档值结构，并且在还原时不可搜索。恢复仅源快照之后，必须将数据重新索引到新索引中。

源存储库委托给另一个快照存储库进行存储。

只有在启用了_source字段且不应用源筛选时，才支持仅源快照。当您恢复一个仅源快照:

- 恢复的索引是只读的，只能为match_all搜索或scroll 请求提供支持重新索引的服务。
- 不支持除match_all和_get请求之外的查询。
- 恢复的索引的映射为空，但原始映射可从types顶级元元素中获得。

当你创建一个源存储库时，你必须指定快照存储的委托存储库的类型和名称:

```
PUT _snapshot/my_src_only_repository
{
  "type": "source",
  "settings": {
    "delegate_type": "fs",
    "location": "my_backup_location"
  }
}
```



## 存储库验证

注册存储库时，会立即在所有主节点和数据节点上验证它，以确保它在集群中当前存在的所有节点上都有效。验证参数可以用来显式禁用存储库验证时，登记或更新存储库:

```
PUT /_snapshot/my_unverified_backup?verify=false
{
  "type": "fs",
  "settings": {
    "location": "my_unverified_backup_location"
  }
}
```

验证过程也可以通过运行以下命令手动执行:

```
POST /_snapshot/my_unverified_backup/_verify
```

它返回存储库成功验证的节点列表，如果验证过程失败，则返回错误消息。



## 快照

存储库可以包含同一个集群的多个快照。快照是通过集群中的唯一名称标识的。通过执行以下命令，可以在存储库my_backup中创建名为snapshot_1的快照:

```
PUT /_snapshot/my_backup/snapshot_1?wait_for_completion=true
```

wait_for_completion参数指定请求是否应该在快照初始化之后立即返回(默认情况下)，或者等待快照完成。在快照初始化期间，关于以前所有快照的信息都被加载到内存中，这意味着在大型存储库中，即使wait_for_completion参数被设置为false，该命令也可能需要几秒钟(甚至几分钟)才能返回。

默认情况下，将创建集群中所有打开和启动索引的快照。可以通过在快照请求的主体中指定索引列表来更改此行为。

```
PUT /_snapshot/my_backup/snapshot_2?wait_for_completion=true
{
  "indices": "index_1,index_2",
  "ignore_unavailable": true,
  "include_global_state": false
}
```

可以使用支持多索引语法的索引参数指定应该包含在快照中的索引列表。快照请求还支持ignore_unavailable选项。将其设置为true将导致在快照创建期间忽略不存在的索引。默认情况下，当ignore_unavailable选项没有被设置并且索引丢失时，快照请求将失败。

通过将include_global_state设置为false，可以防止将集群全局状态存储为快照的一部分。默认情况下，如果参与快照的一个或多个索引没有所有的主分片可用，则整个快照将失败。可以通过将partial设置为true来更改此行为。

快照名称可以使用Date Math表达式自动派生，与创建新索引类似。注意，需要对特殊字符进行URI编码。

例如，创建一个名称为当前日期的快照，如snapshot-2018.05.11，可以通过以下命令来实现:

```
# PUT /_snapshot/my_backup/<snapshot-{now/d}>
PUT /_snapshot/my_backup/%3Csnapshot-%7Bnow%2Fd%7D%3E
```

索引快照进程是递增的。在创建索引快照的过程中，Elasticsearch会分析存储库中已经存储的索引文件的列表，并只复制自上次快照以来创建或更改的文件。这允许多个快照以紧凑的形式保存在存储库中。快照过程以非阻塞方式执行。所有的索引和搜索操作都可以对快照的索引继续执行。

但是，快照代表创建快照时索引的时间点视图，因此快照开始后不会出现在快照过程开始后添加到索引的记录。 对于已启动且当前未重定位的主要分片，快照过程将立即启动。 在1.2.0版之前，如果群集具有参与快照的索引的任何重定位或初始化主键，则快照操作将失败。 从1.2.0版开始，Elasticsearch在对快照进行快照之前，等待碎片的重新定位或初始化完成。

除了创建每个索引的副本外，快照进程还可以存储全局集群元数据，其中包括持久的集群设置和模板。瞬态设置和注册快照存储库不作为快照的一部分存储。

集群中任何时间都只能执行一个快照过程。 在创建特定分片的快照时，该分片无法移动到另一个节点，这可能会干扰重新平衡过程和分配筛选。 快照完成后，Elasticsearch将只能将分片移动到另一个节点（根据当前的分配过滤设置和重新平衡算法）。

快照创建后，可以使用以下命令获取关于该快照的信息:

```
GET /_snapshot/my_backup/snapshot_1
```

该命令返回关于快照的基本信息，包括开始和结束时间、创建快照的Elasticsearch版本、所包含索引的列表、快照的当前状态以及在快照期间发生的故障列表。快照状态可以是

```
IN_PROGRESS   正在运行
SUCCESS 
FAILED 
PARTIAL 	存在分片失败
INCOMPATIBLE 	不兼容
```

与存储库类似，关于多个快照的信息可以一次性查询，也支持通配符:

```
GET /_snapshot/my_backup/snapshot_*,some_other_snapshot
```

所有当前存储在存储库中的快照可以使用以下命令列出:

```
GET /_snapshot/my_backup/_all
```

如果一些快照不可用，则命令失败。布尔参数ignore_unavailable可用于返回当前可用的所有快照。

从成本和性能的角度来看，在基于云的存储库中获取存储库中的所有快照可能会付出高昂的代价。 如果唯一需要的信息是存储库中的快照名称/ uuid以及每个快照中的索引，则可以将可选的布尔参数verbose设置为false，以对存储库中的快照执行更高效且更具成本效益的检索。 请注意，将verbose设置为false会忽略有关快照的所有其他信息，例如状态信息，快照分片的数量等。verbose参数的默认值为true。

可以使用以下命令检索当前运行的快照:

```
GET /_snapshot/my_backup/_current
```

可以使用以下命令从存储库中删除快照:

```
DELETE /_snapshot/my_backup/snapshot_2
```

当从存储库中删除快照时，Elasticsearch删除与已删除快照关联且不被任何其他快照使用的所有文件。如果在创建快照时执行删除快照操作，快照进程将中止，所有作为快照进程一部分创建的文件将被清除。因此，可以使用delete快照操作取消错误启动的长时间运行的快照操作。

一个存储库可以取消注册使用以下命令:

```
DELETE /_snapshot/my_backup
```

当储存库未注册时，Elasticsearch只删除对储存库存储快照的位置的引用。快照本身是保持原样的。



## 恢复

快照可以恢复使用以下命令:

```
POST /_snapshot/my_backup/snapshot_1/_restore
```

默认情况下，恢复快照中的所有索引，而不恢复集群状态。可以选择应该恢复的索引，也可以通过在恢复请求体中使用索引和include_global_state选项来恢复全局集群状态。索引列表支持多索引语法。rename_pattern和rename_replacement选项还可以用于使用正则表达式在恢复时重命名索引，正则表达式支持引用这里解释的原始文本。将include_aliases设置为false，以防止别名与相关索引一起还原

```
POST /_snapshot/my_backup/snapshot_1/_restore
{
  "indices": "index_1,index_2",
  "ignore_unavailable": true,
  "include_global_state": true,
  "rename_pattern": "index_(.+)",
  "rename_replacement": "restored_index_$1"
}
```

可以在正常运行的群集上执行还原操作。 但是，仅当现有索引关闭且其分片数量与快照中的索引数量相同时，才能还原该索引。 如果关闭了已还原的索引，则还原操作会自动打开它们；如果集群中不存在已创建的索引，则会自动创建新的索引。 如果使用include_global_state还原了群集状态（默认为false），则会添加群集中当前不存在的已还原模板，并使用已还原的模板替换具有相同名称的现有模板。 还原的持久性设置将添加到现有的持久性设置中。



## 部分恢复

默认情况下，如果一个或多个参与该操作的索引没有所有可用分片的快照，则整个还原操作将失败。 例如，如果某些分片无法快照，则会发生这种情况。 通过将partial设置为true，仍然可以恢复此类索引。 请注意，在这种情况下，只有成功快照的分片将被还原，所有丢失的分片将被重新创建为空。



## 改变索引设置

大多数索引设置可以在恢复过程中被覆盖。例如，以下命令将恢复索引index_1而不创建任何副本，同时切换回默认的刷新间隔:

```
POST /_snapshot/my_backup/snapshot_1/_restore
{
  "indices": "index_1",
  "index_settings": {
    "index.number_of_replicas": 0
  },
  "ignore_index_settings": [
    "index.refresh_interval"
  ]
}
```

请注意，一些设置，如index.number_of_shards在还原操作期间无法更改。

```
curl -XPUT "http://localhost:9200/_snapshot/my_es_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "my_es_location"
  }
}'


curl -XGET "http://localhost:9200/_snapshot/my_es_backup"

curl -XPOST "http://localhost:9200/_snapshot/my_es_backup/snapshot_es/_restore"

curl -XGET "http://localhost:9200/_cat/indices?v&index=es*"
```



## 快照状态

当前运行的快照列表及其详细状态信息可以使用以下命令获得:

```
GET /_snapshot/_status
```

在这种格式下，命令将返回关于所有当前运行的快照的信息。通过指定存储库名称，可以将结果限制到特定的存储库:

```
GET /_snapshot/my_backup/_status
```

如果同时指定了存储库名称和快照id，该命令将返回给定快照的详细状态信息，即使当前没有运行:

```
GET /_snapshot/my_backup/snapshot_1/_status
```

输出由不同部分组成。 stats子对象提供有关快照文件的数量和大小的详细信息。 由于快照是增量快照，因此仅复制存储库中尚未存在的Lucene段，因此stats对象包含快照引用的所有文件的总计部分，以及实际需要存储的那些文件的增量部分。 作为增量快照的一部分进行复制。 如果快照仍在进行中，则还有一个“已处理”部分，其中包含有关正在复制的文件的信息。

> 注意:属性number_of_files, processed_files, total_size_in_bytes和processed_size_in_bytes使用是为了向后兼容旧的5.x和6.x版本。这些字段将在Elasticsearch v7.0.0中删除。
>

还支持多个id:

```
GET /_snapshot/my_backup/snapshot_1,snapshot_2/_status
```



## 监控快照/恢复进程

有几种方法可以监视快照的进度并在进程运行时恢复它们。这两个操作都支持wait_for_completion参数，该参数将阻塞客户端，直到操作完成。这是用于获得操作完成通知的最简单方法。

快照操作也可以通过定期调用快照信息来监控:

```
GET /_snapshot/my_backup/snapshot_1
```

请注意，快照信息操作与快照操作使用相同的资源和线程池。因此，在快照处理大型分片时执行快照信息操作会导致快照信息操作在返回结果之前等待可用资源。对于非常大的分片，等待时间可能非常长。

要获得关于快照的更直接和完整的信息，可以使用快照状态命令:

```
GET /_snapshot/my_backup/snapshot_1/_status
```

快照info方法只返回关于正在进行的快照的基本信息，而快照状态返回参与快照的每个分片的当前状态的完整分解。

还原过程依赖于Elasticsearch的标准恢复机制。因此，可以使用标准恢复监视服务来监视恢复的状态。 执行还原操作时，集群通常进入红色状态。 之所以发生这种情况，是因为还原操作始于“还原”还原索引的主分片。 在此操作期间，主分片变得不可用，这表明它处于红色状态。 一旦完成主分片的恢复，Elasticsearch将切换到标准恢复过程，该过程此时将创建所需数量的副本，集群将切换为黄色状态。 一旦创建了所有必需的副本，群集便切换到绿色状态。

集群运行状况操作仅提供恢复进程的高级状态。通过监控索引恢复过程，可以更详细地了解恢复过程的当前状态。

## 停止当前正在运行的快照和恢复操作

快照和还原框架仅允许一次运行一个快照或一个还原操作。 如果当前运行的快照被错误地执行或花费了很长时间，则可以使用快照删除操作将其终止。 快照删除操作检查删除的快照当前是否正在运行，如果正在运行，则删除操作会在从存储库删除快照数据之前停止该快照。

```
DELETE /_snapshot/my_backup/snapshot_1
```

恢复操作使用标准的分片恢复机制。因此，可以通过删除正在还原的索引来取消当前正在运行的恢复操作。请注意，此操作将从集群中删除所有已删除索引的数据。



## 集群块对快照和恢复操作的影响

许多快照和还原操作受集群和索引块的影响。 例如，注册和注销存储库需要写入全局元数据访问。 快照操作要求所有索引及其元数据以及全局元数据均可读。 还原操作要求全局元数据是可写的，但是在还原过程中会忽略索引级别块，因为索引实际上是在还原过程中重新创建的。 请注意，存储库内容不属于集群，因此集群块不会影响内部存储库操作，例如列出或删除已注册存储库中的快照。



## 来源

https://www.elastic.co/guide/en/elasticsearch/reference/current/snapshot-restore.html