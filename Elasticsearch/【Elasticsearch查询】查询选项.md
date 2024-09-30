## q

查询字符串(映射到' query_string '查询）

```
GET  /book_publisher/_search?q=authors:matthew
```



## Explain

为每次命中启用解释其分数是如何计算的。

```
GET  /out-7.7.0-2020.10.29/_search?explain=true

或者
GET /_search/out-7.7.0-2020.10.29
{
    "explain": true,
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```



查询和特定文档计算分数解释。这可以提供有用的反馈，无论文档是否匹配特定的查询。

注意，必须为索引参数提供单个索引。

```
GET /twitter/_doc/0/_explain
{
      "query" : {
        "match" : { "message" : "elasticsearch" }
      }
}

```

?q参数查询

```
GET /twitter/_doc/0/_explain?q=message:elasticsearch（同上）
```



## version

 为每个搜索结果返回一个版本。

```
GET /_search
{
    "version": true,
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```

## Count

count请求允许轻松地执行查询并获得该查询的匹配数。它可以跨一个或多个索引执行。查询可以使用简单的查询字符串作为参数提供，也可以使用在请求主体中定义的查询DSL提供。下面是一个例子:

```
PUT /twitter/_doc/1?refresh
{
    "user": "kimchy"
}

GET /twitter/_doc/_count?q=user:kimchy

GET /twitter/_doc/_count
{
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```

## Sort

排序。可以是fieldName的形式，也可以是fieldName:asc/fieldName:desc。fieldName可以是文档中的一个实际字段，也可以是特殊的_score名称，用于指示基于分数的排序。可以有几个排序参数(顺序很重要)。

```
GET  /out-7.7.0-2020.10.29/_search?sort=log.offset
```

允许在特定字段上添加一个或多个排序。每种排序也可以反转。排序是按字段级别定义的，使用特殊字段名`_score`按分数排序，`_doc`按索引顺序排序。

```
GET /my_index/_search
{
  "sort": [
    {
      "post_date": {
        "order": "asc"
      }
    },
    "user",
    {
      "name": "desc"
    },
    {
      "age": "desc"
    },
    "_score"
  ],
  "query": {
    "term": {
      "user": "kimchy"
    }
  }
}
```

除了是最有效的排序顺序之外，`_doc`没有真正的用例。因此，如果不关心文档返回的顺序，那么应该按_doc排序。这在滚动时尤其有用。

### 排序值

每个文档的排序值也作为响应的一部分返回。



### 模式

Elasticsearch支持按数组或多值字段排序。mode选项控制选择什么数组值来对它所属的文档进行排序。模式选项可以有以下值:

```
min  max  sum  avg  median（中位数）
```

```
PUT /my_index/_doc/1?refresh
{
   "product": "chocolate",
   "price": [20, 4]
}

POST /_search
{
   "query" : {
      "term" : { "product" : "chocolate" }
   },
   "sort" : [
      {"price" : {"order" : "asc", "mode" : "avg"}}     // (20 + 4)/2 = 12
   ]
}
```



### 嵌套对象

Elasticsearch还支持按一个或多个嵌套对象中的字段排序。按nested字段排序支持有一个nested排序选项，具有以下属性:

```
path 
定义对嵌套对象进行排序。实际的排序字段必须是这个嵌套对象中的直接字段。按嵌套字段排序时，此字段是强制性的。

filter 
一个过滤器，嵌套路径内的内部对象应该与之匹配，以便通过排序将其字段值考虑在内。常见的情况是在嵌套过滤器或查询中重复查询/筛选。默认情况下，nested_filter是不活动的。

max_children 
选择排序值时每个根文档要考虑的最大子文档数。默认为无限。

nested 
与顶级嵌套相同，但应用于当前嵌套对象中的另一个嵌套路径。
```

在下面的示例中，offer是一个嵌套类型的字段。需要指定嵌套路径;否则，Elasticsearch不知道需要在哪个嵌套级别捕获排序值。

```
POST /_search
{
   "query" : {
      "term" : { "product" : "chocolate" }
   },
   "sort" : [
       {
          "offer.price" : {
             "mode" :  "avg",
             "order" : "asc",
             "nested": {
                "path": "offer",
                "filter": {
                   "term" : { "offer.color" : "blue" }
                }
             }
          }
       }
    ]
}
```

在下面的示例中，父字段和子字段的类型是嵌套的。nested_path需要在每个级别上指定;否则，Elasticsearch不知道需要在哪个嵌套级别捕获排序值。

```
POST /_search
{
   "query": {
      "nested": {
         "path": "parent",
         "query": {
            "bool": {
                "must": {"range": {"parent.age": {"gte": 21}}},
                "filter": {
                    "nested": {
                        "path": "parent.child",
                        "query": {"match": {"parent.child.name": "matt"}}
                    }
                }
            }
         }
      }
   },
   "sort" : [
      {
         "parent.child.age" : {
            "mode" :  "min",
            "order" : "asc",
            "nested": {
               "path": "parent",
               "filter": {
                  "range": {"parent.age": {"gte": 21}}
               },
               "nested": {
                  "path": "parent.child",
                  "filter": {
                     "match": {"parent.child.name": "matt"}
                  }
               }
            }
         }
      }
   ]
}
```

### 缺失值

缺失的参数指定了如何处理缺少排序字段的文档:缺失的值可以设置为`_last`、`_first`或自定义值(用于缺失文档的排序值)。默认值是`_last`。

```
GET /_search
{
    "sort" : [
        { "price" : {"missing" : "_last"} }
    ],
    "query" : {
        "term" : { "product" : "chocolate" }
    }
}
```

如果嵌套内部对象与nested_filter不匹配，则使用缺失的值。



### 忽略未映射字段

默认情况下，如果没有与某个字段关联的映射，搜索请求将失败。unmapped_type选项允许忽略没有映射的字段，也不按它们排序。此参数的值用于确定排序值。下面是它的用法示例:

```
GET /_search
{
    "sort" : [
        { "price" : {"unmapped_type" : "long"} }
    ],
    "query" : {
        "term" : { "product" : "chocolate" }
    }
}
```

如果所有查询的索引都没有price的映射，那么Elasticsearch将处理它，就像有一个long类型的映射一样，即使该索引中的所有文档都没有该字段的值。

### 跟踪分数

对字段进行排序时，不会计算分数。通过将track_scores设置为true，仍然会计算和跟踪分数。

```
GET /_search
{
    "track_scores": true,
    "sort" : [
        { "post_date" : {"order" : "desc"} },
        { "name" : "desc" },
        { "age" : "desc" }
    ],
    "query" : {
        "term" : { "user" : "kimchy" }
    }
}
```

### 内存方面的考虑

排序时，相关的已排序字段值被加载到内存中。这意味着每个分片应该有足够的内存来加载它们。对于基于字符串的类型，排序的字段不应该被analyzed/tokenized。对于数值类型，如果可能，建议显式地将类型设置为更窄的类型(如short、integer和float)。



