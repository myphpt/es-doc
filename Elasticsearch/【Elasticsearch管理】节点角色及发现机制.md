# 节点角色

任何时候启动一个Elasticsearch实例，都是在启动一个节点。连接节点的集合称为集群。如果你在运行一个Elasticsearch的节点，那么你有一个节点的集群。

默认情况下，集群中的每个节点都可以处理HTTP和传输流量。传输层专门用于节点和Java TransportClient之间的通信;HTTP层仅供外部REST客户端使用。

所有节点都知道集群中的所有其他节点，可以将客户端请求转发到适当的节点。除此之外，每个节点都有一个或多个用途:

## Master Eligible Node

 `node.master` 为true（默认值）的节点，这使得它有资格被选为控制集群的主节点。

主节点负责轻量级集群范围内的操作，例如创建或删除索引、跟踪哪些节点是集群的一部分，以及决定将哪些分片分配给哪些节点。对于集群运行状况来说，拥有稳定的主节点非常重要。

> 主节点必须能够访问data/目录(就像data节点一样)，因为在节点重启之间，主节点保存集群状态。

索引和搜索数据是CPU、内存和I/ o密集型操作，可能对节点的资源造成压力。为了确保您的主节点是稳定的，并且不会受到压力，在较大的集群中，设置专用的主节点和专用数据节点是个好主意。

虽然主节点也可以作为协调节点，将搜索和索引请求从客户端路由到数据节点，但最好不要使用专用的主节点。对于集群的稳定性来说，符合主节点要求的节点做的工作越少越好。

设置：

```
node.master: true 
node.data: false 
node.ingest: false 
cluster.remote.connect: false 
```

避免脑裂：`discovery.zen.minimum_master_nodes`应设置的主节点数：

(master_eligible_nodes / 2) + 1

默认值为1.



## Data Node

 `node.data` set to `true` (default)的节点，数据节点保存数据并执行数据相关的操作，如CRUD、搜索和聚合。

数据节点保存包含已建立索引的文档的分片。数据节点处理与数据相关的操作，如CRUD、搜索和聚合。这些操作是I/O密集型、内存密集型和cpu密集型。监控这些资源并在它们超载时添加更多数据节点是很重要的。

```
node.master: false 
node.data: true 
node.ingest: false 
cluster.remote.connect: false 
```



## Ingest node

`node.ingest` set to `true` (default)的节点，

摄入节点可以执行由一个或多个摄入处理器组成的预处理管道。根据摄取处理器执行的操作类型和所需的资源，有意义的做法是使用专用的摄取节点，它们只执行这个特定的任务。

```
node.master: false 
node.data: false 
node.ingest: true 
cluster.remote.connect: false 
```



## tribe node

部落节点，已被废弃，7版本删除



## Coordinating node

无固定配置，是一个动态节点角色。

如果去掉处理任务、保存数据和预处理文档的能力，那么就只剩下一个协调节点，它只能路由请求、减少搜索处理和分发批量索引。从本质上讲，协调节点负责负载均衡。

> 在集群中添加过多的仅协调节点会增加整个集群的负担，因为选出的主节点必须等待每个节点对集群状态更新的确认

```
node.master: false 
node.data: false 
node.ingest: false 
cluster.remote.connect: false 
```



## Data Path

设置方式1：

```
path.data:  /var/elasticsearch/data
```

设置方式2：

```
./bin/elasticsearch -Epath.data=/var/elasticsearch/data
```

数据路径可以由多个节点共享，甚至可以由来自不同集群的节点共享。这对于测试开发机器上的故障转移和不同配置非常有用。但是，在生产环境中，建议每个服务器只运行一个Elasticsearch节点。

默认情况下，Elasticsearch配置为防止多个节点共享相同的数据路径。要允许有多个节点(例如，在您的开发机器上)，请使用设置`node.max_local_storage_nodes`，并将其设置为一个大于1的正整数。

> 不要在同一个数据目录中运行不同类型的节点(例如，主节点，数据节点)。这可能会导致意外的数据丢失。



# 发现机制

## 前置概念

默认情况下，es进程会绑定在自己的回环地址上，也就是127.0.0.1，然后扫描本机上的9300~9305端口号，尝试跟那些端口上启动的其他es进程进行通信，然后组成一个集群。这对于在本机上搭建es集群的开发环境是很方便的。但是对于生产环境下的集群是不行的，需要将每台es进程绑定在一个非回环的ip地址上，才能跟其他节点进行通信，同时需要使用集群发现机制来跟其他节点上的es node进行通信。



## 基本描述

discovery模块负责发现集群中的节点，以及选择一个主节点。

注意，Elasticsearch是一个基于点对点的系统，节点之间直接通信，如果操作是委托/广播。所有的主要api(索引、删除、搜索)都不与主节点通信。

