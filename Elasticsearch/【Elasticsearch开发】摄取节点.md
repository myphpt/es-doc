[TOC]

# Ingest Pipelines

 在实际建立文档索引之前，使用一个摄取节点对文档进行预处理。ingest节点拦截批量和索引请求，应用转换，然后将文档传递回索引或批量api。

`elasticsearch.yml`节点设置：

```
node.ingest: false
```

要在索引之前对文档进行预处理，请定义一个管道，该管道指定一系列处理器。每个处理器都以某种特定的方式转换文档。例如，管道可能有一个处理器从文档中删除一个字段，然后是另一个处理器重命名一个字段。然后，集群状态存储配置的管道。

要使用管道，只需在索引或批量请求上指定管道参数。这样，摄入节点就知道使用哪个管道。例如:

```
PUT my-index/_doc/my-id?pipeline=my_pipeline_id
{
  "foo": "bar"
}
```



## 定义管道

管道是一系列处理器的定义，它们按照声明的顺序执行。管道由两个主要字段组成:description和processors:

```
{
  "description" : "...",
  "processors" : [ ... ]
}
```

description是一个特殊字段，用于存储有关管道所做工作的有用描述。

processors参数定义了要按顺序执行的处理器列表。



## 添加管道

```
PUT _ingest/pipeline/my-pipeline-id
{
  "description" : "describe pipeline",
  "processors" : [
    {
      "set" : {
        "field": "foo",
        "value": "bar"
      }
    }
  ]
}
```

版本

```
PUT _ingest/pipeline/my-pipeline-id
{
  "description" : "describe pipeline",
  "version" : 123,
  "processors" : [
    {
      "set" : {
        "field": "foo",
        "value": "bar"
      }
    }
  ]
}
```



## 获取管道

根据管道ID获取

```
GET _ingest/pipeline/my-pipeline-id
```

对于每个返回的管道，都返回源和版本。版本对于知道节点拥有哪个版本的管道非常有用。您可以指定多个id来返回多个管道。还支持通配符。

管道版本

```
GET /_ingest/pipeline/my-pipeline-id?filter_path=*.version
```



## 删除管道

```
DELETE _ingest/pipeline/my-pipeline-id
```



## 模拟管道

模拟管道API针对请求主体中提供的一组文档执行特定的管道。

您可以指定一个现有的管道来针对提供的文档执行，或者在请求的主体中提供管道定义。

```
POST _ingest/pipeline/_simulate
{
  "pipeline" : {
    // pipeline definition here
  },
  "docs" : [
    { "_source": {/** first document **/} },
    { "_source": {/** second document **/} },
    // ...
  ]
}
```

下面是一个模拟请求的例子，在请求和响应中定义了管道:

```
POST _ingest/pipeline/_simulate
{
  "pipeline" :
  {
    "description": "_description",
    "processors": [
      {
        "set" : {
          "field" : "field2",
          "value" : "_value"
        }
      }
    ]
  },
  "docs": [
    {
      "_index": "index",
      "_type": "_doc",
      "_id": "id",
      "_source": {
        "foo": "bar"
      }
    },
    {
      "_index": "index",
      "_type": "_doc",
      "_id": "id",
      "_source": {
        "foo": "rab"
      }
    }
  ]
}
```

您可以使用模拟管道API来查看每个处理器在文档通过管道时如何影响它。要查看模拟请求中每个处理器的中间结果，可以向请求添加verbose参数。

```
POST _ingest/pipeline/_simulate?verbose
{
  "pipeline" :
  {
    "description": "_description",
    "processors": [
      {
        "set" : {
          "field" : "field2",
          "value" : "_value2"
        }
      },
      {
        "set" : {
          "field" : "field3",
          "value" : "_value3"
        }
      }
    ]
  },
  "docs": [
    {
      "_index": "index",
      "_type": "_doc",
      "_id": "id",
      "_source": {
        "foo": "bar"
      }
    },
    {
      "_index": "index",
      "_type": "_doc",
      "_id": "id",
      "_source": {
        "foo": "rab"
      }
    }
  ]
}
```





## 访问管道中的数据

管道中的处理器对通过管道传递的文档进行读写访问。处理器可以访问文档源中的字段和文档的元数据字段。

访问源中的字段很简单。您只需通过字段的名称引用它们。例如:

```
{
  "set": {
    "field": "my_field",
    "value": 582.1
  }
}
```

在此之上，来自源的字段总是可以通过_source前缀访问:

```
{
  "set": {
    "field": "_source.my_field",
    "value": 582.1
  }
}
```

