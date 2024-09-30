# 全文查询

全文查询使您能够搜索已分析的文本字段，比如电子邮件的正文。查询字符串在索引期间应使用相同分词器进行字段处理。



## 参数

minimum_should_match

lenient：可以将lenient参数设置为true来忽略由数据类型不匹配引起的异常，例如尝试用文本查询字符串查询数值字段。默认值为false。



## match query（标准匹配查询）

用于执行全文查询的标准查询，包括模糊匹配和短语或邻近查询。

match查询接受文本/数字/日期，对它们进行分词，并构造一个查询。例如:

```
GET /_search
{
    "query": {
        "match" : {
            "message" : "this is a test"
        }
    }
}
```

注意，message是字段的名称，可以用任何字段的名称代替。

match查询的类型是boolean型。它意味着对提供的文本进行分析，从分析所得的文本中构造一个布尔查询。operator标志可以设置为or或and来控制布尔子句(默认值为or)。

```
GET /_search
{
    "query": {
        "match" : {
            "message" : {
                "query" : "this is a test",
                "operator" : "and"
            }
        }
    }
}
```

可以设置分词器来控制对文本的分析过程。它默认为字段显式映射定义，或默认的搜索分词器。



### fuzziness

模糊性允许基于被查询字段的类型进行模糊匹配。

相关参数：

```
prefix_length：
max_expansions:
fuzzy_rewrite：控制如何重写查询
fuzzy_transpositions：是否允许模糊换位(ab→ba)，默认是true
```

如果设置了模糊选项，查询将使用`top_terms_blended_freqs_${max_expansions}`作为它的重写方法。

> 请注意，模糊匹配并不应用于具有同义词的词项，因为在底层，这些词项被扩展为一个特殊的同义词查询，该查询混合了词项频率，不支持模糊扩展。

```
GET /_search
{
    "query": {
        "match" : {
            "message" : {
                "query" : "this is a testt",
                "fuzziness": "AUTO"
            }
        }
    }
}
```



### zero_terms_query

如果分词器像stop过滤器那样删除查询中的所有标记，则默认行为是根本不匹配任何文档。为了改变这一点，可以使用zero_terms_query选项，该选项接受none(默认)和所有匹配_all查询的值。

```
GET /_search
{
    "query": {
        "match" : {
            "message" : {
                "query" : "to be or not to be",
                "operator" : "and",
                "zero_terms_query": "all"
            }
        }
    }
}
```



### cutoff_frequency

在查询字符串中的词项时，可以将词汇分为低频词和高频词两类，这些词语与文档内容并不相关。该参数可以将查询字符串中的词项分为高频词和低频词。低频词组成bulk查询，高频词只用来评分，在此基础上形成一个性能上的提升。如果范围在`[0..1]`，则cutoff_frequency指相对于文档总数的出现频率，如果大于或等于1.0，则表示一个绝对值。

该查询允许在运行时动态处理stopwords（停顿词），它是独立的，不需要stopword文件。它防止对高频率词项进行评分/迭代，并且只考虑那些与文档匹配的更重要/更低频率的词项。但是，如果所有查询条件都高于给定的cutoff_frequency，那么查询将自动转换为纯连接(和)查询，以确保快速执行。

```
GET /_search
{
  "query": {
    "match": {
      "message": {
        "query": "Quick and the dead",
        "cutoff_frequency": 0.01
      }
    }
  }
}

任何词项出现在文档中超过1%，被认为是高频词。cutoff_frequency 配置可以指定为一个分数（ 0.01 ）或者一个正整数（ 5 ）。

该查询在执行时转换为以下查询：
{
  "bool": {
    "must": { 
      "bool": {
        "should": [
          { "term": { "text": "quick" }},  //低频词
          { "term": { "text": "dead"  }}   //低频词
        ]
      }
    },
    "should": { 
      "bool": {
        "should": [
          { "term": { "text": "and" }},  //高频词
          { "term": { "text": "the" }}    //高频词
        ]
      }
    }
  }
}
```



