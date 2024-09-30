# 远程集群

远程集群模块允许您建立到远程集群的单向连接。此功能用于跨集群复制和跨集群搜索。

远程集群连接通过配置远程集群并仅连接到远程集群中有限数量的节点来工作。每个远程集群都通过一个名称和一个种子节点列表引用。当注册一个远程集群时，它的集群状态将从一个种子节点中检索，因此默认情况下最多选择三个网关节点作为远程集群请求的一部分连接。

远程集群连接只包含从协调节点到前面选择的远程节点的单向连接。可以通过节点属性标记应该选择哪些节点(参见远程集群设置)。

集群中配置了远程集群的每个节点连接到一个或多个网关节点，并使用它们将请求联合到远程集群。



## 配置远程集群

远程集群可以使用集群设置(可以动态更新)进行全局指定，也可以使用elasticsearch.yml对单个节点进行本地指定。

如果远程集群是通过elasticsearch配置的。只有具有该配置的节点才能连接到远程集群。换句话说，依赖于远程集群请求的功能必须专门从这些节点驱动。通过集群设置API设置的远程集群将在集群中的每个节点上可用。

连接到远程集群的节点的elasticsearch.yml配置文件需要列出应该连接到的远程集群。每个种子条目的格式是remote_host:transport.tcp。端口,例如:

```
cluster:
    remote:
        cluster_one: 
            seeds: 127.0.0.1:9301
        cluster_two: 
            seeds: 127.0.0.1:9302

```

cluster_one和cluster_two是表示到每个集群的连接的任意集群别名。这些名称随后用于区分本地索引和远程索引。在本例中，cluster_one使用端口9301进行传输，而cluster_two使用端口9302。



使用cluster settings API向集群中的所有节点添加远程集群的等效示例如下:

```
PUT _cluster/settings
{
  "persistent": {
    "cluster": {
      "remote": {
        "cluster_one": {
          "seeds": [
            "127.0.0.1:9300"
          ]
        },
        "cluster_two": {
          "seeds": [
            "127.0.0.1:9301"
          ]
        },
        "cluster_three": {
          "seeds": [
            "127.0.0.1:9302"
          ]
        }
      }
    }
  }
}

```

远程集群可以通过将其种子设置为null从集群设置中删除:

```
PUT _cluster/settings
{
  "persistent": {
    "cluster": {
      "remote": {
        "cluster_three": {
          "seeds": null 
        }
      }
    }
  }
}

```

cluster_three将从集群设置中删除，而cluster_one和cluster_two将保持不变。



## 远程集群设置

**`cluster.remote.connections_per_cluster`**  

 要连接到每个远程集群的网关节点的数量。默认值是“3”。 

  **`cluster.remote.initial_connect_timeout`**  

  节点启动时等待建立远程连接的时间。默认值是30。

  **`cluster.remote.node.attr`**  

  筛选合格作为远程集群中的网关节点的节点属性。例如，一个节点可以有一个节点属性node.attr.gateway: true，这样只有具有此属性的节点将被连接到如果  `cluster.remote.node.attr`设置为gateway。

  **`cluster.remote.connect`**  

  默认情况下，集群中的任何节点都可以充当跨集群客户机并连接到远程集群。cluster.remote.connect设置为false(默认为true)，以防止某些节点连接到远程集群。远程集群请求必须发送到允许充当跨集群客户机的节点。

  **`cluster.remote.${cluster_alias}.skip_unavailable`**  

每个集群布尔设置，当没有属于特定集群的节点可用且集群是远程集群请求的目标时，允许跳过特定集群。默认值是false，这意味着所有集群在默认情况下都是强制性的，但是可以通过将该设置设置为true来选择性地使它们成为可选的。



# Cross-cluster搜索

跨集群搜索特性允许任何节点充当跨多个集群的联合客户机。与部落节点特性相反，跨集群搜索节点不会加入远程集群，而是以一种简单的方式连接到远程集群，以执行联合搜索请求。



## 使用

跨集群搜索需要配置远程集群。

```
PUT _cluster/settings
{
  "persistent": {
    "cluster": {
      "remote": {
        "cluster_one": {
          "seeds": [
            "127.0.0.1:9300"
          ]
        },
        "cluster_two": {
          "seeds": [
            "127.0.0.1:9301"
          ]
        },
        "cluster_three": {
          "seeds": [
            "127.0.0.1:9302"
          ]
        }
      }
    }
  }
}

```

要在远程集群cluster_one上搜索twitter索引，索引名必须前缀为集群别名，别名之间用:字符

```
GET /cluster_one:twitter/_search
{
  "query": {
    "match": {
      "user": "kimchy"
    }
  }
}

```

与部落特征相比，跨聚类搜索也可以在不同的聚类上搜索同名索引:

```
GET /cluster_one:twitter,twitter/_search
{
  "query": {
    "match": {
      "user": "kimchy"
    }
  }
}

```

搜索结果的消歧方式与请求中索引消歧的方式相同。即使索引名称相同，这些索引在合并结果时也会被视为不同的索引。从远程索引检索到的所有结果都将以其远程集群名称作为前缀:



## 跳过未连接的集群

默认情况下，在执行搜索请求时，通过跨集群搜索搜索的所有远程集群都必须可用，否则整个请求失败，即使某些集群可用，也不会返回搜索结果。远程集群可以通过布尔型skip_unavailable设置(默认设置为false)成为可选的。

```
PUT _cluster/settings
{
  "persistent": {
    "cluster.remote.cluster_two.skip_unavailable": true 
  }
}
cluster_two是可选的

```

```
GET /cluster_one:twitter,cluster_two:twitter,twitter/_search 
{
  "query": {
    "match": {
      "user": "kimchy"
    }
  }
}
在cluster_one、cluster_two和本地搜索twitter索引

```


