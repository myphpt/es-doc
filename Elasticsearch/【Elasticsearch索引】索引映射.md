# 字段类型

## 字段别名

> 字段别名只能在具有单一映射类型的索引上指定。要添加字段别名，索引必须在6.0或更高版本中创建，或者是使用设置index.mapping.single_type: true

```
PUT trips
{
  "mappings": {
    "_doc": {
      "properties": {
        "distance": {
          "type": "long"
        },
        "route_length_miles": {
          "type": "alias",
          "path": "distance"    //目标字段的路径。注意，这必须是完整的路径，包括任何父对象
        },
        "transit_mode": {
          "type": "keyword"
        }
      }
    }
  }
}

GET _search
{
  "query": {
    "range" : {
      "route_length_miles" : {
        "gte" : 39
      }
    }
  }
}
```

在搜索请求的某些部分以及请求字段功能时，可以提供字段通配符模式。在这些情况下，通配符模式除了匹配具体字段外还将匹配字段别名:

```
GET trips/_field_caps?fields=route_*,transit_mode
```



## 数组

在Elasticsearch中，没有专门的数组数据类型。默认情况下，任何字段都可以包含零个或多个值，但是，数组中的所有值必须具有相同的数据类型。

```
PUT my_index/_doc/1
{
  "message": "some arrays in this document...",
  "tags":  [ "elasticsearch", "wow" ], 
  "lists": [ 
    {
      "name": "prog_list",
      "description": "programming list"
    },
    {
      "name": "cool_list",
      "description": "cool stuff list"
    }
  ]
}

```

## Binary datatype

 二进制类型接受二进制值作为Base64编码的字符串。该字段不存储默认和不可搜索

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "name": {
          "type": "text"
        },
        "blob": {
          "type": "binary",
          "doc_values": false
          "store": true 
        }
      }
    }
  }
}
```

## Range datatypes

```
PUT range_index
{
  "settings": {
    "number_of_shards": 2
  },
  "mappings": {
    "_doc": {
      "properties": {
        "expected_attendees": {
          "type": "integer_range"
        },
        "time_frame": {
          "type": "date_range", 
          "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
        }
      }
    }
  }
}


PUT range_index/_doc/1?refresh
{
  "expected_attendees" : { 
    "gte" : 10,
    "lte" : 20
  },
  "time_frame" : { 
    "gte" : "2015-10-31 12:00:00", 
    "lte" : "2015-11-01"
  }
}

GET range_index/_search
{
  "query" : {
    "term" : {
      "expected_attendees" : {
        "value": 12
      }
    }
  }
}
```

 支持的值：

```
integer_range 	float_range 	long_range	 	double_range 	date_range 		ip_range 
```

支持系统参数：

```
coerce 
boost 
index 
store 
```

## Boolean datatype

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "is_published": {
          "type": "boolean"
        }
      }
    }
  }
}
```

## Date datatype

-  包含格式化日期的字符串，例如`“2015-01-01”`或`“2015/01/01 12:10:30”`。
- 表示毫秒数。
- 表示秒的整数。

在内部，日期被转换为UTC(如果指定了时区)，并存储为表示自epoch以来的毫秒数。

> 日期总是以字符串的形式呈现，即使它们在JSON文档中最初是作为long格式提供的。

可以通过使用||作为分隔符来分隔多个格式。将依次尝试每种格式，直到找到匹配的格式。第一种格式将用于将自epoch以来的毫秒值转换回字符串。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "date": {
          "type":   "date",
          "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
        }
      }
    }
  }
}
```



## Geo-point datatype

 地理点类型

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "location": {
          "type": "geo_point"
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "text": "Geo-point as an object",
  "location": { 
    "lat": 41.12,
    "lon": -71.34
  }
}

PUT my_index/_doc/2
{
  "text": "Geo-point as a string",
  "location": "41.12,-71.34" 
}

PUT my_index/_doc/3
{
  "text": "Geo-point as a geohash",
  "location": "drm3btev3e86" 
}

PUT my_index/_doc/4
{
  "text": "Geo-point as an array",
  "location": [ -71.34, 41.12 ] 
}

GET my_index/_search
{
  "query": {
    "geo_bounding_box": { 
      "location": {
        "top_left": {
          "lat": 42,
          "lon": -72
        },
        "bottom_right": {
          "lat": 40,
          "lon": -74
        }
      }
    }
  }
}
```



## IP datatype

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "ip_addr": {
          "type": "ip"
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "ip_addr": "192.168.1.1"
}

GET my_index/_search
{
  "query": {
    "term": {
      "ip_addr": "192.168.0.0/16"
    }
  }
}
```

## Keyword datatype

 关键字类型

一个字段，用于索引结构化内容，如电子邮件地址、主机名、状态码、邮政编码或标签。

它们通常用于过滤(查找发布状态的所有博客文章)、排序和聚合。关键字字段只能通过它们的确切值进行搜索。

如果需要索引全文内容，如电子邮件正文或产品描述，可能应该使用文本字段。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "tags": {
          "type":  "keyword"
        }
      }
    }
  }
}
```

