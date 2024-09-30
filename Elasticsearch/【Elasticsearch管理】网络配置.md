# HTTP

Elasticsearch只在默认情况下绑定到本地主机。对于运行本地开发服务器(如果在同一台机器上启动多个节点，甚至可以运行开发集群)来说，这已经足够了，但是为了跨多个服务器运行实际的生产集群，将需要配置一些基本的网络设置。

永远不要将未受保护的节点暴露给公共internet。

> 是否绑定专属IP是分辨是否是开发模式和生产模式的标准。

```
network.host 

节点将绑定到此主机名或IP地址，并将此主机发布(广告)给集群中的其他节点。
接受IP地址、主机名、特殊值或任意组合的数组。
注意，任何包含:的值(例如，一个IPv6地址或包含一个特殊值)必须用引号括起来，因为:在YAML中是一个特殊字符。0.0.0.0是一个可接受的IP地址，它将绑定到所有网络接口。值0与值0.0.0.0具有相同的效果。
默认 _local_.
```

```
discovery.zen.ping.unicast.hosts 

为了加入一个集群，节点需要知道集群中至少一些其他节点的主机名或IP地址。此设置提供此节点将尝试联系的其他节点的初始列表。接受IP地址或主机名。
如果主机名查找解析为多个IP地址，那么将使用每个IP地址进行发现。
循环DNS——在每次查找时从列表中返回不同的IP——可以用于发现;
不存在的IP地址将抛出异常，并导致下一轮ping时再次查找DNS(取决于JVM DNS缓存)。
默认值 ["127.0.0.1", "[::1]"]。
```

```
http.port 
要绑定到传入HTTP请求的端口。接受单个值或范围。如果指定了一个范围，则节点将绑定到该范围中的第一个可用端口。
默认值9200-9300.
```

```
transport.tcp.port 
为节点间通信而绑定的端口。接受单个值或范围。如果指定了一个范围，则节点将绑定到该范围中的第一个可用端口。
默认值9300-9400.
```



network.host的特殊值

|                        |                                                       |
| ---------------------- | ----------------------------------------------------- |
| `_[networkInterface]_` | 网络接口的地址，例如 `_en0_`.                         |
| `_local_`              | 系统上的任何回送地址, for example `127.0.0.1`.        |
| `_site_`               | 系统上的任何站点-本地地址, for example `192.168.0.1`. |
| `_global_`             | 系统上任何全局范围的地址, for example `8.8.8.8`.      |



禁用HTTP

可以通过设置`http.enabled`为false完全禁用http模块。Elasticsearch节点(和Java客户机)使用传输接口(而不是HTTP)进行内部通信。在不打算直接服务REST请求的节点上完全禁用http层可能是有意义的。

例如，如果还有打算为所有REST请求提供服务的客户机节点，那么可以在仅数据节点上禁用HTTP。但是请注意，将不能直接向禁用HTTP的节点发送任何REST请求(例如检索节点状态)。



## 高级网络设置

network.host网络设置中介绍的主机设置是同时设置绑定主机和发布主机的快捷方式。在高级用例中，例如在代理服务器后面运行时，可能需要将这些设置设置为不同的值:

```
network.bind_host 
这指定了一个节点应该绑定到哪个网络接口，以便侦听传入的请求。一个节点可以绑定到多个接口，例如两个网卡，或者一个站点本地地址和一个本地地址。默认为network.host。

network.publish_host 
发布主机是节点向集群中的其他节点发布的单一接口，以便这些节点可以连接到它。当前，一个Elasticsearch节点可以绑定到多个地址，但只发布一个地址。如果没有指定，默认network.host为“最佳”地址。按IPv4/IPv6堆栈首选项排序，然后按可达性排序。如果你设置了一个网络。如果产生多个绑定地址，但依赖于节点到节点通信的特定地址，则应该显式设置network.publish_host. 
```

以上两个设置都可以像network一样配置。主机——接受IP地址、主机名和特殊值。



## 高级TCP设置

任何使用TCP的都使用以下配置：

|                                   |                                                             |
| --------------------------------- | ----------------------------------------------------------- |
| `network.tcp.no_delay`            | 启用或禁用TCP无延迟设置。默认值为true。                     |
| `network.tcp.keep_alive`          | 启用或禁用TCP保持活动。默认值为true。                       |
| `network.tcp.reuse_address`       | 地址是否可以重用。在非windows机器上默认为true。             |
| `network.tcp.send_buffer_size`    | TCP发送缓冲区的大小(用大小单位指定)。默认情况下未显式设置。 |
| `network.tcp.receive_buffer_size` | TCP接收缓冲区的大小(用大小单位指定)。默认情况下未显式设置。 |



# Transport

 传输模块用于集群内节点之间的内部通信。从一个节点到另一个节点的每个调用都使用传输模块(例如，当一个HTTP GET请求由一个节点处理，而实际上应该由持有数据的另一个节点处理)。

传输机制在本质上是完全异步的，这意味着没有等待响应的阻塞线程。使用异步通信的好处是首先解决了C10k问题，同时也是分散(广播)/收集操作(如Elasticsearch中的搜索)的理想解决方案。

TCP传输是使用TCP的传输模块的实现。它允许以下设置:

```
transport.tcp.port
绑定端口范围。默认为9300 - 9400。

transport.publish_port
transport.bind_host
transport.publish_host
transport.host
```



## TCP传输概要文件

Elasticsearch允许通过使用传输配置文件绑定到不同接口上的多个端口。参见下面的示例配置

```
transport.profiles.default.port: 9300-9400
transport.profiles.default.bind_host: 10.0.0.1
transport.profiles.client.port: 9500-9600
transport.profiles.client.bind_host: 192.168.0.1
transport.profiles.dmz.port: 9700-9800
transport.profiles.dmz.bind_host: 172.16.1.2
```

