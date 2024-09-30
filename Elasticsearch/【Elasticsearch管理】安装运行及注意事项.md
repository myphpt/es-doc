# 运行Elasticsearch

https://www.elastic.co/guide/en/elasticsearch/reference/7.17/targz.html

[TOC]

## 下载安装包

```
curl -L -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.9.1-linux-x86_64.tar.gz
curl -L -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.17.9-linux-x86_64.tar.gz

```

或者

```
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.9.1-linux-x86_64.tar.gz
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.17.9-linux-x86_64.tar.gz
```



## 节点启动

索引自动创建

```
action.auto_create_index：*

自定义自动创建索引
action.auto_create_index: .monitoring*,.watches,.triggered_watches,.watcher-history*,.ml*
```

静态参数，在配置文件中配置

多配置启动

```
./elasticsearch -Epath.data=data2 -Epath.logs=log2
./elasticsearch -Epath.data=data3 -Epath.logs=log3
```

后台启动

```
./bin/elasticsearch -d -p pid
```

自定义配置启动

```
./bin/elasticsearch -d -Ecluster.name=my_cluster -Enode.name=node_1

环境变量：ES_PATH_CONF
```



## 节点停止

```
pkill -F pid
kill `cat pid`
kill -SIGTERM 15516
```



# 重要配置

集群名称

```
cluster.name: logging-prod
```

节点名称

```
node.name: prod-data-2

// 使用环境变量
node.name: ${HOSTNAME}
```

数据存储路径

```
path:
  data: /var/data/elasticsearch
  logs: /var/log/elasticsearch
  
// 多路径配置
path:
  data:
    - /mnt/elasticsearch_1
    - /mnt/elasticsearch_2
    - /mnt/elasticsearch_3
```

网络地址

```
network.host: 192.168.1.10
network.host: 0.0.0.0
```



发现机制

```
discovery.seed_hosts:
   - 192.168.1.10:9300
   - 192.168.1.11 
   - seeds.mydomain.com 
   - [0:0:0:0:0:ffff:c0a8:10c]:9301 
```

此设置提供了集群中符合主条件的其他节点的列表，这些节点可能处于活动状态并可联系，以便为发现过程提供种子。该设置接受集群中所有符合主条件的节点的地址的YAML序列或数组。每个地址可以是一个IP地址，也可以是通过DNS解析为一个或多个IP地址的主机名。

```
cluster.initial_master_nodes: 
   - master-node-a
   - master-node-b
   - master-node-c
```

当您第一次启动Elasticsearch集群时，集群引导步骤将确定在第一次选举中计算其投票的主合格节点集。在开发模式下，如果没有配置发现设置，这个步骤将由节点本身自动执行。

> 集群首次形成成功后，需要移除每个节点配置中的Initial_master_nodes设置。当重新启动集群或向现有集群添加新节点时，不要使用此设置。



# JVM内存设置

设置最小堆大小(Xms)和最大堆大小(Xmx)相等。

对Elasticsearch可用的堆越多，它可以用于缓存的内存就越多。但是请注意，太多的堆会导致垃圾收集暂停时间过长。

将Xmx设置为不超过物理RAM的50%，以确保有足够的物理RAM留给内核文件系统缓存。

不要将Xmx设置为超过JVM用于压缩对象指针的截止时间(压缩oops);确切的上限有所不同，但接近32gb。您可以通过在日志中查找如下的行来验证您是否在限制之下:

```
heap size [1.9gb], compressed ordinary object pointers [true]
```

更好的是，尝试保持低于阈值为零压缩oops;确切的上限有所不同，但是在大多数系统上26 GB是安全的，但是在某些系统上可以大到30 GB。您可以通过使用JVM选项-XX:+UnlockDiagnosticVMOptions -XX:+PrintCompressedOopsMode启动Elasticsearch来验证是否在限制之下，寻找如下一行:

```
heap address: 0x000000011be00000, size: 27648 MB, zero based Compressed Oops
```

显示启用了从零开始压缩的oops，而不是

```
heap address: 0x0000000118400000, size: 28672 MB, Compressed Oops with base: 0x00000001183ff000
```