## Nested datatype

 嵌套类型

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "user": {
          "type": "nested" 
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "group" : "fans",
  "user" : [
    {
      "first" : "John",
      "last" :  "Smith"
    },
    {
      "first" : "Alice",
      "last" :  "White"
    }
  ]
}

GET my_index/_search
{
  "query": {
    "nested": {
      "path": "user",
      "query": {
        "bool": {
          "must": [
            { "match": { "user.first": "Alice" }},
            { "match": { "user.last":  "Smith" }} 
          ]
        }
      }
    }
  }
}

GET my_index/_search
{
  "query": {
    "nested": {
      "path": "user",
      "query": {
        "bool": {
          "must": [
            { "match": { "user.first": "Alice" }},
            { "match": { "user.last":  "White" }} 
          ]
        }
      },
      "inner_hits": { 
        "highlight": {
          "fields": {
            "user.first": {}
          }
        }
      }
    }
  }
}
```

## Numeric datatypes

 数值类型

```
long 	integer 	short 	byte 	double 	float 	half_float 		scaled_float 
```

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "number_of_bytes": {
          "type": "integer"
        },
        "time_in_seconds": {
          "type": "float"
        },
        "price": {
          "type": "scaled_float",
          "scaling_factor": 100
        }
      }
    }
  }
}
```



## Object datatype

对象类型

```
PUT my_index
{
  "mappings": {
    "_doc": { 
      "properties": {
        "region": {
          "type": "keyword"
        },
        "manager": { 
          "properties": {
            "age":  { "type": "integer" },
            "name": { 
              "properties": {
                "first": { "type": "text" },
                "last":  { "type": "text" }
              }
            }
          }
        }
      }
    }
  }
}

PUT my_index/_doc/1
{ 
  "region": "US",
  "manager": { 
    "age":     30,
    "name": { 
      "first": "John",
      "last":  "Smith"
    }
  }
}
```

##  Text datatype

文本类型

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "full_name": {
          "type":  "text"
        }
      }
    }
  }
}
```

##  Token count datatype

 token_count类型的字段实际上是一个整数字段，它接受字符串值，分析它们，然后对字符串中记号的数量进行索引。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "name": { 
          "type": "text",
          "fields": {
            "length": { 
              "type":     "token_count",
              "analyzer": "standard"
            }
          }
        }
      }
    }
  }
}

PUT my_index/_doc/1
{ "name": "John Smith" }

PUT my_index/_doc/2
{ "name": "Rachel Alice Williams" }

GET my_index/_search
{
  "query": {
    "term": {
      "name.length": 3 
    }
  }
}
```

## Percolator type

 percolator字段类型将json结构解析为原生查询并存储该查询，以便percolate query可以使用它来匹配所提供的文档。任何包含json对象的字段都可以配置为percolator字段。

```
PUT my_index
{
    "mappings": {
        "_doc": {
            "properties": {
                "query": {
                    "type": "percolator"
                },
                "field": {
                    "type": "text"
                }
            }
        }
    }
}

PUT my_index/_doc/match_value
{
    "query" : {
        "match" : {
            "field" : "value"
        }
    }
}
```



## join  datatype

 join数据类型是一个特殊字段，它在具有相同索引的文档中创建父/子关系。relations部分定义了文档中的一组可能的关系，每个关系分别是父名称和子名称。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "my_join_field": { 
          "type": "join",
          "relations": {
            "question": "answer" 
          }
        }
      }
    }
  }
}

PUT my_index/_doc/1?refresh
{
  "text": "This is a question",
  "my_join_field": {
    "name": "question" 
  }
}

PUT my_index/_doc/2?refresh
{
  "text": "This is another question",
  "my_join_field": {
    "name": "question"
  }
}

PUT my_index/_doc/3?routing=1&refresh 
{
  "text": "This is an answer",
  "my_join_field": {
    "name": "answer", 
    "parent": "1" 
  }
}

PUT my_index/_doc/4?routing=1&refresh
{
  "text": "This is another answer",
  "my_join_field": {
    "name": "answer",
    "parent": "1"
  }
}

GET my_index/_search
{
  "query": {
    "match_all": {}
  },
  "sort": ["_id"]
}
```



# 映射参数

## analyzer

```
PUT /my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "text": { 
          "type": "text",
          "fields": {
            "english": { 
              "type":     "text",
              "analyzer": "english"
            }
          }
        }
      }
    }
  }
}

analyzer 用于索引所有terms ，包括停止词
search_analyzer 用于非短语查询的，将删除停止词
search_quote_analyzer 用于不会删除停止词的短语查询
```

## normalizer

keyword字段的normalizer属性与analyzer类似，不同之处在于它保证分析链生成单个标记。

在索引keyword之前，以及通过查询解析器(如match查询)或通过Term查询搜索keyword字段时，使用规范化器。

```
PUT index
{
  "settings": {
    "analysis": {
      "normalizer": {
        "my_normalizer": {
          "type": "custom",
          "char_filter": [],
          "filter": ["lowercase", "asciifolding"]
        }
      }
    }
  },
  "mappings": {
    "_doc": {
      "properties": {
        "foo": {
          "type": "keyword",
          "normalizer": "my_normalizer"
        }
      }
    }
  }
}
```





## boost

权重（5.0废弃）

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "title": {
          "type": "text",
          "boost": 2 
        },
        "content": {
          "type": "text"
        }
      }
    }
  }
}
```