默认配置文件是特殊的。如果其他配置文件没有特定的配置设置集，则将其用作任何其他配置文件的回退，并且此节点是如何连接到集群中的其他节点的。

可以在每个传输配置文件上配置以下参数，如上面的示例所示:

- `port`: The port to bind to 
- `bind_host`: The host to bind 
- `publish_host`: The host which is published in informational APIs 
- `tcp_no_delay`: Configures the `TCP_NO_DELAY` option for this socket 
- `tcp_keep_alive`: Configures the `SO_KEEPALIVE` option for this socket 
- `reuse_address`: Configures the `SO_REUSEADDR` option for this socket 
- `tcp_send_buffer_size`: Configures the send buffer size of the socket 
- `tcp_receive_buffer_size`: Configures the receive buffer size of the socket 



## Transport跟踪

 传输模块有一个专用的跟踪记录器，当它被激活时，它会记录传入和传出的请求。可以通过设置org.elasticsearch.transport.TransportService的级别动态激活该日志。跟踪记录器要跟踪:

```
PUT _cluster/settings
{
   "transient" : {
      "logger.org.elasticsearch.transport.TransportService.tracer" : "TRACE"
   }
}
```

还可以使用一组包含和排除通配符模式来控制跟踪哪些操作。默认情况下，除故障检测外，每个请求都将被跟踪:

```
PUT _cluster/settings
{
   "transient" : {
      "transport.tracer.include" : "*",
      "transport.tracer.exclude" : "internal:discovery/zen/fd*"
   }
}
```

# 线程池

一个节点拥有几个线程池，以便改进在节点内管理线程内存消耗的方式。许多这些池还有与它们相关联的队列，这些队列允许持有挂起的请求，而不是丢弃它们。

```
generic
线程池类型为scaling

index
索引写入删除操作。线程池类型为fixed，大小为# of available processors，队列长度为200。

search
count/search/suggest操作。类型为fixed_auto_queue_size，大小为int((# of available_processors * 3) / 2) + 1，初始值为1000.

get
类型为fixed，大小为# of available processors，队列长度为1000.

analyze  
类型为fixed，大小为1，队列长度为16

write
single-document index/delete/update和 bulk requests。
类型为fixed，大小为# of available processors，队列长度为200。最大大小为1 + # of available processors

snapshot
snapshot/restore操作。
类型为scaling，保持活跃5m，并且最大为`min(5, (# of available processors)/2)`.

warmer
segment warm-up 操作。
类型为scaling，保持活跃5m，并且最大为`min(5, (# of available processors)/2)`.

refresh
类型为scaling，保持活跃5m，并且最大为`min(10, (# of available processors)/2)`.

listener 
listener threaded设置为true的时候。
类型为scaling，默认为`min(10, (# of available processors)/2)`.
```

设置

可以通过设置特定类型的参数来更改特定的线程池;例如，改变索引线程池有更多的线程:

```
thread_pool:
    index:
        size: 30
```



## fixed线程池

下面是线程池的类型及其各自的参数:

fixed：fixed持有固定大小的线程来处理请求，使用一个队列(可选绑定)处理没有线程为其服务的挂起请求。

size：size参数控制线程的数量，默认为内核数量乘以5。

queue_size：queue_size控制没有线程执行的挂起请求队列的大小。默认情况下，它被设置为-1，这意味着它是无界的。当一个请求进入并且队列已满时，它将中止该请求。

```
thread_pool:
    index:
        size: 30
        queue_size: 1000
```



## fixed_auto_queue_size

fixed_auto_queue_size线程池持有固定大小的线程，用于处理没有线程服务的挂起请求，并使用一个有界队列处理这些请求。它类似于fixed线程池，但是，queue_size会根据Little定律的计算自动调整。每次完成auto_queue_frame_size操作时，这些计算可能会将queue_size调高或调低50。

size参数控制线程的数量，默认为内核数量乘以5。

queue_size允许控制没有线程执行的挂起请求队列的初始大小。

min_queue_size设置控制queue_size可以调整的最小值。

max_queue_size设置控制queue_size可以调整的最大数量。

auto_queue_frame_size设置控制在调整队列之前进行度量的操作数量。它应该足够大，单个操作不能过度影响计算。

target_response_time是一个时间值设置，指示线程池队列中任务的目标平均响应时间。如果任务通常超过这个时间，线程池队列将被调低，以拒绝任务。

```
thread_pool:
    search:
        size: 30
        queue_size: 500
        min_queue_size: 10
        max_queue_size: 1000
        auto_queue_frame_size: 2000
        target_response_time: 1s
```



## scaling

可伸缩的线程池持有动态数量的线程。这个数字与工作负载成比例，并在核心参数和最大参数的值之间变化。

keep_alive参数决定一个线程在不做任何工作的情况下应该在线程池中保留多长时间。

```
thread_pool:
    warmer:
        core: 1
        max: 8
        keep_alive: 2m
```



## 处理器设置

自动检测处理器的数量，并根据它自动设置线程池设置。这可以通过显式设置处理器设置来实现。

```
processors: 2
```

如果在同一个主机上运行多个Elasticsearch实例，但希望Elasticsearch调整其线程池的大小，就像它只有一部分CPU一样，应该覆盖设置为所需的部分的处理器(例如，如果在一台16核的机器上运行两个Elasticsearch实例，请将处理器设置为8)。请注意，这是一个专家级的用例，其中涉及的内容远不止设置处理器设置，还有其他需要考虑的事项，如更改垃圾收集器线程的数量、将进程固定到内核等。

有时候会错误地检测到处理器的数量，在这种情况下，显式地设置处理器设置可以解决这类问题。

```
GET /_nodes/os
```