### synonym（同义词）

```
GET /_search
{
   "query": {
       "match" : {
           "message": {
               "query" : "ny city",
               "auto_generate_synonyms_phrase_query" : false
           }
       }
   }
}
```



## match_phrase query （短语匹配查询）

类似于match查询，但用于匹配准确的短语或单词接近匹配。

match_phrase查询分析文本，并从分析的文本中创建一个短语查询。例如:

```
GET /_search
{
    "query": {
        "match_phrase" : {
            "message" : "this is a test"
        }
    }
}
```

可以设置分词器来控制哪个分词器将对文本进行分词。默认为字段显式映射定义和搜索分词器，例如:

```
GET /_search
{
    "query": {
        "match_phrase" : {
            "message" : {
                "query" : "this is a test",
                "analyzer" : "my_analyzer"
            }
        }
    }
}
```

该查询还接受zero_terms_query，如上文所述。



## match_phrase_prefix query （前缀查询）

类似于match_phrase查询，但是对最终的单词执行通配符搜索。

match_phrase_prefix与match_phrase相同，只是它允许在文本中的最后一个词项上进行前缀匹配。例如:

```
GET /_search
{
    "query": {
        "match_phrase_prefix" : {
            "message" : "quick brown f"
        }
    }
}
```

它接受与短语类型相同的参数。此外，它还接受一个max_expansions参数(默认值为50)，该参数可以控制最后一个词将被扩展到多少个后缀。强烈建议将其设置为可接受的值，以控制查询的执行时间。例如:

```
GET /_search
{
    "query": {
        "match_phrase_prefix" : {
            "message" : {
                "query" : "quick brown f",
                "max_expansions" : 10
            }
        }
    }
}
```



## multi_match query（混合匹配查询）

 匹配查询的多字段版本。

multi_match查询建立在匹配查询之上，允许多字段查询:

```
GET /_search
{
  "query": {
    "multi_match" : {
      "query":    "this is a test", 
      "fields": [ "subject", "message" ] 
    }
  }
}
```

字段可以用通配符指定，例如:

```
GET /_search
{
  "query": {
    "multi_match" : {
      "query":    "Will Smith",
      "fields": [ "title", "*_name" ] 
    }
  }
}
```

 单个字段可以使用插入符号(^)进行增强:

```
GET /_search
{
  "query": {
    "multi_match" : {
      "query" : "this is a test",
      "fields" : [ "subject^3", "message" ] 
    }
  }
}
subject字段的重要性是message字段的三倍。
```

如果没有提供字段，multi_match查询默认`index.query.default_field`索引设置为`*`。`*`表示提取映射中符合词项查询条件的所有字段，并过滤元数据字段。然后将所有提取的字段组合起来构建一个查询。

> 重要：如果您有大量的字段，上述自动扩展可能会导致查询大量字段，从而导致性能问题。在以后的版本中(在7.0中声明)，一次查询的字段将限制在不超过1024个。

multi_match查询内部执行的方式取决于类型参数，可以设置为:

```
best_fields 
(默认)查找匹配任何字段的文档，但使用来自最佳字段的_score。

most_fields 
查找匹配任何字段的文档，并合并每个字段的_score。

cross_fields 
用同一个分词器处理字段，就好像它们是一个大字段。查找每一个词在任何字段。

phrase 
对每个字段运行一个match_phrase查询，并使用来自最佳字段的_score。

phrase_prefix 
在每个字段上运行match_phrase_prefix查询，并组合每个字段的_score。

```

示例：

```
GET /_search
{
  "query": {
    "multi_match" : {
      "query":      "brown fox",
      "type":       "best_fields",
      "fields":     [ "subject", "message" ],
      "tie_breaker": 0.3
    }
  }
}

等同于：
GET /_search
{
  "query": {
    "dis_max": {
      "queries": [
        { "match": { "subject": "brown fox" }},
        { "match": { "message": "brown fox" }}
      ],
      "tie_breaker": 0.3
    }
  }
}
```

