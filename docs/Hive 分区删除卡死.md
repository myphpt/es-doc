## 现象

Hiveserver2 Web界面显示删除分区语句长时间执行卡死的情况



报错

```
2021-10-08 18:52:35,755 ERROR ZooKeeperHiveLockManager: [HiveServer2-Background-Pool: Thread-680621]: Unable to acquire IMPLICIT, EXCLUSIVE lock protocol@http@ts_day=2021-09-23/ts_hour=02 after 100 attempts.
2021-10-08 18:52:35,764 ERROR org.apache.hadoop.hive.ql.Driver: [HiveServer2-Background-Pool: Thread-680621]: FAILED: Error in acquiring locks: Locks on the underlying objects cannot be acquired. retry after some time
org.apache.hadoop.hive.ql.lockmgr.LockException: Locks on the underlying objects cannot be acquired. retry after some time
        at org.apache.hadoop.hive.ql.lockmgr.DummyTxnManager.acquireLocks(DummyTxnManager.java:190)
        at org.apache.hadoop.hive.ql.Driver.acquireLocksAndOpenTxn(Driver.java:1244)
        at org.apache.hadoop.hive.ql.Driver.runInternal(Driver.java:1557)
        at org.apache.hadoop.hive.ql.Driver.run(Driver.java:1339)
        at org.apache.hadoop.hive.ql.Driver.run(Driver.java:1334)
        at org.apache.hive.service.cli.operation.SQLOperation.runQuery(SQLOperation.java:256)
        at org.apache.hive.service.cli.operation.SQLOperation.access$600(SQLOperation.java:92)
        at org.apache.hive.service.cli.operation.SQLOperation$BackgroundWork$1.run(SQLOperation.java:345)
        at java.security.AccessController.doPrivileged(Native Method)
        at javax.security.auth.Subject.doAs(Subject.java:422)
        at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1875)
        at org.apache.hive.service.cli.operation.SQLOperation$BackgroundWork.run(SQLOperation.java:357)
        at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
        at java.util.concurrent.FutureTask.run(FutureTask.java:266)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
        at java.lang.Thread.run(Thread.java:748)

```

Hive中该表的分区持有锁，其他操作无法再对该分区进行操作，造成提交的删除分区的SQL任务卡死



原因

1、`hiveserver2`连接过于频繁

2、已有其他操作持有锁



查看锁

```
show locks protocol.http PARTITION(ts_day='2021-10-09',ts_hour='14');

输出信息：
protocol@http@ts_day=2021-10-09/ts_hour=14	SHARED
```



查看锁的具体信息

```
show locks protocol.http PARTITION(ts_day='2021-10-09',ts_hour='14') extended;

输出信息：
protocol@http@ts_day=2021-10-09/ts_hour=14	SHARED
LOCK_QUERYID:root_20211015142314_e292ad61-1bd4-48c9-9c64-932420185742	 
LOCK_TIME:1634278995066	 
LOCK_MODE:IMPLICIT	 
LOCK_QUERYSTRING:select count(*) from  protocol.http where ts_day="2021-10-09" and ts_hour="14"	 
```

解锁表

```
unlock table protocol.http PARTITION(ts_day="2021-10-09",ts_hour="14");
```



总结

当Hive某个分区正在进行查询操作时，无法进行分区的删除操作



冷数据删除问题已记录wiki

https://wiki.tophant.com/pages/viewpage.action?pageId=62861020