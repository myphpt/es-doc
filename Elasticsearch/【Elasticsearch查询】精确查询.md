# 复合查询

复合查询封装了其他复合查询或子查询，可以组合它们的结果和分数，改变它们的行为，或者从查询切换到过滤上下文。

## constant_score query  

 包装另一个查询，但在筛选器上下文中执行它的查询。给所有匹配的文档相同的“常量”_score。

```
GET /_search
{
    "query": {
        "constant_score" : {
            "filter" : {
                "term" : { "user" : "kimchy"}
            },
            "boost" : 1.2
        }
    }
}
```



## bool query  

 用于组合多个子查询或复合查询子句的默认查询，如must、should、must_not或filter子句。must和should子句的分数组合在一起——匹配的子句越多越好——而must_not和filter子句则在过滤器上下文中执行。

```
POST _search
{
  "query": {
    "bool" : {
      "must" : {
        "term" : { "user" : "kimchy" }
      },
      "filter": {
        "term" : { "tag" : "tech" }
      },
      "must_not" : {
        "range" : {
          "age" : { "gte" : 10, "lte" : 20 }
        }
      },
      "should" : [
        { "term" : { "tag" : "wow" } },
        { "term" : { "tag" : "elasticsearch" } }
      ],
      "minimum_should_match" : 1,
      "boost" : 1.0
    }
  }
}
```



## dis_max query  

 接受多个查询并返回与任何查询子句匹配的任何文档的查询。bool查询组合来自所有匹配查询的分数，而dis_max查询使用单个最佳匹配查询子句的分数。

```
GET /_search
{
    "query": {
        "dis_max" : {
            "tie_breaker" : 0.7,
            "boost" : 1.2,
            "queries" : [
                {
                    "term" : { "age" : 34 }
                },
                {
                    "term" : { "age" : 35 }
                }
            ]
        }
    }
}
```



## function_score query  

 使用函数修改主查询返回的分数，以考虑流行度、近似性、距离或脚本实现的自定义算法等因素。

 要使用function_score，用户必须定义一个查询和一个或多个函数，这些函数为查询返回的每个文档计算一个新分数。

```
GET /_search
{
    "query": {
        "function_score": {
            "query": { "match_all": {} },
            "boost": "5",
            "random_score": {}, 
            "boost_mode":"multiply"
        }
    }
}
```



## boosting query 

 返回与正查询匹配的文档，但减少与负查询匹配的文档的分数。

boosting查询可用于有效地降级与给定查询匹配的结果。与bool查询中的“NOT”子句不同，它仍然选择包含不需要的词语的文档，但会降低它们的总体得分。

```
GET /_search
{
    "query": {
        "boosting" : {
            "positive" : {
                "term" : {
                    "field1" : "value1"
                }
            },
            "negative" : {
                 "term" : {
                     "field2" : "value2"
                }
            },
            "negative_boost" : 0.2
        }
    }
}
```



## 单层嵌套

组成部分

```
{
   "bool" : {
      "must" :     [],
      "should" :   [],
      "must_not" : [],
   }
}
```

**`must`**  ： 所有的语句都 *必须（must）* 匹配，与 `AND` 等价。 

**`must_not`**  ： 所有的语句都 *不能（must not）* 匹配，与 `NOT` 等价。 

**`should`**  ： 至少有一个语句要匹配，与 `OR` 等价。 

```
GET /my_store/_doc/_search
{
  "query": {
    "bool": {
      "should": [
        {
          "term": {
            "price": 20
          }
        },
        {
          "term": {
            "productID": "XHDK-A-1293-#fJ3"
          }
        }
      ],
      "must_not": {
        "term": {
          "price": 30
        }
      }
    }
  }
}
```



## 双层嵌套

```
GET /my_store/_doc/_search
{
  "query": {
    "bool": {
      "should": [
        {
          "term": {
            "productID": "KDKE-B-9947-#kL5"
          }
        },
        {
          "bool": {
            "must": [
              {
                "term": {
                  "productID": "JODL-X-1937-#pV7"
                }
              },
              {
                "term": {
                  "price": 30
                }
              }
            ]
          }
        }
      ]
    }
  }
}
  
```



# 词项查询