## coerce

数据并不总是规范的。根据它是如何产生的，一个数字可能在JSON主体中呈现为一个真正的JSON数字，例如5，但它也可能呈现为一个字符串，例如。“5”。或者，应该是整数的数字可能会被呈现为浮点数，例如5.0，甚至“5.0”。

强制尝试清除脏值，以符合字段的数据类型。例如:

- 字符串将被强制为数字。
- 浮点数将被截断作为整数值。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "number_one": {
          "type": "integer"
        },
        "number_two": {
          "type": "integer",
          "coerce": false
        }
      }
    }
  }
}
```

全局设置

```
PUT my_index
{
  "settings": {
    "index.mapping.coerce": false
  },
  "mappings": {
    "_doc": {
      "properties": {
        "number_one": {
          "type": "integer",
          "coerce": true
        },
        "number_two": {
          "type": "integer"
        }
      }
    }
  }
}
```

## copy_to

copy_to参数允许将多个字段的值复制到group字段中，然后可以将group字段作为单个字段进行查询。例如，first_name和last_name字段可以复制到full_name字段，如下所示:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "first_name": {
          "type": "text",
          "copy_to": "full_name" 
        },
        "last_name": {
          "type": "text",
          "copy_to": "full_name" 
        },
        "full_name": {
          "type": "text"
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "first_name": "John",
  "last_name": "Smith"
}

GET my_index/_search
{
  "query": {
    "match": {
      "full_name": { 
        "query": "John Smith",
        "operator": "and"
      }
    }
  }
}
```



重要的点：

- 复制的是字段值，而不是term(从分析过程中产生)。
- 原始_source字段不会被修改以显示复制的值。
- 使用"copy_to": ["field_1"， "field_2"]可以将相同的值复制到多个字段中。
- 不能通过中间字段递归复制



## dynamic

默认情况下，可以动态地将字段添加到文档或文档内的内部对象中，只要为包含新字段的文档建立索引即可。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic": false, 
      "properties": {
        "user": { 
          "properties": {
            "name": {
              "type": "text"
            },
            "social_networks": { 
              "dynamic": true,
              "properties": {}
            }
          }
        }
      }
    }
  }
}

支持的值：
true 	将新检测到的字段添加到映射中。(默认)
false 		忽略新检测到的字段。这些字段将不会被索引，因此不能被搜索，但仍然会出现在返回命中的_source字段中。这些字段将不会添加到映射中，新的字段必须显式添加。

strict （如果检测到新字段，则抛出异常并拒绝文档。新字段必须显式地添加到映射中）
```



## enabled

Elasticsearch尝试索引给它的所有字段，但有时如果只想存储字段而不索引它。例如，假设正在使用Elasticsearch作为web会话存储。可能希望索引会话ID和上次更新时间，但不需要对会话数据本身查询或运行聚合。

enabled设置只能应用于映射类型和对象字段，它会导致Elasticsearch完全跳过字段内容的解析。JSON仍然可以从_source字段检索，但它是不搜索或存储为任何其他方式:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "user_id": {
          "type":  "keyword"
        },
        "last_updated": {
          "type": "date"
        },
        "session_data": { 
          "enabled": false
        }
      }
    }
  }
}

PUT my_index/_doc/session_1
{
  "user_id": "kimchy",
  "session_data": {   //任何数据都可以传递到session_data字段，因为它将被完全忽略。
    "arbitrary_object": {
      "some_array": [ "foo", "bar", { "baz": 2 } ]
    }
  },
  "last_updated": "2015-12-06T18:20:22"
}

PUT my_index/_doc/session_2
{
  "user_id": "jpountz",
  "session_data": "none",    //session_data还将忽略非JSON对象的值。
  "last_updated": "2015-12-06T18:22:13"
}
```

整个映射类型也可能被禁用，在这种情况下，文档被存储在_source字段中，这意味着它可以被检索，但它的内容没有以任何方式被索引:

```
PUT my_index
{
  "mappings": {
    "_doc": { 
      "enabled": false
    }
  }
}

PUT my_index/_doc/session_1
{
  "user_id": "kimchy",
  "session_data": {
    "arbitrary_object": {
      "some_array": [ "foo", "bar", { "baz": 2 } ]
    }
  },
  "last_updated": "2015-12-06T18:20:22"
}

GET my_index/_doc/session_1 

GET my_index/_mapping 
```



## eager_global_ordinals 