通常best_fields类型使用单个最佳匹配字段的分数，但如果指定了tie_breaker，那么它计算的分数如下:

1、来自最佳匹配字段的分数

2、为所有其他匹配字段附加上tie_breaker * _score



## common terms query（常规词项查询）

 一个更专业的查询，给予不常见的词更多的偏好。

 common terms查询是stopwords的现代替代品，它提高了搜索结果的精确度和召回率(通过考虑stopwords)，同时又不牺牲性能。



问题

查询中的每个词都有一个开销。搜索“The brown fox”需要三个词项查询，分别针对“The”、“brown”和“fox”进行查询，所有这些查询都是针对索引中的所有文档执行的。对“The”的查询可能匹配许多文档，因此对相关性的影响比其他两个词项小得多。

以前，这个问题的解决方案是忽略高频项。通过将“the”作为stopword处理，我们减小了索引大小并减少了需要执行的词汇查询的数量。

这种方法的问题是，虽然stopwords对相关性的影响很小，但它们仍然很重要。如果我们删除stopwords，我们就会失去准确性(比如我们无法区分“happy”和“not happy”)，我们就会失去记忆(比如像“The The”或“To be or not to be”这样的文本在索引中根本不存在)。



方案

常用词项查询将查询词项分为两组:较重要的(即低频词项)和较不重要的(即高频词项，这些词项以前是停止词)。

首先，它搜索与更重要的词项匹配的文档。这些词项出现在较少的文件中，对相关性有较大的影响。

然后，它对不太重要的词项执行第二次查询——这些词项经常出现并且对相关性影响不大。但是它没有计算所有匹配文档的相关性分数，而是只计算第一个查询已经匹配的文档的_score。通过这种方式，高频项可以提高相关性的计算，而不需要付出较差的性能代价。

如果查询只包含高频词项，那么单个查询将作为AND(合取)查询执行，换句话说，需要所有词项。尽管每个单独的词项将匹配许多文档，但是词项的组合将缩小结果集，使之只匹配最相关的那些。单个查询也可以作为OR执行，并带有特定的minimum_should_match，在这种情况下，可能应该使用足够高的值。

Terms根据cutoff_frequency分配给高频或低频组，该频率可以指定为绝对频率(>=1)或相对频率(0.0 .. 1.0)。(请记住，文档频率是按每个分片级别计算的。)

也许这个查询最有趣的特性是它自动适应特定于某个域的stopwords。例如，在一个视频托管网站上，像“clip”或“video”这样的常见词项将自动表现为停止词，而不需要手动维护列表。

在本例中，文档频率大于0.1%的单词(如“this”和“is”)将被视为通用词项。

```
GET /_search
{
    "query": {
        "common": {
            "body": {
                "query": "this is bonsai cool",
                "cutoff_frequency": 0.001
            }
        }
    }
}
```

可以使用`minimum_should_match (high_freq, low_freq)`、`low_freq_operator`(默认的“or”)和`high_freq_operator`(默认的“or”)参数控制应该匹配的词的数量。

对于低频词项，将low_freq_operator设置为“and”，以使所有词项都是必需的:

```
GET /_search
{
    "query": {
        "common": {
            "body": {
                "query": "nelly the elephant as a cartoon",
                "cutoff_frequency": 0.001,
                "low_freq_operator": "and"
            }
        }
    }
}

这大致相当于:
GET /_search
{
    "query": {
        "bool": {
            "must": [
            { "term": { "body": "nelly"}},
            { "term": { "body": "elephant"}},
            { "term": { "body": "cartoon"}}
            ],
            "should": [
            { "term": { "body": "the"}},
            { "term": { "body": "as"}},
            { "term": { "body": "a"}}
            ]
        }
    }
}
```