元数据字段

```
{
  "set": {
    "field": "_id",
    "value": "1"
  }
}
```



## 转换的元数据字段

```
{
  "set": {
    "field": "received",
    "value": "{{_ingest.timestamp}}"
  }
}
```



## 访问模板

```
{
  "set": {
    "field": "field_c",
    "value": "{{field_a}} {{field_b}}"
  }
}

{
  "set": {
    "field": "{{service}}",
    "value": "{{code}}"
  }
}
```



## 管道中的条件执行

```
PUT _ingest/pipeline/drop_guests_network
{
  "processors": [
    {
      "drop": {
        "if": "ctx.network_name == 'Guest'"
      }
    }
  ]
}
```

插入数据

```
POST test/_doc/1?pipeline=drop_guests_network
{
  "network_name" : "Guest"
}
```



## 条件中处理嵌套类型

源文档通常包含嵌套的字段。如果文档中不存在父对象，应该注意避免nullpointerexception。例如，如果源文档没有顶级a对象或二级b对象，那么ctx.a.b.c可以抛出nullpointerexception。

为了防止nullpointerexception，应该使用null安全操作。幸运的是，可以使用`?.`使得操作null变得安全

```
PUT _ingest/pipeline/drop_guests_network
{
  "processors": [
    {
      "drop": {
        "if": "ctx.network?.name == 'Guest'"
      }
    }
  ]
}
```

插入文档

```
POST test/_doc/1?pipeline=drop_guests_network
{
  "network": {
    "name": "Guest"
  }
}
```

使用以下文档则会有空异常

```
POST test/_doc/2?pipeline=drop_guests_network
{
  "foo" : "bar"
}
```

源文档还可以这么写

```
{
  "network.name": "Guest"
}
```

在这种情况下需要使用扩展处理器

```
PUT _ingest/pipeline/drop_guests_network
{
  "processors": [
    {
      "dot_expander": {
        "field": "network.name"
      }
    },
    {
      "drop": {
        "if": "ctx.network?.name == 'Guest'"
      }
    }
  ]
}
```

但是，调用`. equalsignorecase`这样的方法不是空安全的，可能会导致`NullPointerException`。比如`'Guest'.equalsIgnoreCase(ctx.network?.name)`是安全的

`ctx.network?.name.equalsIgnoreCase('Guest')`就不是安全的

可以在条件中对空值进行显示的判断

```
{
  "drop": {
    "if": "ctx.network?.name != null && ctx.network.name.contains('Guest')"
  }
}
```



## 复杂条件

在if条件下，ctx的值是只读的。

一个复杂条件

```
PUT _ingest/pipeline/not_prod_dropper
{
  "processors": [
    {
      "drop": {
        "if": "Collection tags = ctx.tags;if(tags != null){for (String tag : tags) {if (tag.toLowerCase().contains('prod')) { return false;}}} return true;"
      }
    }
  ]
}
```

因为JSON不支持新行字符，所以条件符需要全部在一行上。但是，Kibana的控制台支持三引号语法，以帮助编写和调试这样的脚本。

```
PUT _ingest/pipeline/not_prod_dropper
{
  "processors": [
    {
      "drop": {
        "if": """
            Collection tags = ctx.tags;
            if(tags != null){
              for (String tag : tags) {
                  if (tag.toLowerCase().contains('prod')) {
                      return false;
                  }
              }
            }
            return true;
        """
      }
    }
  ]
}
```

插入文档

```
POST test/_doc/1?pipeline=not_prod_dropper
{
  "tags": ["application:myapp", "env:Stage"]
}
```

由于在标记中没有找到prod(不区分大小写)，因此文档被删除。

由于prod(大小写不敏感)被发现在标签中，下面的文档被索引(即没有被删除)。

```
POST test/_doc/2?pipeline=not_prod_dropper
{
  "tags": ["application:myapp", "env:Production"]
}
```

可以使用带有verbose的模拟管道API来帮助构建复杂的条件。如果条件的计算结果为false，那么它将从模拟的详细结果中被省略，因为文档不会改变。

应该注意避免过于复杂或昂贵的条件检查，因为每个文档都需要检查条件。



## 处理器中的条件处理

if条件处理器和管道处理器的组合可以产生处理异类输入的简单而强大的方法。例如，可以定义单个管道，根据某些标准委托给其他管道。