主节点的职责是维护全局集群状态，并在节点加入或离开集群时通过重新分配碎片进行操作。每次更改集群状态时，集群中的其他节点都知道该状态(方式取决于实际的发现实现)。



## 设置

```
cluster.name允许相同名称的Elasticsearch实例组成集群
```



## Zen discovery

Zen discovery是Elasticsearch的默认内置发现模块。它提供单播和基于文件的发现，并且可以扩展为支持云环境和通过插件进行的其他形式的发现。

Zen discovery与其他模块集成，例如，节点之间的所有通信都是使用传输模块（transport）完成的。



## Ping

在这个过程中，节点使用发现机制来查找其他节点。



## 列表

Zen discovery使用一个种子节点列表来开始发现过程。在启动时，或者在选择新的主节点时，Elasticsearch尝试连接到它列表中的每个种子节点，并与它们进行心跳连接，以查找其他节点并构建集群的完整图景。

> 因此在配置该列表时不需要将所有的节点都配置进去</u>，但是如果集群节点过多，且配置种子节点过少，则会有负载问题

默认情况下，有两种配置种子节点列表的方法:单播和基于文件。建议种子节点列表包含集群中master node的列表。



## 单播

单播发现配置一个用作种子节点的静态主机列表。这些主机可以指定为主机名或IP地址;指定为主机名的主机在每一轮ping期间被解析为IP地址。注意，如果您所处的环境中DNS解析随时间而变化，则可能需要调整JVM安全设置。

`discovery.zen.ping.unicast`

```
设置的主机静态列表。以是主机数组，也可以是逗号分隔的字符串。每个值都应该是host:port或host(其中port默认设置为`transport.profile .default.port`，如果没有设置则回落到transport.tcp.port)。注意，IPv6主机必须用括号括起来。该设置的默认值是127.0.0.1，[::1]
```

`discovery.zen.ping.unicast.resolve_timeout`

```
配置在每轮ping中等待DNS查找的时间。这被指定为一个时间单位，默认为5s。
```

单播发现使用传输模块来执行发现。



## 基于文件

除了主机提供的静态`discovery.zen.ping.unicast.hosts`设置时，可以通过外部文件提供主机列表。当这个文件发生变化时，Elasticsearch会重新加载它，这样种子节点列表就可以动态变化，而不需要重新启动每个节点。例如，这为一个在Docker容器中运行的Elasticsearch实例提供了一个方便的机制，当这些IP地址在节点启动时可能不知道时，它将动态地提供一个IP地址列表以用于Zen discovery。

若要启用基于文件的发现，请按如下方式配置文件主机提供程序:

```
discovery.zen.hosts_provider: file
```

然后以下面描述的格式创建`$ES_PATH_CONF/unicast_hosts.txt`文件。每当对`unicast_hosts.txt`文件进行更改时，Elasticsearch就会提取新的更改，并使用新主机列表。

注意，基于文件的发现插件增加了elasticsearch.yml的单播主机列表。如果在discovery.zen.ping.unicast.hosts中有有效的单播主机项。然后，除了unicast_hosts.txt中提供的主机外，还将使用它们。

`discovery.zen.ping.unicast。resolve_timeout`设置也适用于通过基于文件的发现通过地址指定的节点的DNS查找。这被指定为一个时间单位，默认为5s。

该文件的格式为每行指定一个节点条目。每个节点条目由主机(主机名或IP地址)和一个可选的传输端口号组成。如果指定了端口号，则必须紧跟在由:分隔的主机之后(在同一行上)。如果未指定端口号，则使用默认值9300。

例如，这是一个unicast_hosts.txt示例，用于包含四个参与单播发现的节点的集群，其中一些节点不在默认端口上运行:

```
10.10.10.5
10.10.10.6:9305
10.10.10.5:10005
# an IPv6 address
[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:9301
```

允许使用主机名而不是IP地址(类似于`discovery.zen.ping.unicast.hosts`)， IPv6地址必须用方括号指定，端口在方括号后面。

还可以向该文件添加注释。所有注释必须出现在以#开头的行上(也就是说，注释不能从行中间开始)。



# 主节点选举

作为ping进程的一部分，可以选择或加入集群的master 。这是自动完成的。

`discovery.zen.ping_timeout`：决定节点在开始选举或加入现有集群之前需要等待多长时间。默认为3s

`discovery.zen.join_timeout`：节点加入集群的超时时间，默认为60s

`discovery.zen.minimum_master_nodes`：形成集群的主节点数量，推荐设置为集群数量的二分之一加一，防止脑裂。

`discovery.zen.master_election.ignore_non_master_pings`：是否忽略来自非master角色的节点心跳，默认为false。