或者使用minimum_should_match指定必须出现的低频词的最小数量或百分比，例如:

```
GET /_search
{
    "query": {
        "common": {
            "body": {
                "query": "nelly the elephant as a cartoon",
                "cutoff_frequency": 0.001,
                "minimum_should_match": 2
            }
        }
    }
}

这大致相当于:
GET /_search
{
    "query": {
        "bool": {
            "must": {
                "bool": {
                    "should": [
                    { "term": { "body": "nelly"}},
                    { "term": { "body": "elephant"}},
                    { "term": { "body": "cartoon"}}
                    ],
                    "minimum_should_match": 2
                }
            },
            "should": [
                { "term": { "body": "the"}},
                { "term": { "body": "as"}},
                { "term": { "body": "a"}}
                ]
        }
    }
}

```

不同的minimum_should_match可以应用于带有附加low_freq和high_freq参数的低频和高频项。下面是一个提供附加参数的例子(注意结构的变化):

```
GET /_search
{
    "query": {
        "common": {
            "body": {
                "query": "nelly the elephant not as a cartoon",
                "cutoff_frequency": 0.001,
                "minimum_should_match": {
                    "low_freq" : 2,
                    "high_freq" : 3
                }
            }
        }
    }
}

这大致相当于:

GET /_search
{
    "query": {
        "bool": {
            "must": {
                "bool": {
                    "should": [
                    { "term": { "body": "nelly"}},
                    { "term": { "body": "elephant"}},
                    { "term": { "body": "cartoon"}}
                    ],
                    "minimum_should_match": 2
                }
            },
            "should": {
                "bool": {
                    "should": [
                    { "term": { "body": "the"}},
                    { "term": { "body": "not"}},
                    { "term": { "body": "as"}},
                    { "term": { "body": "a"}}
                    ],
                    "minimum_should_match": 3
                }
            }
        }
    }
}
```

在这种情况下，这意味着高频词只有在至少有三个时才会对相关性产生影响。但是minimum_should_match用于高频词项的最有趣的用法是当只有高频词项时:

```
GET /_search
{
    "query": {
        "common": {
            "body": {
                "query": "how not to be",
                "cutoff_frequency": 0.001,
                "minimum_should_match": {
                    "low_freq" : 2,
                    "high_freq" : 3
                }
            }
        }
    }
}

相当于：

GET /_search
{
    "query": {
        "bool": {
            "should": [
            { "term": { "body": "how"}},
            { "term": { "body": "not"}},
            { "term": { "body": "to"}},
            { "term": { "body": "be"}}
            ],
            "minimum_should_match": "3<50%"
        }
    }
}
```

因此，与使用AND相比，使用高频生成的查询的限制要少一些。common term查询还支持boost和analyzer作为参数。



## query_string query（字符串查询）

支持高级的Lucene语法，适合高级用户使用。

使用查询解析器来解析其内容的查询。下面是一个例子:

```
GET /_search
{
    "query": {
        "query_string" : {
            "default_field" : "content",
            "query" : "this AND that OR thus"
        }
    }
}
```

 `query_string`查询解析输入并在操作符周围分割文本。每个文本部分都是独立分析的。例如下面的查询:

```
GET /_search
{
    "query": {
        "query_string" : {
            "default_field" : "content",
            "query" : "(new york city) OR (big apple)" 
        }
    }
}

将被分割成new york city和big apple，每个字段进行独立的分析。
```



## simple_query_string query （简单字符串查询）

 适合直接向用户公开的更简单、更健壮的query_string语法版本。

使用SimpleQueryParser解析其上下文的查询。与常规的query_string查询不同，simple_query_string查询永远不会抛出异常，并且会丢弃查询中无效的部分。下面是一个例子:

```
GET /_search
{
  "query": {
    "simple_query_string" : {
        "query": "\"fried eggs\" +(eggplant | potato) -frittata",
        "fields": ["title^5", "body"],
        "default_operator": "and"
    }
  }
}
```