全局序号是在doc值之上的一种数据结构，它按照字典顺序为每个惟一的term维护递增的编号。每个term都有一个唯一的数字，并且term a的数量小于term b的数量。全局序号只支持关键字和文本字段。在关键字字段中，它们默认可用，但文本字段只能在启用fielddata及其所有相关组件时使用它们。

Doc值(和fielddata)也有序号，序号是特定段和字段中所有term的唯一编号。全局序数就是在此基础上构建的，它提供了段序数和全局序数之间的映射，后者在整个碎片中是唯一的。给定特定字段的全局序数与一个分片的所有段绑定在一起，一旦有新的段可见，它们就需要完全重新构建。

全局序号用于使用分段序号的特性，例如term聚合，以提高执行时间。term聚合完全依赖全局序数在切分级别执行聚合，然后仅在最后的reduce阶段将全局序数转换为实际的term，该阶段合并来自不同切分的结果。

全局序数的加载时间取决于字段中项的数量，但一般来说时间较低，因为它的源字段数据已经加载。全局序数的内存开销很小，因为它被非常有效地压缩了。

默认情况下，全局序号是在搜索时加载的，如果正在优化索引速度，这是一个正确的权衡。但是，如果你对搜索速度更感兴趣，在你计划在term聚合中使用的字段上设置eager_global_ordinals: true可能会有效:

```
PUT my_index/_mapping/_doc
{
  "properties": {
    "tags": {
      "type": "keyword",
      "eager_global_ordinals": true
    }
  }
}
```

这将把成本从搜索时间转移到刷新时间。Elasticsearch将确保在发布更新索引内容之前构建全局序数。

如果你决定不需要在这个字段上运行term聚合，那么你可以在任何时候禁用全局序号的即时加载:

```
PUT my_index/_mapping/_doc
{
  "properties": {
    "tags": {
      "type": "keyword",
      "eager_global_ordinals": false
    }
  }
}
```



## fielddata

默认情况下，大多数字段都被索引，这使得它们可以被搜索。然而，在脚本中排序、聚合和访问字段值需要不同于搜索的访问模式。

搜索需要回答“哪些文档包含这个term?”，而排序和聚合需要回答另一个问题:“这个文档的这个字段的值是多少?”

大多数字段可以使用索引时、磁盘上的doc_values进行数据访问模式，但是文本字段不支持doc_values。

相反，文本字段使用名为fielddata的内存中查询时间数据结构。该数据结构是在字段第一次用于聚合、排序或在脚本中使用时按需构建的。它是由阅读整个反向索引对于每一段从磁盘,反相term↔︎文档的关系,并将结果存储在内存中,JVM堆。



text类型默认禁用

Fielddata会消耗大量堆空间，特别是在加载高基数文本字段时。一旦fielddata被加载到堆中，它将在段的生命周期中一直留在堆中。此外，加载fielddata是一个昂贵的过程，可能会导致用户体验延迟。这就是为什么默认情况下禁用fielddata的原因。

如果你试图排序，聚合，或访问一个文本字段的脚本值，会抛出异常

默认情况下在文本字段中禁用Fielddata。在[your_field_name]上设置fielddata=true，以便将fielddata加载到内存中。注意，这可能会使用大量内存。



开启之前

在启用fielddata之前，请考虑为什么在聚合、排序或脚本中使用文本字段。这样做通常是没有意义的。

在索引之前会分析文本字段，以便通过搜索New或York可以找到像New York这样的值。当可能需要一个名为new york的bucket时，这个字段上的term聚合将返回一个new bucket和一个york bucket。

因此，你应该有一个文本字段用于全文搜索，和一个未分析的关键字字段，doc_values为聚合启用，如下所示:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "my_field": { 
          "type": "text",
          "fields": {
            "keyword": { 
              "type": "keyword"
            }
          }
        }
      }
    }
  }
}
```



text类型开启

```
PUT my_index/_mapping/_doc
{
  "properties": {
    "my_field": { 
      "type":     "text",
      "fielddata": true
    }
  }
}
```



Fielddata过滤可用于减少加载到内存中的词的数量，从而减少内存的使用。term可按频率过滤:

频率过滤器允许只加载文档频率在最小值和最大值之间的项，该值可以表示为绝对数字(当该数字大于1.0时)或百分比(例如0.01是1%，1.0是100%)。每段计算频率。百分比是基于字段中有值的文档的数量，而不是该部分中的所有文档。

通过min_segment_size指定段中应该包含的最小文档数，可以完全排除小段:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "tag": {
          "type": "text",
          "fielddata": true,
          "fielddata_frequency_filter": {
            "min": 0.001,
            "max": 0.1,
            "min_segment_size": 500
          }
        }
      }
    }
  }
}
```



## format