## 设置JVM内存

文件配置方式

```
vim jvm.options 

-Xms4g
-Xmx4g
```

环境变量方式

```
注释掉文件配置
ES_JAVA_OPTS="-Xms2g -Xmx2g" ./bin/elasticsearch 
ES_JAVA_OPTS="-Xms4000m -Xmx4000m" ./bin/elasticsearch 
```



## heap dumps

```
-XX:HeapDumpPath=... 
```

默认情况下,Elasticsearch配置JVM堆转储内存溢出异常的默认数据目录(/var/lib/elasticsearch 这是RPM和Debian软件包的数据目录)。如果此路径不适合接收堆转储，在jvm.options文件中设置-XX:HeapDumpPath=的值。

如果指定目录，JVM将根据运行实例的PID为堆转储生成一个文件名。如果指定的是固定文件名而不是目录，那么当JVM需要对内存不足异常执行堆转储时，该文件必须不存在，否则堆转储将失败。

## GC Log

```
# Turn off all previous logging configuratons
-Xlog:disable

# Default settings from JEP 158, but with `utctime` instead of `uptime` to match the next line
-Xlog:all=warning:stderr:utctime,level,tags

# Enable GC logging to a custom location with a variety of options
-Xlog:gc*,gc+age=trace,safepoint:file=/opt/my-app/gc.log:utctime,pid,tags:filecount=32,filesize=64m

# 错误日志 这些是JVM在遇到致命错误(比如分段错误)时产生的日志
-XX:ErrorFile=文件目录
```



## 临时目录

如果打算在Linux上长时间运行.tar.gz发行版，那么应该考虑为Elasticsearch创建一个专用的临时目录，该目录不位于清除旧文件和目录的路径下。该目录应该设置权限，以便只有Elasticsearch运行的用户才能访问它。然后在启动Elasticsearch之前设置$ES_TMPDIR环境变量指向它。





# 系统配置

## 文件描述符

Elasticsearch使用了很多文件描述符或文件句柄。耗尽文件描述符可能是灾难性的，很可能会导致数据丢失。确保将运行Elasticsearch的用户打开的文件描述符的数量限制提高到65,536或更高。

```
/etc/security/limits.conf

* soft nofile 65536
* hard nofile 131072
* soft nproc 2048
* hard nproc 4096

或
elasticsearch  -  nofile  65536

或
elasticsearch启动前root权限执行 ulimit -n 65536
```

检查

```
GET _nodes/stats/process?filter_path=**.max_file_descriptors
```



## 关闭交换区

大多数操作系统尝试为文件系统缓存使用尽可能多的内存，并急切地交换未使用的应用程序内存。这可能导致JVM堆的部分或甚至其可执行页被交换到磁盘。

交换对性能和节点稳定性非常不利，应该不惜一切代价避免。它可能导致垃圾收集持续几分钟而不是几毫秒，并可能导致节点响应缓慢，甚至断开与集群的连接。在弹性分布式系统中，让操作系统杀死节点更有效。

有三种方法可以禁用交换。首选的选项是完全禁用交换。如果不能这样做，则选择将切换最小化还是内存锁定取决于您的环境。

方式一：

注意：通常，Elasticsearch是机器上运行的唯一服务，其内存使用由JVM选项控制。应该没有必要启用交换。

临时关闭交换区

```
sudo swapoff -a
```

永久关闭交换区

```
vim /etc/fstab
注释掉带有swap的分区
```



方式二：

Linux系统上可用的另一个选项是确保sysctl值vm.swappiness设置为1。这减少了内核交换的倾向，在正常情况下不应该导致交换，但在紧急情况下仍然允许整个系统交换。

```
查看
cat /proc/sys/vm/swappiness
30
该值越小, 表示越大限度的使用物理内存, 最小值=0
该值越大, 表示越积极的使用 swap 交换分区, 最大值=100

临时设置
sysctl vm.swappiness=1

永久设置
echo "vm.swappiness=1" >> /etc/sysctl.conf
```



方式三：

```
vim config/elasticsearch.yml

bootstrap.memory_lock: true
```

集群查看

```
GET _nodes?filter_path=**.mlockall
```

