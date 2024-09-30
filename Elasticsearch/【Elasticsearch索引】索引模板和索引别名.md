# 索引模板

索引模板包括设置和映射以及一个简单的模式，控制是否应将模板应用于新索引。当创建新索引时，自动应用符合条件的索引模板。

模板仅在创建索引时应用。更改模板对现有索引没有影响。当使用create index API时，在create index调用中定义的设置/映射将优先于模板中定义的任何匹配设置/映射。

> Tips：create索引的操作将优先于模板先执行。



## 使用场景

场景1：数据量非常大，需要进行索引生命周期管理，按日期划分索引，要求多个索引的Mapping一致，每次手动创建或者脚本创建都很麻烦

场景2：实际业务多个索引，想让多个索引中的相同名字的字段类型完全一致，以便实现跨索引检索。

## 一般格式

```
PUT /_template/template_1
{
    "index_patterns" : ["*"],
    "order" : 0,
    "settings" : {},
    "mappings":{},
    "aliases":{}
}
```

索引模板提供C风格的 /* */块注释。在JSON文档中，除了第一个大括号之前，任何地方都允许注释。

定义一个名为template_1的模板，模板模式为te*或bar*。设置和映射将应用于任何匹配te*或bar*模式的索引名。

## 模板列表

templates命令提供关于现有模板的信息。

```
GET /_cat/templates?v
```



## 获取模板

```
//获取模板列表
GET /_template

GET /_template/template_1
GET /_template/temp*
GET /_template/template_1,template_2
```



## 创建模板

```
PUT _template/template_1
{
  "index_patterns": ["te*", "bar*"],
  "settings": {
    "number_of_shards": 1
  },
  "mappings": {
    "_doc": {
      "_source": {
        "enabled": false
      },
      "properties": {
        "host_name": {
          "type": "keyword"
        },
        "created_at": {
          "type": "date",
          "format": "EEE MMM dd HH:mm:ss Z YYYY"
        }
      }
    }
  }
}
```



## 修改模板

执行执行创建模板的操作，会自动进行覆盖。新模板只对新创建的索引生效，对历史索引不起作用。



## 删除模板

```
DELETE /_template/template_1
```



## 模板是否存在

```
HEAD _template/template_1
```



## 模板优先级

```
order
若同一个索引可应用于多个模板，根据order值确定配置应用顺序。order高会覆盖order低的模板。
```



## 模板版本

模板可以选择添加一个版本号，版本号可以是任意的整数值，以简化外部系统对模板的管理。版本字段是完全可选的，它仅用于模板的外部管理。要取消版本设置，只需替换模板而不用指定一个。

```
PUT /_template/template_1
{
    "index_patterns" : ["*"],
    "order" : 0,
    "settings" : {
        "number_of_shards" : 1
    },
    "version": 123
}
```

要检查版本，您可以使用filter_path来过滤响应，以限制响应的版本:

```
GET /_template/template_1?filter_path=*.version

//响应：
{
  "template_1" : {
    "version" : 123
  }
}
```




## 模板与别名

```
curl -X PUT "localhost:9200/_template/template_1?pretty" -H 'Content-Type: application/json' -d'
{
    "index_patterns" : ["te*"],
    "settings" : {
        "number_of_shards" : 1
    },
    "aliases" : {
        "alias1" : {},
        "alias2" : {
            "filter" : {
                "term" : {"user" : "kimchy" }
            },
            "routing" : "kimchy"
        },
        "{index}-alias" : {}   //在创建索引期间，别名中的{index}占位符将被模板应用到的实际索引名替换。
    }
}'
```

## 动态模板（7.9版本）

修改动态Mapping：将默认的long改成integer，date_*开头的字段匹配为date类型。

```
PUT _template/sample_dynamic_template
{
  "index_patterns": [
    "sample*"
  ],
  "mappings": {
    "dynamic_templates": [
      {
        "handle_integers": {
          "match_mapping_type": "long",
          "mapping": {
            "type": "integer"
          }
        }
      },
      {
        "handle_date": {
          "match": "date_*",
          "unmatch": "*_text",
          "mapping": {
            "type": "date"
          }
        }
      }
    ]
  }
}
```

- index_patterns：对应待匹配的以”sample开头的“索引。
- handle_integers：动态模板的名字，你可以自己定义。
- match_mapping_type：被匹配的被重写的源数据类型。
- match/unmatch：匹配字段类型。


## 相关配置

```
    "settings": {
        "index": {
          "refresh_interval": "10s",//每10秒刷新
          "number_of_shards" : "5",//主分片数量
          "number_of_replicas" : "2",//副本数量
          "translog": {
            "flush_threshold_size": "1gb",//内容容量到达1gb异步刷新
            "sync_interval": "30s",//间隔30s异步刷新（设置后无法更改）
            "durability": "async"//异步刷新
          }
        }
      }
```



# 索引别名

1、允许将索引与别名混叠，所有API都会自动将别名转换为实际的索引名称。