在JSON文档中，日期表示为字符串。Elasticsearch使用一组预先配置的格式来识别这些字符串并将其解析为一个长值，表示UTC中自epoch以来的毫秒数。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "date": {
          "type":   "date",
          "format": "yyyy-MM-dd"
        }
      }
    }
  }
}
```

## ignore_above

超过ignore_above设置的字符串将不会被索引或存储。对于字符串数组，ignore_above将分别应用于每个数组元素，超过ignore_above的字符串元素将不会被索引或存储。

> 所有的字符串/数组元素仍然会出现在_source字段中，如果后者是在Elasticsearch中默认启用的。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "message": {
          "type": "keyword",
          "ignore_above": 20 
        }
      }
    }
  }
}

PUT my_index/_doc/1 
{
  "message": "Syntax error"
}

PUT my_index/_doc/2 
{
  "message": "Syntax error with some long stacktrace"
}

GET _search 
{
  "aggs": {
    "messages": {
      "terms": {
        "field": "message"
      }
    }
  }
}
```

这个选项对于防止Lucene的term字节长度限制为32766也很有用。

ignore_above的值是字符数，但是Lucene会计算字节数。如果使用带有许多非ascii字符的UTF-8文本，可能需要将限制设置为32766 / 4 = 8191，因为UTF-8字符最多占用4个字节。

## ignore_malformed

有时无法对接收的数据进行太多控制。一个用户发送的登录字段是日期，另一个用户发送的登录字段是电子邮件地址。

试图将错误的数据类型索引到字段中，默认情况下会抛出异常，并拒绝整个文档。ignore_malform参数如果设置为真，则允许忽略异常。格式错误的字段没有索引，但文档中的其他字段将正常处理。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "number_one": {
          "type": "integer",
          "ignore_malformed": true
        },
        "number_two": {
          "type": "integer"
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "text":       "Some text value",
  "number_one": "foo" 
}

PUT my_index/_doc/2
{
  "text":       "Some text value",
  "number_two": "foo" 
}
```

全局参数：

```
PUT my_index
{
  "settings": {
    "index.mapping.ignore_malformed": true 
  },
  "mappings": {
    "_doc": {
      "properties": {
        "number_one": { 
          "type": "byte"
        },
        "number_two": {
          "type": "integer",
          "ignore_malformed": false 
        }
      }
    }
  }
}
```

当ignore_malform被打开时，在索引时错误的字段会被悄悄地忽略。只要可能，建议保留包含格式不正确字段的文档数量，否则对该字段的查询将变得毫无意义。通过在特定的_ignore字段上使用exist或term查询，Elasticsearch可以很容易地检查有多少文档存在格式错误的字段。



## index

索引选项控制字段值是否被索引。它接受true或false，默认为true。没有索引的字段是不可查询的。



## index_options

index_options参数控制将哪些信息添加到反向索引中，用于搜索和高亮显示。它接受以下设置:

```
docs 只有文档号被索引。
freqs 文档编号和term频率被索引。词频用于给重复词评分高于单个词评分。
positions 文档编号、term频率和term位置(或顺序)被索引。位置可用于邻近度或短语查询。
offsets 对文档编号、term频率、位置以及开始和结束字符偏移量(将term映射回原始字符串)进行索引。 unified highlighter使用偏移来加速高亮。
```

> 在6.0.0中，数值字段不赞成使用index_options参数。

## fields 

为不同的目的以不同的方式索引同一个字段通常很有用。这就是多字段的目的。例如，字符串字段可以映射为文本字段用于全文搜索，也可以映射为关键字字段用于排序或聚合:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "city": {
          "type": "text",
          "fields": {
            "raw": { 
              "type":  "keyword"
            }
          }
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "city": "New York"
}

PUT my_index/_doc/2
{
  "city": "York"
}

GET my_index/_search
{
  "query": {
    "match": {
      "city": "york" 
    }
  },
  "sort": {
    "city.raw": "asc" 
  },
  "aggs": {
    "Cities": {
      "terms": {
        "field": "city.raw" 
      }
    }
  }
}
```

混合分词器

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "text": { 
          "type": "text",
          "fields": {
            "english": { 
              "type":     "text",
              "analyzer": "english"
            }
          }
        }
      }
    }
  }
}

PUT my_index/_doc/1
{ "text": "quick brown fox" } 

PUT my_index/_doc/2
{ "text": "quick brown foxes" } 

GET my_index/_search
{
  "query": {
    "multi_match": {
      "query": "quick brown foxes",
      "fields": [ 
        "text",
        "text.english"
      ],
      "type": "most_fields" 
    }
  }
}
```



## norms 

norms 存储了各种标准化因素，这些因素稍后在查询时用于计算文档相对于查询的得分。

虽然norms对于评分很有用，但它也需要大量的磁盘空间(通常是索引中每个文档每个字段一个字节的顺序，甚至对于没有这个特定字段的文档也是如此)。因此，如果你不需要在某个特定领域得分，你应该禁用该领域的norms 。特别是，对于仅用于过滤或聚合的字段，情况就是如此。

> 对于相同索引中的相同名称的字段，规范设置必须具有相同的设置。

禁用

```
PUT my_index/_mapping/_doc
{
  "properties": {
    "title": {
      "type": "text",
      "norms": false
    }
  }
}
```

> norms 不会立即被删除，但是当你继续索引新的文档时，旧的片段会被合并成新的片段，norms 会被删除。在norms 被删除的字段上的任何分数计算都可能返回不一致的结果，因为一些文档不再有norms ，而其他文档可能仍然有norms 。



## null_value

不能索引或搜索空值。当一个字段被设置为null(或一个空数组或一个空值数组)时，它被视为该字段没有值。null_value参数允许用指定的值替换显式的空值，以便对其进行索引和搜索。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "status_code": {
          "type":       "keyword",
          "null_value": "NULL" 
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "status_code": null
}

PUT my_index/_doc/2
{
  "status_code": [] 
}

GET my_index/_search
{
  "query": {
    "term": {
      "status_code": "NULL" 
    }
  }
}
```

