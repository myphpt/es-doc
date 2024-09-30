

[TOC]

# 配置的优先级

1. Transient setting （临时配置）
2. Persistent setting （永久配置）
3. `elasticsearch.yml` setting （配置文件）
4. Default setting value （默认配置）



# 启动配置

```
ES_PATH_CONF=/path/to/my/config ./bin/elasticsearch
```



# 静态配置文件`elasticsearch.yaml`

```
path:
    data: /var/lib/elasticsearch
    logs: /var/log/elasticsearch
```

或者

```
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
```

引用环境变量

```
node.name:    ${HOSTNAME}
network.host: ${ES_NETWORK_HOST}
```



# 动态配置API

建议的方式

可以使集群处于同一设置，避免本地配置文件不同而未发现

```
PUT /_cluster/settings
```

查询参数：

```
flat_settings：(可选，布尔值)如果为真，将以平面格式返回设置。默认值为false。
include_defaults：(可选，布尔值)如果为真，返回所有默认的集群设置。默认值为false

master_timeout ：可选，连接到mater节点的时间，默认30s（PUT使用）
timeout：获取响应的超时时间，默认30s（PUT使用）
```



1、临时设置

```
PUT /_cluster/settings?flat_settings=true
{
  "transient" : {
    "indices.recovery.max_bytes_per_sec" : "20mb"
  }
}
```



2、持久设置

```
PUT /_cluster/settings
{
  "persistent" : {
    "indices.recovery.max_bytes_per_sec" : "50mb"
  }
}
```



3、重置设置

```
PUT /_cluster/settings
{
  "transient" : {
    "indices.recovery.max_bytes_per_sec" : null
  }
}
```



4、通配符重置

```
PUT /_cluster/settings
{
  "transient" : {
    "indices.recovery.*" : null
  }
}
```



# API约定

# 混合索引

所有多索引API支持以下`url`查询字符串参数:

`ignore_unavailable`

控制是否忽略任何指定的索引不可用，包括不存在的索引或关闭的索引。可以指定真或假。

`allow_no_indices`

控制如果通配符索引表达式没有生成具体索引时是否失败。可以指定真或假。例如，如果指定了通配符表达式foo\*，并且没有以foo开头的可用索引，那么根据这个设置，请求将失败。当指定了_all、\*或没有索引时，该设置也适用。如果别名指向一个关闭的索引，此设置也适用于别名。

`expand_wildcards`

控制扩展到何种类型的具体索引通配符索引表达式。如果指定open，则通配符表达式将仅展开为打开的索引，如果指定closed，则通配符表达式将仅展开为关闭的索引。另外，两个值(打开、关闭)都可以指定为扩展到所有索引。如果没有指定，那么通配符扩展将被禁用，如果指定了all，通配符表达式将扩展到所有索引(这等同于指定open,closed)。

 Document APIs和single-index `alias` APIs不支持以上配置



# 索引名中的时间表达式

Date math索引名称解析使您能够搜索一系列时间序列索引，而不是搜索所有时间序列索引并过滤结果或维护别名。限制搜索索引的数量可以减少集群上的负载并提高执行性能。例如，如果在日常日志中搜索错误，可以使用日期数学名称模板将搜索限制为过去两天。

格式：

```
<static_name{date_math_expr{date_format|time_zone}}>

time_zone默认值为utc
```

必须将日期数学索引名称表达式括在尖括号中，并且所有特殊字符都应该是URI编码的。例如:

```
#GET /<logstash-{now/d}>/_search
GET /%3Clogstash-%7Bnow%2Fd%7D%3E/_search(URI编码)
```

相关示例：基础时间2024年3月22日中午

| `<logstash-{now/d}>`                    | `logstash-2024.03.22` |
| --------------------------------------- | --------------------- |
| `<logstash-{now/M}>`                    | `logstash-2024.03.01` |
| `<logstash-{now/M{YYYY.MM}}>`           | `logstash-2024.03`    |
| `<logstash-{now/M-1M{YYYY.MM}}>`        | `logstash-2024.02`    |
| `<logstash-{now/d{YYYY.MM.dd|+12:00}}>` | `logstash-2024.03.23` |



# 常规参数

可应用与所有的API

## ?pretty=true

```
当追加?pretty=true时，返回的JSON将被格式化(仅用于调试!)另一个选项是set ?format=yaml，这将导致结果以(有时)可读性更强的yaml格式返回。
```

## ?human=false

```
统计信息以适合人类(如“exists_time”:“1h”或“size”:“1kb”)和计算机(如“exists_time_in_millis”:3600000或“size_in_bytes”:1024)的格式返回。可以通过在查询字符串中添加?human=false来关闭人类可读的值。当统计结果由监视工具使用，而不是供人使用时，这样做是有意义的。human的默认值为false。
```

## 日期计算

- `+1h` - 加1个小时 
- `-1d` - 减一天
- `/d`  - 四舍五入到最近的日志

举个`2001-01-01 12:00:00`栗子：

```
now+1h    				2001-01-01 13:00:00 
now-1h    				2001-01-01 11:00:00 
now-1h/d  				2001-01-01 00:00:00
2001.02.01\|\|+1M/d     2001-03-01 00:00:00 
```



## ?filter_path

所有REST api都接受一个filter_path参数，该参数可用于减少Elasticsearch返回的响应。这个参数采用逗号分隔的过滤器列表，用点符号表示:

```
GET /_search?q=elasticsearch&filter_path=took,hits.hits._id,hits.hits._score
GET /_cluster/state?filter_path=metadata.indices.*.stat*
```

注意，Elasticsearch有时直接返回字段的原始值，如`_source`字段。如果你想过滤_source字段，你应该考虑将已经存在的_source参数和filter_path参数结合在一起，像这样:

```
GET /_search?filter_path=hits.hits._source&_source=title&sort=rating:desc
```



## 压平设置

flat_settings标志影响设置列表的呈现。当flat_settings标志为真时，设置将以flat格式返回:

```
GET twitter/_settings?flat_settings=true
```



## 堆栈追踪

默认不启用

```
POST /twitter/_search?size=surprise_me
POST /twitter/_search?size=surprise_me&error_trace=true

```



# 基于URL的准许控制

许多用户使用带有基于url访问控制的代理来确保对Elasticsearch索引的访问。对于多搜索、多获取和批量请求，用户可以选择在URL中指定索引，并在请求体中的每个请求上指定索引。这可能使基于url的访问控制具有挑战性。

若要防止用户覆盖URL中指定的数据流或索引，在`elasticsearch.yml`中设置`rest.action.multi.allow_explicit_index` 值为 `false`

## 时间表达式

格式：

```
<static_name{date_math_expr{date_format|time_zone}}>
time_zone默认值为utc

```

必须将日期数学索引名称表达式括在尖括号中，并且所有特殊字符都应该是URI编码的。例如:

```
#GET /<logstash-{now/d}>/_search
GET /%3Clogstash-%7Bnow%2Fd%7D%3E/_search(URI编码)

```



## ?pretty=true

```
当追加?pretty=true时，返回的JSON将被格式化(仅用于调试!)另一个选项是?format=yaml，这将导致结果以(有时)可读性更强的yaml格式返回。

```

## ?human=false

```
统计信息以适合人类(如“exists_time”:“1h”或“size”:“1kb”)和计算机(如“exists_time_in_millis”:3600000或“size_in_bytes”:1024)的格式返回。可以通过在查询字符串中添加?human=false来关闭人类可读的值。当统计结果由监视工具使用，而不是供人使用时，这样做是有意义的。human的默认值为false。

```

## ?filter_path

所有REST api都接受一个filter_path参数，该参数可用于减少Elasticsearch返回的响应。这个参数采用逗号分隔的过滤器列表，用点符号表示:

```
GET /_search?q=elasticsearch&filter_path=took,hits.hits._id,hits.hits._score
GET /_cluster/state?filter_path=metadata.indices.*.stat*
GET /_cluster/state?filter_path=routing_table.indices.**.state
GET /_cluster/state?filter_path=metadata.indices.*.state,-metadata.indices.logstash-*
GET /_count?filter_path=-_shards

```

注意，Elasticsearch有时直接返回字段的原始值，如_source字段。如果你想过滤_source字段，你应该考虑将已经存在的_source参数和filter_path参数结合在一起，像这样:

```
GET /_search?filter_path=hits.hits._source&_source=title&sort=rating:desc

```

## ?flat_settings=true

flat_settings标志影响设置列表的呈现。当flat_settings标志为真时，设置将以flat格式返回，默认是false

```
GET twitter/_settings?flat_settings=true

```

## ?error_trace=true

默认情况下，当请求返回错误时，Elasticsearch不包含错误的堆栈跟踪。您可以通过将error_trace url参数设置为true来启用该行为。

```
POST /twitter/_search?size=surprise_me&error_trace=true

```



# 适用于_cat API

## ?v 

加上表头



## ?help 

参数列解释



## ?h

表头

```
?h=field1,field2
列出指定参数列，支持通配符

```



## ?format

```
?format=json
显示字符串格式化，支持参数：text（默认）、json 、smile 、yaml 、cbor

```



## ?time

```
?time=d 
关于时间的格式化，支持参数：d h m s ms micros nanos

```



## ?size

```
?size=k
关于大小的格式化，支持参数： k m g t p

```



## ?byte

```
?byte=b
字节格式化，支持参数：b kb mb gb tb pb

```



## ?sort

```
可以简写为?s
?s=order:desc,index_patterns
排序
例如，有一个排序字符串s=column1,column2:desc,column3，这个表将按column1升序排序，按column2降序排序，按column3升序排序。

```



## 响应头

以下三种写法可以达到同样的效果

```
GET /_cat/indices?pretty
curl -XGET "http://node02:9200/_cat/indices?pretty"
curl '192.168.56.10:9200/_cat/indices?pretty' -H "Accept: application/json"

```

```
GET /_cat/indices?format=json&pretty
curl -XGET "http://node02:9200/_cat/indices?format=json&pretty"
curl 'localhost:9200/_cat/indices?format=json&pretty'

```





## 通配符控制

默认值为true，但当设置为false时，Elasticsearch将拒绝在请求主体中明确指定索引的请求。

```
rest.action.multi.allow_explicit_index: false
```



## 参考

https://www.elastic.co/guide/en/elasticsearch/reference/6.5/url-access-control.html

https://www.elastic.co/guide/en/elasticsearch/reference/6.5/date-math-index-names.html#date-math-index-names

https://www.elastic.co/guide/en/elasticsearch/reference/6.5/multi-index.html