锁定失败：最大的可能是用户没有权限

```
root用户下执行：ulimit -l unlimited
或者
vim  /etc/security/limits.conf

设置memlock  unlimited 
* soft memlock  unlimited
* hard memlock  unlimited


```

另一个原因是临时目录挂载失败

```
export ES_JAVA_OPTS="$ES_JAVA_OPTS -Djna.tmpdir=<path>"
./bin/elasticsearch
```



## 虚拟内存

Elasticsearch默认使用一个mmapfs目录来存储其索引。默认操作系统对mmap计数的限制可能太低，这可能会导致内存不足异常。

```
vi /etc/sysctl.conf
添加下面配置：
vm.max_map_count=655360 
并执行命令：sysctl -p
```



## 线程数

Elasticsearch为不同类型的操作使用许多线程池。重要的是，它能够在需要时创建新线程。确保Elasticsearch用户可以创建的线程数至少是4096个。

```
vim /etc/security/limits.conf
设置nproc 为4096
```



## TCP重传重试

```
sysctl -w net.ipv4.tcp_retries2=5

vim /etc/sysctl.conf
net.ipv4.tcp_retries2=5
```

重启



# 引导程序检测

总的来说，我们有很多用户遇到意外问题的经验，因为他们没有配置重要的设置。在以前版本的Elasticsearch中，这些设置中的一些错误配置会被记录为警告。可以理解，用户有时会错过这些日志消息。为了确保这些设置得到应有的重视，Elasticsearch在启动时进行了bootstrap检查。

这些自举检查检查各种Elasticsearch和系统设置，并将它们与Elasticsearch操作的安全值进行比较。如果Elasticsearch处于开发模式，任何失败的引导检查都会在Elasticsearch日志中以警告的形式出现。如果Elasticsearch处于生产模式，任何失败的引导检查将导致Elasticsearch拒绝开始。

有一些引导检查，总是强制防止Elasticsearch运行与不兼容的设置。这些检查单独记录。



## 开发模式和生产模式

默认情况下，Elasticsearch绑定到环回地址，用于HTTP和传输(内部)通信。对于下载和使用Elasticsearch以及日常开发来说，这是很好的，但对于生产系统就没用了。要加入一个集群，Elasticsearch节点必须可以通过传输通信到达。若要通过非环回地址加入集群，节点必须将transport绑定到非环回地址，并且不使用单节点发现。

因此，如果一个Elasticsearch节点不能通过非环回地址与另一台机器组成集群，则我们认为它处于开发模式;反之，如果它可以通过非环回地址加入集群，则认为它处于生产模式。

注意，可以通过HTTP独立地配置HTTP和传输。`http.host` 和`transport.host`;这对于将单个节点配置为可以通过HTTP访问以进行测试而不触发生产模式非常有用。



我们认识到，有些用户需要将传输绑定到外部接口，以测试他们对传输客户机的使用情况。对于这种情况，我们提供`single-node`(设置`discovery.type`为`single-node`);在这种情况下，节点将选择自己为主节点，并且不会与任何其他节点加入集群。

如果在生产环境中运行单个节点，则有可能逃避引导检查(通过不将传输绑定到外部接口，或者通过将传输绑定到外部接口并将发现类型设置为single-node)。

对于这种情况，可以通过设置系统属性es.enforce.bootstrap.check设置为true强制执行引导检查(通过设置JVM选项或添加-Des.enforce.bootstrap.checks=true来设置该值。对于环境变量ES_JAVA_OPTS)。如果您处于这种特殊情况，我们强烈建议您这样做。此系统属性可用于强制执行独立于节点配置的引导检查。



## 堆内存检测

如果JVM以不相等的初始堆大小和最大堆大小启动，那么当JVM堆在系统使用期间调整大小时，它很容易出现暂停。为了避免这些调整大小的暂停，最好在启动JVM时使初始堆大小等于最大堆大小。另外,如果`bootstrap.memory_lock`启用，JVM将在启动时锁定堆的初始大小。如果初始堆大小不等于最大堆大小，那么在重新调整大小后，不会将所有JVM堆锁定在内存中。