```
PUT _ingest/pipeline/logs_pipeline
{
  "description": "A pipeline of pipelines for log files",
  "version": 1,
  "processors": [
    {
      "pipeline": {
        "if": "ctx.service?.name == 'apache_httpd'",
        "name": "httpd_pipeline"
      }
    },
    {
      "pipeline": {
        "if": "ctx.service?.name == 'syslog'",
        "name": "syslog_pipeline"
      }
    },
    {
      "fail": {
        "message": "This pipeline requires service.name to be either `syslog` or `apache_httpd`"
      }
    }
  ]
}
```

上面的示例允许使用者为所有基于日志的索引请求指向单个管道。根据条件，将调用正确的管道来处理该类型的数据。

对于索引映射模板中定义的用于保存需要索引前处理的数据的所有索引的默认管道，此模式非常适用。



## 正则表达式中的条件

需要在`elasticsearch.yml`设置：

```
script.painless.regex.enabled: true
```

示例

```
PUT _ingest/pipeline/check_url
{
  "processors": [
    {
      "set": {
        "if": "ctx.href?.url =~ /^http[^s]/",
        "field": "href.insecure",
        "value": true
      }
    }
  ]
}
```

插入数据：

```
POST test/_doc/1?pipeline=check_url
{
  "href": {
    "url": "http://www.elastic.co/"
  }
}
```

正则表达式开销很大，如果存在可行的替代方案，应该避免使用正则表达式。

例如，在这种情况下startsWith可以用来得到相同的结果，而不使用正则表达式:

```
PUT _ingest/pipeline/check_url
{
  "processors": [
    {
      "set": {
        "if": "ctx.href?.url != null && ctx.href.url.startsWith('http://')",
        "field": "href.insecure",
        "value": true
      }
    }
  ]
}
```



## 处理管道中的失败



```
{
  "description" : "my first pipeline with handled exceptions",
  "processors" : [
    {
      "rename" : {
        "field" : "foo",
        "target_field" : "bar",
        "on_failure" : [
          {
            "set" : {
              "field" : "error",
              "value" : "field \"foo\" does not exist, cannot rename to \"bar\""
            }
          }
        ]
      }
    }
  ]
}
```

下面的示例在整个管道上定义了一个on_failure块，用于更改将失败文档发送到的索引。

```
{
  "description" : "my first pipeline with handled exceptions",
  "processors" : [ ... ],
  "on_failure" : [
    {
      "set" : {
        "field" : "_index",
        "value" : "failed-{{ _index }}"
      }
    }
  ]
}
```

除了定义处理器故障时的行为之外，还可以忽略一个故障并通过指定ignore_failure设置继续处理下一个处理器。

在下面的示例中，如果字段foo不存在，则失败将被捕获，管道将继续执行，在本例中，这意味着管道不执行任何操作。

```
{
  "description" : "my first pipeline with handled exceptions",
  "processors" : [
    {
      "rename" : {
        "field" : "foo",
        "target_field" : "bar",
        "ignore_failure" : true
      }
    }
  ]
}
```

您可能想要检索由失败的处理器抛出的实际错误消息。为此，您可以访问名为on_failure_message、on_failure_processor_type和on_failure_processor_tag的元数据字段。这些字段只能从on_failure块的上下文中访问。

下面是您前面看到的示例的更新版本。但是，本示例没有手动设置错误消息，而是利用on_failure_message元数据字段提供错误消息。

```
{
  "description" : "my first pipeline with handled exceptions",
  "processors" : [
    {
      "rename" : {
        "field" : "foo",
        "to" : "bar",
        "on_failure" : [
          {
            "set" : {
              "field" : "error",
              "value" : "{{ _ingest.on_failure_message }}"
            }
          }
        ]
      }
    }
  ]
}
```



## 处理器列表

### 通用参数

field

value

if

on_failure

ignore_failure

tag



### Append Processor



 如果字段已经存在且是数组，则向现有数组追加一个或多个值。将标量转换为数组，并将一个或多个值附加到该字段，如果该字段存在且该字段是标量。如果字段不存在，则创建包含所提供值的数组。接受一个值或一个值数组。

```
{
  "append": {
    "field": "tags",
    "value": ["production", "{{app}}", "{{owner}}"]
  }
}
```

### Bytes Processor

 将人类可读字节值(如1kb)转换为其字节值(如1024)。支持的人类可读单位是“b”，“kb”，“mb”，“gb”，“tb”，“pb”大小写不敏感。如果字段的格式不受支持，或者结果值超过2^63，就会发生错误。

```
{
  "bytes": {
    "field": "file.size"
  }
}
```

