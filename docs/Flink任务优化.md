## Kafka

lag延迟量



## 1、资源

CPU使用率

IO

内存





2、并发

3、数据



# BEngineJob优化记录

## 未优化前

### 禁止算子链合并

Standalone单并发：

```
{Source: KafkaSource={"numBytesOutPerSecond":{"min":8126893,"avg":8126893,"max":8126893,"sum":8126893},"numRecordsOutPerSecond":{"min":7328,"avg":7328,"max":7328,"sum":7328},"timestamp":"2023-06-09 11:18:47"}}
```

Standalone10个并发：

```
{Source: KafkaSource={"numBytesOutPerSecond":{"min":2600150,"avg":3138543,"max":3789341,"sum":31385437},"numRecordsOutPerSecond":{"min":2069,"avg":2617,"max":3244,"sum":26178},"timestamp":"2023-06-09 11:26:28"}}

```

Yarn单并发194：21000左右

Yarn10个并发194

```
timeCount=20,timeCount=100,numBytesOutPerSecondAll=2652052976,MB速率=126.46m/s,Count速率=152699/s,最大速率MB=139.77m/s,最大速率Count=170362/s
```



### 合并算子链

Yarn单并发194：32000左右





问题1：更换Yarn运行模式

问题2：Hutool的JSON解析比Jackson慢3到4倍

问题3：









# 方案

1、切换Yarn

2、修改hutoop为jackson

3、每个topic一个链路



单并发

原：20000

jackson：51000

splitUnion：32000

splitTopic：97000



原：20000  

切换jackson：51000

切分数据流：97000



## 内存问题

JVM内存分析

https://www.cnblogs.com/bolang100/p/6478537.html

https://blog.csdn.net/wangshuminjava/article/details/107608469



## 报错1

```
java.lang.OutOfMemoryError: GC overhead limit exceeded
        at java.util.Arrays.copyOf(Arrays.java:3236) ~[?:1.8.0_144]
        at java.io.ByteArrayOutputStream.grow(ByteArrayOutputStream.java:118) ~[?:1.8.0_144]
        at org.apache.flink.table.runtime.typeutils.RawValueDataSerializer.copy(RawValueDataSerializer.java:38) ~[flink-table-blink_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.table.runtime.typeutils.RowDataSerializer.copyRowData(RowDataSerializer.java:166) ~[flink-table-blink_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.table.runtime.typeutils.RowDataSerializer.copy(RowDataSerializer.java:129) ~[flink-table-blink_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.table.runtime.typeutils.RowDataSerializer.copy(RowDataSerializer.java:50) ~[flink-table-blink_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.runtime.state.heap.CopyOnWriteStateMap.get(CopyOnWriteStateMap.java:297) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.runtime.state.heap.StateTable.get(StateTable.java:251) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.runtime.state.heap.StateTable.get(StateTable.java:139) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.runtime.state.heap.HeapValueState.value(HeapValueState.java:73) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.table.runtime.operators.window.WindowOperator.processElement(WindowOperator.java:343) ~[flink-table-blink_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.streaming.runtime.tasks.OneInputStreamTask$StreamTaskNetworkOutput.emitRecord(OneInputStreamTask.java:193) ~[flink-dist_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.streaming.runtime.io.StreamTaskNetworkInput.processElement(StreamTaskNetworkInput.java:179) ~[flink-dist_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.streaming.runtime.io.StreamTaskNetworkInput.emitNext(StreamTaskNetworkInput.java:152) ~[flink-dist_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.streaming.runtime.io.StreamOneInputProcessor.processInput(StreamOneInputProcessor.java:67) ~[flink-dist_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.streaming.runtime.tasks.StreamTask.processInput(StreamTask.java:372) ~[flink-dist_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.streaming.runtime.tasks.StreamTask$$Lambda$174/139980188.runDefaultAction(Unknown Source) ~[?:?]
        at org.apache.flink.streaming.runtime.tasks.mailbox.MailboxProcessor.runMailboxLoop(MailboxProcessor.java:186) ~[flink-dist_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.streaming.runtime.tasks.StreamTask.runMailboxLoop(StreamTask.java:575) ~[flink-dist_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.streaming.runtime.tasks.StreamTask.invoke(StreamTask.java:539) ~[flink-dist_2.11-1.12.0.jar:1.12.0]
        at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:722) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.runtime.taskmanager.Task.run(Task.java:547) ~[nta-flink-task.jar:4.3.0]

```

原因

```
执行垃圾收集的时间比例太大， 有效的运算量太小，默认情况下,，如果GC花费的时间超过 98%， 并且GC回收的内存少于 2%， JVM就会抛出这个错误。
```

## 报错2

```
Caused by: java.lang.OutOfMemoryError: Java heap space
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.util.TextBuffer.carr(TextBuffer.java:886) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.util.TextBuffer.finishCurrentSegment(TextBuffer.java:740) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.json.UTF8StreamJsonParser._finishString2(UTF8StreamJsonParser.java:2461) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.json.UTF8StreamJsonParser._finishAndReturnString(UTF8StreamJsonParser.java:2437) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.json.UTF8StreamJsonParser.getText(UTF8StreamJsonParser.java:293) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.deser.std.BaseNodeDeserializer.deserializeObject(JsonNodeDeserializer.java:267) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.deser.std.JsonNodeDeserializer.deserialize(JsonNodeDeserializer.java:68) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.deser.std.JsonNodeDeserializer.deserialize(JsonNodeDeserializer.java:15) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper._readTreeAndClose(ObjectMapper.java:4254) ~[nta-flink-task.jar:4.3.0]
        at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper.readTree(ObjectMapper.java:2725) ~[nta-flink-task.jar:4.3.0]

```

原因：

```
在JVM中如果98%的时间是用于GC(Garbage Collection)且可用的 Heap size 不足2%的时候将抛出异常信息，java.lang.OutOfMemoryError: Java heap space。 

```



## 方法论

1、代码层面：JVM分析

2、背压不会导致OOM，状态和计时器才会（试解决方案RocksDB state）

3、状态设置过期时间





## 方案

1、设置状态过期时间

2、减小窗口大小

3、分离Task

4、禁止形成算子链

5、状态后端

6、增加内存