要通过堆大小检查，必须配置堆大小。



## 文件描述符检测

文件描述符是一种Unix结构，用于跟踪打开的“文件”。但是在Unix中，一切都是一个文件。例如，“文件”可以是物理文件、虚拟文件(例如，/proc/loadavg)或网络套接字。Elasticsearch需要大量的文件描述符(例如，每个shard由多个段和其他文件组成，加上与其他节点的连接，等等)。这个引导检查在OS X和Linux上执行。

要通过文件描述符检查，您可能必须配置文件描述符。



## 内存锁检测

当JVM进行一次主要的垃圾收集时，它会触及堆的每个页面。如果这些页面中的任何一个被交换到磁盘，那么它们必须被交换回内存中。这会导致大量磁盘抖动，而Elasticsearch更愿意使用这些磁盘来服务请求。

有几种方法可以配置系统，使其不允许交换。一种方法是请求JVM通过mlockall (Unix)或虚拟锁(Windows)在内存中锁定堆。这是通过Elasticsearch设置bootstrap.memory_lock完成的。

但是，在某些情况下，这个设置可以传递给Elasticsearch，但是Elasticsearch不能锁定堆(例如，如果Elasticsearch用户没有memlock unlimited)。内存锁检查验证bootstrap.memory_lock设置被启用，即JVM能够成功地锁定堆。

要通过内存锁检查，您可能必须配置bootstrap.memory_lock。



## 最大线程数检测

Elasticsearch通过将请求分解为多个阶段并将这些阶段传递给不同的线程池执行器来执行请求。在Elasticsearch中有不同的线程池执行器来执行各种任务。因此，Elasticsearch需要创建大量线程的能力。最大线程数检查确保Elasticsearch进程在正常使用情况下有权创建足够的线程。这个检查只在Linux上执行。

如果您在Linux上，要通过最大线程数检查，您必须配置您的系统以允许Elasticsearch进程能够创建至少4096个线程。这可以通过使用nproc设置的/etc/security/limit .conf来完成(注意，您可能还需要增加root用户的限制)。



## 最大文件检测

作为单个碎片组件的段文件和作为跨日志组件的跨日志代可以变得很大(超过多个gb)。在Elasticsearch过程可以创建的文件的最大大小受到限制的系统上，这可能会导致写操作失败。因此，这里最安全的选择是最大文件大小不受限制，这就是bootstrap检查强制执行的最大文件大小。

为了通过最大文件检查，您必须配置您的系统，以允许Elasticsearch过程能够写入大小不限的文件。这可以通过/etc/security/limit .conf实现，将fsize设置为unlimited(注意，您可能还需要增加root用户的限制)。



## 最大虚拟内存检测

Elasticsearch和Lucene使用mmap来有效地将索引的一部分映射到Elasticsearch地址空间中。这将某些索引数据保存在内存中，而不是JVM堆中，以便快速访问。为了使其有效，Elasticsearch应该有无限的地址空间。最大虚拟内存大小检查强制使Elasticsearch进程拥有无限的地址空间，并且只在Linux上强制执行。

要通过最大虚拟内存大小检查，您必须配置您的系统以允许Elasticsearch进程拥有无限的地址空间。这可以通过/etc/security/limit .conf实现，将as设置为unlimited(注意，您可能还需要增加root用户的限制)。



## 最大映射计数检测（mmapfs）

继续前面的内容，为了有效地使用mmap, Elasticsearch还需要能够创建许多内存映射区域。最大映射计数检查检查内核允许一个进程拥有至少262,144个内存映射区域，并且只在Linux上执行。要通过最大映射计数检查，必须配置vm.max_map_count。通过sysctl至少为262144。

另外，只有在使用mmapfs作为索引的存储类型时，才需要进行最大映射计数检查。如果不允许使用mmapfs，则不会强制执行此引导检查。



## 客户端JVM检测

openjdk派生的JVM提供了两种不同的JVM:客户机JVM和服务器JVM。这些jvm使用不同的编译器从Java字节码生成可执行的机器码。客户端JVM针对启动时间和内存占用进行了调优，而服务器JVM则针对性能最大化进行了调优。这两种vm之间的性能差异可能非常大。客户端JVM检查确保Elasticsearch不在客户端JVM中运行。