### Convert Processor

 将当前摄取的文档中的字段转换为另一种类型，例如将字符串转换为整数。如果字段值是数组，则所有成员都将被转换。

支持的类型包括:integer、long、float、double、string、boolean和auto。

指定auto将尝试将字符串值字段转换为最近的非字符串类型。



特有参数：

target_field

type

ignore_missing：如果设置为true并且field不存在，或者为null，处理器会悄悄地退出，而不修改文档



### Date Processor

 从字段解析日期，然后使用日期或时间戳作为文档的时间戳。默认情况下，日期处理器将解析后的日期添加为一个名为@timestamp的新字段。您可以通过设置target_field配置参数来指定一个不同的字段。同一日期处理器定义支持多种日期格式。它们将被依次用于尝试解析日期字段，其顺序与它们作为处理器定义的一部分所定义的顺序相同。



特有参数：

target_field

formats

timezone

locale



```
{
  "description" : "...",
  "processors" : [
    {
      "date" : {
        "field" : "initial_date",
        "target_field" : "timestamp",
        "formats" : ["dd/MM/yyyy hh:mm:ss"],
        "timezone" : "Europe/Amsterdam"
      }
    }
  ]
}
```

模板：

```
{
  "description" : "...",
  "processors" : [
    {
      "date" : {
        "field" : "initial_date",
        "target_field" : "timestamp",
        "formats" : ["ISO8601"],
        "timezone" : "{{my_timezone}}",
        "locale" : "{{my_locale}}"
      }
    }
  ]
}
```

### Date Index Name Processor

 该处理器的目的是通过使用date math索引名称支持，将文档指向基于文档中的日期或时间戳字段的基于时间的索引。

处理器使用基于提供的索引名前缀的日期数学索引名表达式、正在处理的文档中的日期或时间戳字段和提供的日期舍入设置_index元字段。

首先，该处理器从正在处理的文档的字段中获取日期或时间戳。日期格式可以根据字段的值应该如何解析为日期来配置。然后将这个日期、提供的索引名前缀和提供的日期舍入格式化为一个日期数学索引名表达式。这里还可以根据如何将日期格式化为日期数学索引名称表达式来指定可选的日期格式。



特有参数：

index_name_prefix

date_rounding：在将日期格式化为索引名时，如何四舍五入。有效值是:y(年)、M(月)、w(周)、d(日)、h(小时)、M(分钟)和s(秒)。支持模板片段。

date_formats

timezone

locale

index_name_format

```
PUT _ingest/pipeline/monthlyindex
{
  "description": "monthly date-time index naming",
  "processors" : [
    {
      "date_index_name" : {
        "field" : "date1",
        "index_name_prefix" : "myindex-",
        "date_rounding" : "M"
      }
    }
  ]
}
```

### Dissect Processor

 与Grok处理器类似，dissect也从文档中的单个文本字段中提取结构化字段。然而，与Grok处理器不同，dissect不使用正则表达式。这使得dissect的语法更加简单，并且在某些情况下比Grok处理器更快。

模式：

```
%{clientip} %{ident} %{auth} [%{@timestamp}] \"%{verb} %{request} HTTP/%{httpversion}\" %{status} %{size}
```

匹配：

```
1.2.3.4 - - [30/Apr/1998:22:00:52 +0000] \"GET /english/venues/cities/images/montpellier/18.gif HTTP/1.0\" 200 3171
```



特有参数

pattern

append_separator



```
{
  "dissect": {
    "field": "message",
    "pattern" : "%{clientip} %{ident} %{auth} [%{@timestamp}] \"%{verb} %{request} HTTP/%{httpversion}\" %{status} %{size}"
   }
}
```



### Drop Processor

删除文档而不引发任何错误。这有助于阻止基于某些条件对文档建立的索引。

```
{
  "drop": {
    "if" : "ctx.network_name == 'Guest'"
  }
}
```



### Dot Expander Processor

该处理器允许管道中的其他处理器访问名称中带有点的字段。否则，任何处理器都无法访问这些字段。

特有参数：

path

```
{
  "dot_expander": {
    "field": "foo.bar"
  }
}
```

### Fail Processor

当您希望管道失败并希望将特定消息转发给请求者时，这将非常有用。

特有参数：

message

```
{
  "fail": {
    "if" : "ctx.tags.contains('production') != true",
    "message": "The production tag is not present, found tags: {{tags}}"
  }
}
```

### Foreach Processor

处理数组中未知长度的元素。

特有参数：

processor



```
{
  "values" : ["foo", "bar", "baz"]
}
```