> null_value需要与字段具有相同的数据类型。例如，一个长字段不能有字符串null_value。
>
> null_value只影响数据索引的方式，它不修改_source文档。



## position_increment_gap

经过分析的文本字段考虑了term的位置，以便能够支持邻近或短语查询。当索引具有多个值的文本字段时，在值之间添加一个“假”间隙，以防止大多数短语查询在值之间匹配。这个间隙的大小使用position_increment_gap配置，默认值为100。

```
PUT my_index/_doc/1
{
    "names": [ "John Abraham", "Lincoln Smith"]
}


GET my_index/_search
{
    "query": {
        "match_phrase": {
            "names": {
                "query": "Abraham Lincoln"   //这个短语查询与我们的文档不匹配，这是完全预期的。
            }
        }
    }
}

GET my_index/_search
{
    "query": {
        "match_phrase": {
            "names": {
                "query": "Abraham Lincoln",
                "slop": 101  //这个短语查询匹配我们的文档，即使Abraham和Lincoln在不同的字符串中，因为slop > position_increment_gap。
            }
        }
    }
}
```

映射

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "names": {
          "type": "text",
          "position_increment_gap": 0 
        }
      }
    }
  }
}
```

## properties

```
PUT my_index
{
  "mappings": {
    "_doc": { 
      "properties": {
        "manager": { 
          "properties": {
            "age":  { "type": "integer" },
            "name": { "type": "text"  }
          }
        },
        "employees": { 
          "type": "nested",
          "properties": {
            "age":  { "type": "integer" },
            "name": { "type": "text"  }
          }
        }
      }
    }
  }
}

PUT my_index/_doc/1 
{
  "region": "US",
  "manager": {
    "name": "Alice White",
    "age": 30
  },
  "employees": [
    {
      "name": "John Smith",
      "age": 34
    },
    {
      "name": "Peter Brown",
      "age": 26
    }
  ]
}
```

## search_analyzer

通常，在索引时和搜索时应该使用相同的分析器，以确保查询中的term与倒排索引中的term格式相同。不过，有时在搜索时使用不同的分析器是有意义的，比如在使用edge_ngram标记器进行自动完成时。

默认情况下，查询将使用字段映射中定义的分析器，但这可以用search_analyzer设置覆盖:

```
PUT my_index
{
  "settings": {
    "analysis": {
      "filter": {
        "autocomplete_filter": {
          "type": "edge_ngram",
          "min_gram": 1,
          "max_gram": 20
        }
      },
      "analyzer": {
        "autocomplete": { 
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "autocomplete_filter"
          ]
        }
      }
    }
  },
  "mappings": {
    "_doc": {
      "properties": {
        "text": {
          "type": "text",
          "analyzer": "autocomplete", 
          "search_analyzer": "standard" 
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "text": "Quick Brown Fox" 
}

GET my_index/_search
{
  "query": {
    "match": {
      "text": {
        "query": "Quick Br", 
        "operator": "and"
      }
    }
  }
}
```

## similarity

Elasticsearch允许配置评分算法或每个字段的相似性。相似度设置提供了一种简单的方法来选择除了默认的BM25(比如TF/IDF)之外的相似度算法。

相似点主要用于文本字段，但也可以应用于其他字段类型。

以通过调优内置相似点的参数来配置定制相似点。

```
BM25 	Okapi BM25算法
classic 	TF/IDF算法
boolean 一个简单的布尔相似度，当不需要进行全文排序并且评分应该仅基于查询词是否匹配时使用。布尔相似性给term一个与查询提升相等的分数。
```

映射

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "default_field": { 
          "type": "text"
        },
        "boolean_sim_field": {
          "type": "text",
          "similarity": "boolean" 
        }
      }
    }
  }
}
```

# 内置字段



## 定义字段

_index

_uid

_type

_id



## 文档source字段

_source

_size

```
sudo bin/elasticsearch-plugin install mapper-size
```



## 索引内置字段

_all

一个对所有其他字段的值进行索引的全部字段。默认情况下禁用。

_field_names

文档中包含非空值的所有字段。用于索引文档中每个字段的名称的_field_names字段，该文档中包含除null之外的任何值。exists查询使用该字段查找特定字段具有或不具有任何非空值的文档。

现在，`_field_names`字段只对禁用doc_values和规范的字段的名称进行索引。对于启用了doc_values或norm的字段，exists查询仍然可用，但不会使用_field_names字段。

禁用`_field_names`通常是不必要的，因为它不再像以前那样携带索引开销。如果有很多有doc_values和norms禁用的字段，不需要执行存在查询使用这些字段，想禁用_field_names添加以下映射:

```
PUT tweets
{
  "mappings": {
    "_doc": {
      "_field_names": {
        "enabled": false
      }
    }
  }
}
```

_ignored

6.4添加，在索引时由于ignore_malform而被忽略的文档中的所有字段。_ignore字段索引并存储文档中被忽略的每个字段的名称，这些字段是由于格式错误和ignore_malform被打开而被忽略的。

该字段可通过term、term和exists查询进行搜索，并作为搜索结果的一部分返回。

```
GET _search
{
  "query": {
    "exists": {
      "field": "_ignored"
    }
  }
}

GET _search
{
  "query": {
    "term": {
      "_ignored": "@timestamp"
    }
  }
}
```



_routing

公式：shard_num = hash(_routing) % num_primary_shards

根据路由索引和删除文档

```
PUT my_index/_doc/1?routing=user1&refresh=true 
{
  "title": "This is a document"
}

GET my_index/_doc/1?routing=user1 
```

获取路由的值

```
GET my_index/_search
{
  "query": {
    "terms": {
      "_routing": [ "user1" ] 
    }
  }
}
```

根据路由值搜索

```
GET my_index/_search?routing=user1,user2 
{
  "query": {
    "match": {
      "title": "document"
    }
  }
}
```

设置路由为必须参数

```
PUT my_index2
{
  "mappings": {
    "_doc": {
      "_routing": {
        "required": true 
      }
    }
  }
}

PUT my_index2/_doc/1    //错误
{
  "text": "No routing value provided"
}
```

_meta

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "_meta": { 
        "class": "MyApp::User",
        "version": {
          "min": "1.0",
          "max": "1.3"
        }
      }
    }
  }
}