`discovery.zen.ping_timeout`(默认为3s)决定节点在开始选举或加入现有集群之前需要等待多长时间。在此超时间隔内将发送三个ping。如果超时后无法达成任何决定，ping进程将重新启动。

在缓慢或繁忙的网络中，在做出选举决定之前，3秒可能不足以让一个节点意识到其环境中的其他节点。在这种情况下，应该小心地增加超时时间，因为这会减慢选举过程。一旦一个节点决定加入一个已经形成的集群，它将向主集群(`discovery.zen.join_timeout`)发送一个连接请求，默认超时为ping超时的20倍，即发送20次。

当主节点停止或遇到问题时，集群节点重新开始ping并选择新的主节点。当一个节点单方面的认为主服务器已经失败时，这种轮询机制还可以防止网络(部分)故障。在这种情况下，节点将简单地从其他节点获取当前活动master的消息。

如果`discovery.zen.master_election.ignore_non_master_pings`为true，来自不符合主条件的节点的ping(节点node.master为false)被忽略在master选举;默认值为false。可以通过设置node.master为false来排除节点成为主节点。

`discovery.zen.minimum_master_nodes`设置需要加入新当选的master的主合格节点的最小数量，以便完成选举，并使当选的节点接受其mater身份。相同的设置控制应属于任何活动集群的活动主合格节点的最小数量。如果不满足此要求，活动主节点将退出，并开始新的主节点选举。此设置必须设置为主合格节点的仲裁。建议避免只有两个合格的master节点，因为2的仲裁是2。因此，丢失任何一个主节点都将导致无法操作的集群。



# 集群故障

有两个正在运行故障检测机制。第一种方法是通过主服务器ping集群中的所有其他节点，并验证它们是活动的。另一种方法，每个节点ping master来验证它是否仍然存在，或者是否需要重新启动一个选举过程。

以下设置使用discovery.zen.fd前缀控制故障检测过程:

ping_interval：节点被ping的频率。默认为1s。

ping_timeout：等待ping响应的时间，默认为30秒。

ping_retries：有多少ping失败/超时导致一个节点被认为失败。默认为3。



# 集群状态更新

`discovery.zen.commit_timeout`：master获取确认的超时

`discovery.zen.publish_timeout`：master发布状态的超时

master节点是集群中唯一可以更改集群状态的节点。master node每次会处理一个集群状态的更新事件，并应用这次状态更新，然后将更新后的状态发布到集群中所有的node上去。每个node接收master发布的消息，但并不提交。如果master没有在一定时间内从(由`discovery.zen.commit_timeout`设置控制，默认为30秒)minimum_master_nodes节点获取确认，则该集群状态将拒绝更改。

一旦有足够多的节点响应，就会提交集群状态，并向所有节点发送一条消息。然后，节点继续将新的集群状态应用到它们自己的内部状态。主节点等待所有节点响应，直到超时，然后继续处理队列中的下一个更新。`discovery.zen.publish_timeout`默认设置为30秒，从发布开始的那一刻开始计时。这两个超时设置都可以通过集群动态更改



# 无master的集群操作

要使集群完全可操作，它必须有一个活动的master节点，运行的符合条件的master节点的数量必须满足`discovery.zen.minimum_master_nodes`设置(如果设置)。no_master_block设置控制在没有活动的master时应该拒绝哪些操作。

`discovery.zen.no_master_block`设置有两个有效选项:

all ：节点上的所有操作——即。读和写都将被拒绝。这也适用于对集群状态的读或写操作，如get索引设置、put映射和集群状态操作。

write：(默认)写操作将被拒绝。根据最后已知的集群配置，读取操作将会成功。这可能导致读取部分陈旧数据，因为此节点可能与集群的其他节点隔离。

`discovery.zen.no_master_block`设置不适用于基于节点的api(例如集群状态、节点信息和节点状态api)。对这些api的请求将不会被阻止，并且可以在任何可用节点上运行。



# 单节点集群

`discovery.type`设置指定Elasticsearch是否应该形成多节点集群。默认情况下，Elasticsearch在形成集群时发现其他节点，并允许其他节点稍后加入集群。如果discovery.type设置为single-node，Elasticsearch只形成单节点集群。



# 发现过程

（1）已经初步配置好了各个节点，首先通过network.host绑定到了非回环的ip地址，从而可以跟其他节点通信
 （2）通过`discovery.zen.ping.unicast.hosts`配置一批unicast中间路由的node
 （3）所有node都可以发送ping消息到路由node，再从路由node获取cluster state
 （4）接着所有node会选举出一个master
 （5）所有node都会跟master进行通信，然后加入master的集群
 （6）要求cluster.name必须一样，才能组成一个集群
 （7）node.name就标识出了每个node我们自己设置的一个名称