要通过客户机JVM检查，您必须在服务器VM中启动Elasticsearch。在现代系统和操作系统上，服务器VM是默认的。



## JVM收集器检测

针对不同的工作负载，openjdk派生的jvm有各种垃圾收集器。串行收集器特别适合于单逻辑CPU机器或极小的堆，这两种类型都不适合运行Elasticsearch。使用带有Elasticsearch的串行收集器会对性能造成毁灭性的影响。串行收集器检查确保Elasticsearch没有配置为与串行收集器一起运行。

要通过串行收集器检查，您必须不使用串行收集器启动Elasticsearch(无论它来自您正在使用的JVM的默认值，还是您已显式地使用-XX:+UseSerialGC指定它)。注意，随Elasticsearch附带的默认JVM配置将Elasticsearch配置为使用CMS收集器。



## 系统过滤器检测

Elasticsearch根据操作系统(例如Linux上的seccomp)安装不同风格的系统调用过滤器。安装这些系统调用过滤器是为了防止执行与fork相关的系统调用的能力，作为对Elasticsearch任意代码执行攻击的防御机制。系统调用筛选器检查确保如果启用了系统调用筛选器，则它们已成功安装。

要通过系统调用过滤器检查，您必须修复您的系统上阻止系统调用过滤器安装的任何配置错误(检查您的日志)，或者在您自己的风险下通过设置bootstrap.system_call_filter为false禁用系统调用过滤器。



## OnError和OutOfMemoryError检测

如果JVM遇到致命错误(OnError)或OutOfMemoryError (OnOutOfMemoryError)， JVM选项OnError和OnOutOfMemoryError允许执行任意命令。但是，在默认情况下，Elasticsearch系统调用过滤器(seccomp)是启用的，这些过滤器防止分叉。因此，使用OnError或OnOutOfMemoryError和系统调用过滤器是不兼容的。如果使用了这两个JVM选项，并且启用了系统调用过滤器，OnError和OnOutOfMemoryError检查将阻止Elasticsearch启动。

这个检测总是强制执行的。要通过此检查，不要启用OnError或OnOutOfMemoryError;相反，升级到Java 8u92并使用JVM标志ExitOnOutOfMemoryError。虽然它没有OnError和OnOutOfMemoryError的全部功能，但是在启用seccomp的情况下，将不支持任意分支。



## JDK早起版本检测

OpenJDK项目提供了即将发布的早期访问快照。这些版本不适合生产。早期访问检查检测这些早期访问快照。要通过这个检查，您必须在JVM的发布构建上启动Elasticsearch。



## G1GC检测

JDK 8附带的热点JVM的早期版本已知存在问题，当启用G1GC收集器时，可能会导致索引损坏。受影响的版本是那些比JDK 8u40附带的HotSpot版本更早的版本。G1GC检查检测热点JVM的这些早期版本。



## All权限检测

all权限检查确保在引导过程中使用的安全策略不会授予Elasticsearch用户java.security.AllPermission。使用授予的所有权限运行等同于禁用安全管理器。



## 发现配置检测

默认情况下，当Elasticsearch第一次启动时，它将尝试发现运行在同一主机上的其他节点。如果在几秒钟内没有发现被选中的主节点，Elasticsearch将形成一个集群，其中包括已发现的所有其他节点。在开发模式中，不需要任何额外配置就能形成这个集群是很有用的，但这不适用于生产，因为可能会形成多个集群并因此丢失数据。

此引导检查确保发现没有使用默认配置运行。它可以通过设置以下至少一个属性来满足:

```
discovery.seed_hosts
discovery.seed_providers
cluster.initial_master_nodes
```

> 注意，在集群第一次启动后，你应该从配置中删除`cluster.initial_master_nodes` 。当重新启动节点或向现有集群添加新节点时，不要使用此设置。相反，配置`discovery.seed_hosts` or `discovery.seed_providers`。如果您不需要任何发现配置，例如运行单节点集群，请设置discovery.seed_hosts: []以禁用发现并满足此引导检查。