PUT my_index/_mapping/_doc
{
  "_meta": {
    "class": "MyApp2::User3",
    "version": {
      "min": "1.3",
      "max": "1.5"
    }
  }
}
```

# 动态映射

## 动态字段映射

控制参数：dynamic

映射类型参考：

```
null   没有字段
true/false  boolean
floating point number  float
integer  long
object  object
array 取决于数组中的第一个非空值。
string 
```



## 日期探测

参数：`date_detection` 默认开启

参数：dynamic_date_formats 默认探测格式为

[ `"strict_date_optional_time"`,`"yyyy/MM/dd HH:mm:ss Z||yyyy/MM/dd Z"`]

```
PUT my_index/_doc/1
{
  "create_date": "2015/09/02"
}

GET my_index/_mapping 
```

关闭日期探测

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "date_detection": false
    }
  }
}

PUT my_index/_doc/1 
{
  "create": "2015/09/02"
}
```

自定义探测格式

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic_date_formats": ["MM/dd/yyyy"]
    }
  }
}
PUT my_index/_doc/1
{
  "create_date": "09/25/2015"
}
```



## 数值探测

JSON支持本地浮点和整数数据类型，但一些应用程序或语言有时可能将数字呈现为字符串。通常正确的解决方案是显式映射这些字段，但数字检测(默认禁用)可以自动做到这一点:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "numeric_detection": true
    }
  }
}

PUT my_index/_doc/1
{
  "my_float":   "1.0", 
  "my_integer": "1" 
}
```

## 动态模板

原始字段名{name}和检测到的datatype {dynamic_type}模板变量可以在映射规范中用作占位符。

> 动态字段映射只在字段包含具体值时添加——而不是null或空数组。这意味着，如果在dynamic_template中使用了null_value选项，那么它只会在第一个具有该字段的具体值的文档被索引之后应用。

```
  "dynamic_templates": [
    {
      "my_template_name": { 
        ...  match conditions ...  //匹配条件可以包括:match_mapping_type、match、match_pattern、unmatch、path_match、path_unmatch。
        "mapping": { ... } 
      }
    },
    ...
  ]
```

### match_mapping_type

match_mapping_type是json解析器检测到的数据类型。因为JSON不允许区分长数据和整数，或者双精度数据和浮点数据，所以它总是选择较宽的数据类型。long表示整数，double表示浮点数。

可以自动检测到下列数据类型:

-  当`true` 或者`false` 发生时，为`boolean`类型
- 当日期探测开启，并且匹配配置的字符串格式时，为date类型
- 有小数部分的数字为double类型
- 没有小数部分的数字为long类型
- 对象类型
- 字符串为string类型

*也可以用来匹配所有的数据类型。

例如，如果我们想要将所有整数字段映射为integer而不是long，将所有string字段映射为text和keyword，我们可以使用以下模板:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic_templates": [
        {
          "integers": {
            "match_mapping_type": "long",
            "mapping": {
              "type": "integer"
            }
          }
        },
        {
          "strings": {
            "match_mapping_type": "string",
            "mapping": {
              "type": "text",
              "fields": {
                "raw": {
                  "type":  "keyword",
                  "ignore_above": 256
                }
              }
            }
          }
        }
      ]
    }
  }
}