全文查询将在执行之前对查询字符串进行分词，而词项级查询将对存储在反向索引中的精确词项进行操作，并且执行前对只对具有normalizer属性的keyword字段词项进行规范化。

这些查询通常用于数字、日期和枚举等结构化数据，而不是全文字段。或者，它们允许您在分析过程之前创建低级查询。

## term query（词项查询）

 查找包含在指定字段中确切指定的词项的文档。

词项查询查找包含倒排索引中指定的精确词项的文档。例如:

```
POST _search
{
  "query": {
    "term" : { "user" : "Kimchy" } 
  }
}
在用户字段的倒排索引中查找包含确切的词项Kimchy的文档。
```

权重：boost



Why doesn’t the term query match my document?

 字符串字段可以是text类型(作为全文处理，如电子邮件的正文)或keyword类型(作为精确值处理，如电子邮件地址或邮政编码)。精确值(如数字、日期和关键字)将字段中指定的精确值添加到反向索引中，以使它们可搜索。

但是，对`text` 字段进行分析。这意味着它们的值首先通过分析器生成一个词项列表，然后将其添加到反向索引中。

分析文本有很多方法:默认的standard analyzer会去掉大多数标点符号，将文本分解为单个单词，并将它们小写。例如，standard的分析器会将字符串“Quick Brown Fox!”分词为[`quick`, `brown`, `fox`].。

这个分析过程使得在一个大块段落中搜索单个单词成为可能。

词项查询在字段的倒索引中查找确切的词项—它不知道关于字段的分析器的任何信息。这使得它在keyword 字段、数字或日期字段中查找值非常有用。在查询全文文本字段时，使用match查询，它理解如何分析字段。

为了演示，请尝试下面的示例。首先，创建一个索引，指定字段映射，索引一个文档:

```
PUT my_index
{
  "mappings": {
    "_doc": {
      "properties": {
        "full_text": {
          "type":  "text" 
        },
        "exact_value": {
          "type":  "keyword" 
        }
      }
    }
  }
}

PUT my_index/_doc/1
{
  "full_text":   "Quick Foxes!", 
  "exact_value": "Quick Foxes!"  
}
```

现在，比较term查询和match查询的结果:

```
GET my_index/_search
{
  "query": {
    "term": {
      "exact_value": "Quick Foxes!" 
    }
  }
}

GET my_index/_search
{
  "query": {
    "term": {
      "full_text": "Quick Foxes!" 
    }
  }
}

GET my_index/_search
{
  "query": {
    "term": {
      "full_text": "foxes" 
    }
  }
}

GET my_index/_search
{
  "query": {
    "match": {
      "full_text": "Quick Foxes!" 
    }
  }
}
```



### 数字的精确查询

非评分模式查询数字

```
GET /my_store/products/_search
{
    "query" : {
        "constant_score" : { 
            "filter" : {
                "term" : { 
                    "price" : 20
                }
            }
        }
    }
}
```

### 文本的精确查询

1、text字段可设置为无需分析的

```
"properties" : {
                "productID" : {
                    "type" : "string",
                    "index" : "not_analyzed" 
                }
            }
```

2、直接设置为KeyWord类型，可通过非评分模式和布尔查询实现精确匹配



### 查询优化

理论上非评分查询 先于 评分查询执行。非评分查询任务旨在降低那些将对评分查询计算带来更高成本的文档数量，从而达到快速搜索的目的。





## terms query（多词项查询）

 查找包含指定字段中指定的任何确切词项的文档。

 筛选具有与所提供的任何词项(未分析)匹配的字段的文档。例如:

```
GET /_search
{
    "query": {
        "terms" : { "user" : ["kimchy", "elasticsearch"]}
    }
}
```



## terms_set query

返回与至少一个或多个提供的词项匹配的任何文档。这些词项没有被分析，因此必须精确匹配。必须匹配的词的数量在每个文档中都是不同的，或者由最小应匹配字段控制，或者在每个文档中计算最小应匹配脚本。

控制必须匹配的必需词汇的数量的字段必须是一个数字字段:

```
PUT /my-index
{
    "mappings": {
        "_doc": {
            "properties": {
                "required_matches": {
                    "type": "long"
                }
            }
        }
    }
}

PUT /my-index/_doc/1?refresh
{
    "codes": ["ghi", "jkl"],
    "required_matches": 2
}

PUT /my-index/_doc/2?refresh
{
    "codes": ["def", "ghi"],
    "required_matches": 2
}

GET /my-index/_search
{
    "query": {
        "terms_set": {
            "codes" : {
                "terms" : ["abc", "def", "ghi"],
                "minimum_should_match_field": "required_matches"
            }
        }
    }
}
```



## range query  （范围查询）

 查找指定字段中包含指定范围内的值(日期、数字或字符串)的文档。

```
GET _search
{
    "query": {
        "range" : {
            "age" : {
                "gte" : 10,
                "lte" : 20,
                "boost" : 2.0
            }
        }
    }
}
```

符号：

```
gt gte lt lte 
```

查询过去一个小时内的所有文档

```
"range" : {
    "timestamp" : {
        "gt" : "now-1h"
    }
}
```

某一段时间

```
"range" : {
    "timestamp" : {
        "gt" : "2020-01-01 00:00:00",
        "lt" : "2020-01-01 00:00:00||+1M" 
    }
}
```



## exists query （存在查询）

返回原始字段中至少有一个非空值的文档:

```
GET /_search
{
    "query": {
        "exists" : { "field" : "user" }
    }
}
```

不会被匹配到的情况：

```
{ "user": null }
{ "user": [] } 
{ "user": [null] } 
{ "foo":  "bar" } 
```



## null_value

如果字段映射包含null_value设置，则显式的空值将被指定的null_value替换。例如，如果用户字段映射如下:

```
PUT /example
{
  "mappings": {
    "_doc": {
      "properties": {
        "user": {
          "type": "keyword",
          "null_value": "_null_"
        }
      }
    }
  }
}
```

然后显式的空值将被索引为字符串null，当搜寻非空文档时，null值依然可以被搜索到

```
{ "user": null }
{ "user": [null] }
```

返回字段为空的文档：

```
GET /_search
{
    "query": {
        "bool": {
            "must_not": {
                "exists": {
                    "field": "user"
                }
            }
        }
    }
}
```

 

## prefix query （前缀查询）

 查找指定字段中包含以指定的确切前缀开头的词项的文档。

```
GET /_search
{ "query": {
    "prefix" : { "user" : "ki" }
  }
}
```

 权重：boost



## wildcard query （通配符查询） 

 查找指定字段中包含与指定模式匹配的词项的文档，其中模式支持单字符通配符(?)和多字符通配符(*)

```
GET /_search
{
    "query": {
        "wildcard" : { "user" : "ki*y" }
    }
}
```



## regexp query  （正则查询）

 查找指定字段中包含与指定的正则表达式匹配的词项的文档。

 注意:regexp查询的性能在很大程度上取决于所选的正则表达式。与使用lookaround正则表达式一样，匹配像`.*`这样的所有内容会非常慢。如果可能，您应该尝试在正则表达式开始之前使用一个长前缀。像`.*?+`会大大降低性能。

```
GET /_search
{
    "query": {
        "regexp":{
            "name.first": "s.*y"
        }
    }
}
```



## fuzzy query （模糊查询） 

 查找指定字段中包含与指定词项有模糊相似之词项的文档。模糊查询使用基于Levenshtein编辑距离的相似性。

 模糊查询生成在模糊性中指定的最大编辑距离内的匹配词项，然后检查词项字典，以找出这些生成的词项中哪些确实存在于索引中。最后一个查询使用最多max_expansions匹配的词项。

```
GET /_search
{
    "query": {
       "fuzzy" : { "user" : "ki" }
    }
}
```

高级查询：

```
GET /_search
{
    "query": {
        "fuzzy" : {
            "user" : {
                "value": "ki",
                "boost": 1.0,
                "fuzziness": 2,
                "prefix_length": 0,
                "max_expansions": 100
            }
        }
    }
}
```



## type query  （类型查询）

 筛选与所提供的文档/映射类型匹配的文档。

```
GET /_search
{
    "query": {
        "type" : {
            "value" : "_doc"
        }
    }
}
```



## ids query（ID查询）

 查找具有指定类型和id的文档。

```
GET /_search
{
    "query": {
        "ids" : {
            "type" : "_doc",
            "values" : ["1", "4", "100"]
        }
    }
}
```



# 