2、别名可以映射到多个索引，在指定它时，别名将自动扩展到别名索引。

3、别名可以与筛选器相关联，该筛选器将在搜索和路由值时自动应用

4、别名不能与索引具有相同的名称。

相当于数据库中的视图，相当于Linux中的软连接



## 查询

查询别名列表

```
GET /_cat/aliases?v
```

查询别名下的所有索引

```
GET /_alias/<alias_name> 
```

查询索引的别名

```
GET /{index}/_alias/{alias}
GET /logs_20162801/_alias/*
```

检查别名是否存在

```
HEAD /_alias/2016
HEAD /_alias/20*
HEAD /logs_20162801/_alias/*
```



## 创建

创建索引别名

```
POST /_aliases
{
  "actions": [
    {
      "add": {
        "index": "data",
        "alias": "alias1"
      }
    }
  ]
}
```

创建映射多个索引的别名

```
POST /_aliases
{
    "actions" : [
        { "add" : { "index" : "test1", "alias" : "alias1" } },
        { "add" : { "index" : "test2", "alias" : "alias1" } }
    ]
}

或者
POST /_aliases
{
    "actions" : [
        { "add" : { "indices" : ["test1", "test2"], "alias" : "alias1" } }
    ]
}

或者
POST /_aliases
{
    "actions" : [
        { "add" : { "index" : "test*", "alias" : "all_test_indices" } }
    ]
}
```

包含过滤条件的别名

类似于数据库的视图

```
//创建一个索引
PUT /test1
{
  "mappings": {
    "_doc": {
      "properties": {
        "user" : {
          "type": "keyword"
        }
      }
    }
  }
}

//创建一个别名
POST /_aliases
{
    "actions" : [
        {
            "add" : {
                 "index" : "test1",
                 "alias" : "alias2",
                 "filter" : { "term" : { "user" : "kimchy" } }
            }
        }
    ]
}
```

包含路由的别名

```
POST /_aliases
{
    "actions" : [
        {
            "add" : {
                 "index" : "test",
                 "alias" : "alias1",
                 "routing" : "1"
            }
        }
    ]
}

或者

POST /_aliases
{
    "actions" : [
        {
            "add" : {
                 "index" : "test",
                 "alias" : "alias2",
                 "search_routing" : "1,2",
                 "index_routing" : "2"
            }
        }
    ]
}
```



创建索引的时候添加别名

```
PUT /logs_20162801
{
    "mappings" : {
        "_doc" : {
            "properties" : {
                "year" : {"type" : "integer"}
            }
        }
    },
    "aliases" : {
        "current_day" : {},
        "2016" : {
            "filter" : {
                "term" : {"year" : 2016 }
            }
        }
    }
}

```



## 别名关系

切换别名关系

在相同的API中，重命名别名是一个简单的删除然后添加操作。这个操作是原子的，不用担心短时间内别名没有指向索引:

```
POST /_aliases
{
    "actions" : [
        { "remove" : { "index" : "test1", "alias" : "alias1" } },
        { "add" : { "index" : "test2", "alias" : "alias1" } }
    ]
}

```



剔除错误的别名关系

```
PUT test     
PUT test_2   
POST /_aliases
{
    "actions" : [
        { "add":  { "index": "test_2", "alias": "test" } },
        { "remove_index": { "index": "test" } }  
    ]
}

```



## 添加索引别名（PUT）

```
PUT /<index_name>/_alias/<alias_name> 

参数：
index_name：支持 * | _all | glob pattern | name1, name2
routing 
filter 

```



## 删除

删除索引别名

```
POST /_aliases
{
  "actions": [
    {
      "remove": {
        "index": "data",
        "alias": "alias1"
      }
    }
  ]
}

```



删除别名（DELETE）

```
DELETE /{index}/_alias/{name}

参数：
index   * | _all | glob pattern | name1, name2, … 
name    * | _all | glob pattern | name1, name2, … 

```

举个栗子

```
DELETE /logs_20162801/_alias/current_day

```

带参数的别名搜索

如果使用路由别名的搜索操作也具有路由参数，则使用该参数中指定的搜索别名路由和路由的交集。例如，下面的命令将使用“2”作为路由值:

```
GET /alias2/_search?q=user:kimchy&routing=2,3
```



## 写索引

可以将别名指向的索引关联为写索引。当指定时，针对指向多个索引的别名的所有索引和更新请求将尝试解析为一个索引，即写索引。每次只能为每个别名分配一个索引作为写索引。如果没有指定写索引，并且别名引用了多个索引，那么就不允许写。

```
POST /_aliases
{
    "actions" : [
        {
            "add" : {
                 "index" : "test",
                 "alias" : "alias1",
                 "is_write_index" : true
            }
        }
    ]
}
```

没有显式地为索引设置is_write_index: true且只引用一个索引的别名，将使所引用的索引表现为写索引，直到引用了另一个索引为止。此时，将没有写索引，写操作将被拒绝。

**注意**：操作失败，没有is_write_index这个参数