PUT my_index/_doc/1
{
  "my_integer": 5, 
  "my_string": "Some string" 
}
```

### `match` and `unmatch`

 match参数使用模式来对字段名进行匹配，而unmatch使用模式来排除通过match匹配的字段。

下面的例子匹配所有名称以long开头的字符串字段(除了以text结尾的)，并将它们映射为long字段:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic_templates": [
        {
          "longs_as_strings": {
            "match_mapping_type": "string",
            "match":   "long_*",
            "unmatch": "*_text",
            "mapping": {
              "type": "long"
            }
          }
        }
      ]
    }
  }
}

PUT my_index/_doc/1
{
  "long_num": "5", 
  "long_text": "foo" 
}
```

### `match_pattern`

 match_pattern参数调整匹配参数的行为，这样它就可以在字段名上支持完整的Java正则表达式匹配，而不是简单的通配符，例如:

```
  "match_pattern": "regex",
  "match": "^profit_\d+$"
```

### `path_match` and `path_unmatch`

 path_match和path_unmatch参数的工作方式与match和unmatch相同，但操作在字段的完整的虚线路径上，而不仅仅是最终的名称，例如some_object.*.some_field。

这个示例将name对象中所有字段的值复制到顶层的full_name字段，middle字段除外:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic_templates": [
        {
          "full_name": {
            "path_match":   "name.*",
            "path_unmatch": "*.middle",
            "mapping": {
              "type":       "text",
              "copy_to":    "full_name"
            }
          }
        }
      ]
    }
  }
}

PUT my_index/_doc/1
{
  "name": {
    "first":  "Alice",
    "middle": "Mary",
    "last":   "White"
  }
}
```

### `{name}` and `{dynamic_type}`

 在映射中，{name}和{dynamic_type}占位符被替换为字段名和检测到的动态类型。下面的示例将所有字符串字段设置为使用与字段同名的分析器，并对所有非字符串字段禁用doc_values:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic_templates": [
        {
          "named_analyzers": {
            "match_mapping_type": "string",
            "match": "*",
            "mapping": {
              "type": "text",
              "analyzer": "{name}"
            }
          }
        },
        {
          "no_doc_values": {
            "match_mapping_type":"*",
            "mapping": {
              "type": "{dynamic_type}",
              "doc_values": false
            }
          }
        }
      ]
    }
  }
}

PUT my_index/_doc/1
{
  "english": "Some English text", 
  "count":   5 
}
```



## 动态模板示例

### 结构化搜索

默认情况下，Elasticsearch将把字符串字段映射为文本字段和关键字字段。然而，如果只是索引结构化的内容，对全文搜索不感兴趣，可以使Elasticsearch映射字段仅为'关键字'。注意，这意味着为了搜索这些字段，将不得不搜索与索引完全相同的值。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic_templates": [
        {
          "strings_as_keywords": {
            "match_mapping_type": "string",
            "mapping": {
              "type": "keyword"
            }
          }
        }
      ]
    }
  }
}
```

### 仅分析字段搜索

与前面的例子相反,如果唯一关心的是全文搜索,且不打算运行聚合,排序或精确的搜索字符串字段,设置Elasticsearch映射它只作为一个文本字段(这是默认行为之前5.0):

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic_templates": [
        {
          "strings_as_text": {
            "match_mapping_type": "string",
            "mapping": {
              "type": "text"
            }
          }
        }
      ]
    }
  }
}
```

### 禁用norms

norms是指数时间的评分因素。如果不关心评分(例如，如果从不按评分对文档排序，就会出现这种情况)，那么可以在索引中禁用这些评分因子的存储，从而节省一些空间。

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic_templates": [
        {
          "strings_as_keywords": {
            "match_mapping_type": "string",
            "mapping": {
              "type": "text",
              "norms": false,
              "fields": {
                "keyword": {
                  "type": "keyword",
                  "ignore_above": 256
                }
              }
            }
          }
        }
      ]
    }
  }
}
```

此模板中的sub关键字字段与动态映射的默认规则一致。当然，如果不需要它们，因为不需要对该字段执行精确的搜索或聚合，那么可以像前一节所描述的那样删除它。

### 时间序列

当使用Elasticsearch进行时间序列分析时，通常会有许多数字字段，将经常聚合但从不过滤。在这种情况下，可以禁用索引在这些字段，以节省磁盘空间，也可能获得一些索引速度:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "dynamic_templates": [
        {
          "unindexed_longs": {
            "match_mapping_type": "long",
            "mapping": {
              "type": "long",
              "index": false
            }
          }
        },
        {
          "unindexed_doubles": {
            "match_mapping_type": "double",
            "mapping": {
              "type": "float",   //与默认的动态映射规则一样，双精度浮点数被映射为浮点数，通常足够精确，但需要一半的磁盘空间。
              "index": false
            }
          }
        }
      ]
    }
  }
}
```