处理：

```
{
  "foreach" : {
    "field" : "values",
    "processor" : {
      "uppercase" : {
        "field" : "_ingest._value"
      }
    }
  }
}
```

### Grok Processor

从文档中的单个文本字段中提取结构化字段。您可以选择从哪个字段提取匹配的字段，以及希望匹配的grok模式。grok模式类似于正则表达式，它支持可重用的别名表达式。

特有参数：

patterns

pattern_definitions

trace_match

待匹配数据：

```
{
  "message": "55.3.244.1 GET /index.html 15824 0.043"
}
```

处理：

```
{
  "description" : "...",
  "processors": [
    {
      "grok": {
        "field": "message",
        "patterns": ["%{IP:client} %{WORD:method} %{URIPATHPARAM:request} %{NUMBER:bytes} %{NUMBER:duration}"]
      }
    }
  ]
}
```



配置：

ingest.grok.watchdog.interval 

ingest.grok.watchdog.max_execution_time



### Gsub Processor

通过应用正则表达式和替换项转换字符串字段。如果字段不是字符串，处理器将抛出异常。



特有参数：

pattern

replacement

target_field

```
{
  "gsub": {
    "field": "field1",
    "pattern": "\.",
    "replacement": "-"
  }
}
```





### Join Processor

使用分隔符将数组中的每个元素连接为单个字符串。当字段不是数组时，抛出错误。



特有参数：

separator



```
{
  "join": {
    "field": "joined_array_field",
    "separator": "-"
  }
}
```





### JSON Processor

将JSON字符串转换为结构化JSON对



特有参数：

target_field

add_to_root

源文档：

```
{
  "string_source": "{\"foo\": 2000}"
}
```

转换后文档：

```
{
  "string_source": "{\"foo\": 2000}",
  "json_target": {
    "foo": 2000
  }
}
```





### KV Processor

这个处理器帮助自动解析foo=bar类型的消息(或特定事件字段)。

特有参数：

field_split

value_split

target_field

include_keys

exclude_keys

prefix

trim_key

trim_value

strip_brackets

```
{
  "kv": {
    "field": "message",
    "field_split": " ",
    "value_split": "="
  }
}
```





### Lowercase Processor

将字符串转换为其等效小写字母

```
{
  "lowercase": {
    "field": "foo"
  }
}
```



### Pipeline Processor

执行另一个管道。

```
{
  "pipeline": {
    "name": "inner-pipeline"
  }
}
```







### Remove Processor

删除现有字段。如果一个字段不存在，将抛出异常。

```
{
  "remove": {
    "field": "user_agent"
  }
}
```





### Rename Processor

重命名现有字段。如果字段不存在或已经使用了新名称，则会抛出异常。

```
{
  "rename": {
    "field": "provider",
    "target_field": "cloud.provider"
  }
}
```



### Script Processor

允许内联脚本和存储脚本在摄取管道内执行。



### Set Processor

设置一个字段并将其与指定的值关联。如果该字段已经存在，则其值将被替换为所提供的值。

特有参数：

override

```
{
  "set": {
    "field": "host.os.name",
    "value": "{{os}}"
  }
}
```



### Set Security User Processor

通过对摄入进行预处理，将用户相关的详细信息(如用户名、角色、电子邮件、full_name和元数据)从当前经过身份验证的用户设置到当前文档。

特有参数：

properties

```
{
  "processors" : [
    {
      "set_security_user": {
        "field": "user"
      }
    }
  ]
}
```



### Split Processor

使用分隔符将字段分割为数组。只对字符串字段有效。

特有参数：

separator

target_field

```
{
  "split": {
    "field": "my_field",
    "separator": "\\s+" 
  }
}
```

### Sort Processor

按升序或降序对数组中的元素进行排序。同构的数字数组将按数字排序，而字符串数组或异构的字符串+数字数组将按字典排序。当字段不是数组时，抛出错误。

特有参数：

order

```
{
  "sort": {
    "field": "array_field_to_sort",
    "order": "desc"
  }
}
```

### Trim Processor

删除字段中的空格。

```
{
  "trim": {
    "field": "foo"
  }
}
```



### Uppercase Processor

将字符串转换为等效的大写字符串。

```
{
  "uppercase": {
    "field": "foo"
  }
}
```



### URL Decode Processor

URL-decodes字符串

```
{
  "urldecode": {
    "field": "my_url_to_decode"
  }
}
```



## 参考

https://www.elastic.co/guide/en/elasticsearch/reference/current/ingest.html