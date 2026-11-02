# PolarDB-X 企业版原生 CCL

使用前确认产品系列与 CN 版本。官方文档将普通 CCL 的最低版本列为
`5.4.9-16167266`，慢 SQL 限流触发器为 `5.4.11-16251897`。
标准版采用不同的能力与语法，不能直接套用本页。

## 重要语义

- 这是执行并发约束，不是每秒请求数。限额按 CN 生效，需考虑节点数和流量倾斜。
- 匹配包含库表、数据库账号、SQL 类型和可选模板/关键词。各项共同决定范围。
- 模板来自真实 `sql_code` 或经验证的模板编号，不自行哈希 SQL，也不混用 DAS SQL ID。
- 等待请求仍占资源。明确配置队列与超时；`MAX_CONCURRENCY=0` 可能拒绝全部匹配请求，不能作为自动默认值。
- 规则查询中的 `KILLED` 表示 CCL 拒绝计数，不能据此声称执行了 kill 会话命令。
- 删除规则可能释放等待请求；配置消失不等于业务已恢复。

## 查询、创建、解除

以下是 SQL 语法示例，不是可直接运行的生产配置。先根据已核实证据替换标识符、账号和参数，通过授权 SQL 工具单条执行。

```sql
SHOW CCL_RULES;
```

```sql
CREATE CCL_RULE `agent_ccl_example`
ON `example_db`.`example_table`
TO 'example_user'@'%'
FOR SELECT
FILTER BY TEMPLATE('9037e5e2')
WITH MAX_CONCURRENCY=2, WAIT_QUEUE_SIZE=0, WAIT_TIMEOUT=1;
```

示例中的 `%` 表示账号来源范围，不能未经核实扩大 Host 范围。
多表模板必须按目标版本实际匹配语义确认覆盖；不能随意选一张表。
不在 shell 双引号中直接拼接含反引号的 SQL。

关键词过滤示例，针对 `SELECT example_column FROM example_table` 的词序（与上面的模板规则是两种独立示例）：

```sql
CREATE CCL_RULE `example_keyword_rule`
ON `example_db`.`example_table`
TO 'example_user'@'%'
FOR SELECT
FILTER BY KEYWORD('example_column', 'example_table')
WITH MAX_CONCURRENCY=2, WAIT_QUEUE_SIZE=0, WAIT_TIMEOUT=1;
```

官方文档概括为参数值区分大小写、其他词不区分大小写；本次实测发现反引号标识符例外，不能将这句话当作所有标识符的保证。关键词也不是无序集合或任意正则表达式；按下节的版本限定证据检查词序和大小写。
模板编号可从 SQL 日志的 `sql_code`、`SHOW FULL PROCESSLIST` 或 `EXPLAIN`
取得并核验。原生规则支持 SELECT/INSERT/UPDATE/DELETE，每条指定一种类型；
DAS 创建入口的类型范围与原生 SQL 不相同。

## Matching boundaries tested 2026-10-21

Evidence scope: PolarDB-X Zero Enterprise Edition, build `5.7.25-TDDL-5.4.21-20260701`, two CNs. These are observations from one tested build, not compatibility guarantees for other versions or for a DAS keyword-generation interface. The tests used a zero-concurrency rule to make matching observable as rejection; this is not a recommended emergency default.

| Boundary | Observed evidence | Rule-authoring consequence |
|---|---|---|
| Keyword order | `SELECT marker FROM ccl_probe WHERE id=1` was rejected by `KEYWORD('marker','ccl_probe')` but passed with the reversed list. The ordered rule recorded three hits in the five-query matrix; the reversed rule recorded zero. | Preserve SQL token order; merely including all tokens is insufficient. |
| Quoted identifier case | Keyword `marker` matched unquoted `MaRkEr` and quoted `` `marker` ``, but not quoted `` `MaRkEr` ``. The distinction remained with wildcard table scope and `FAST_MATCH=0`. | Preserve quoting and case in coverage samples; do not describe all non-value tokens as case-insensitive. |
| Exact table scope | With `ON ...ccl_probe`, the lower-case table reference was rejected while `FROM CCL_PROBE` succeeded. With wildcard table scope and `FAST_MATCH=0`, both table spellings were rejected by the keyword rule. | Table-scope comparison and keyword comparison are separate filters. Do not infer CCL table matching from successful SQL name resolution. |

A separate no-cache result record also shows the exact-table case distinction and reversed-keyword non-match. That record includes query outcomes but not the CREATE statement or rule read-back; therefore it does not independently prove the `FAST_MATCH=0` configuration. The wildcard/no-cache matrix does include its CREATE statement. Disabling the cache is not an established fix for the table-scope issue.

Review actual SQL spellings, quoted/unquoted variants, and an unrelated control query before claiming coverage. If exact scope misses a variant, report the coverage gap rather than silently replacing it with a wildcard. A template filter still has to satisfy the same table/account scope.

The raw evidence was reviewed from `run-v2.log`, `run-focused.log`, `results-nocache.json`, and their available test scripts on 2026-10-21. Some focused matrix entries log a constant success flag; conclusions above come from the recorded SQL responses and rule counters. The core run's count expectation included a query that did not match, and its empty-list assertion reported failure despite an empty result; these flags alone are not evidence of a counter or cleanup defect.

## 并发、等待与拒绝

| 参数 | 语义 |
|---|---|
| `MAX_CONCURRENCY` | 每 CN 允许的匹配执行并发；显式设置，默认 0 可能使全部匹配请求报错 |
| `WAIT_QUEUE_SIZE` | 每 CN 等待队列容量，默认 0；等待仍占线程 |
| `WAIT_TIMEOUT` | 排队最长等待秒数，默认 600；不是 SQL 执行超时，也不是规则存活时间 |
| `FAST_MATCH` | 匹配缓存开关，0 关闭、1 开启，默认 1 |

未达到并发上限时运行（RUN）；达到上限但队列有空位时等待（WAIT）；
排队超时报错（WAIT_TIMEOUT）；并发和队列都满时拒绝（KILL）。
错误码可能随版本变化，应结合错误文本和规则名判断。

例如两个 CN 各限制为 2，均匀分流时总共最多允许 4 条匹配执行；
请求都落到一个 CN 时，该节点仍只允许 2 条。不是全实例共享额度。

## 观测与解除效果

```sql
SHOW CCL_RULE `agent_ccl_example`;
```

读回定义及 `ACTIVE_NODE_COUNT`，观察 `RUNNING`、`WAITING`、`TOTAL_MATCH`、
`KILLED` 的变化。审计可辅助使用 `matched_ccl_rule`、`ccl_wait_time`（毫秒）、
`ccl_status`、`ccl_hit_cache`；缺失字段不补零。

```sql
DROP CCL_RULE IF EXISTS `agent_ccl_example`;
```

`DROP IF EXISTS` 并不能证明当前任务拥有规则；删除前必须比对记录。
`NO.` 表示匹配优先级，数字越小优先级越高，不是 DAS 的规则标识。
观测时区分当前 `RUNNING`/`WAITING` 与累计匹配/拒绝计数，用窗口增量判断命中。
删除规则会使规则失效并放行其等待请求，因此可能出现流量反弹。

`CLEAR CCL_RULES` 清空全部规则；不适合作为某一条规则的解除方式。
`SLOW_SQL_CCL GO` 是持续识别慢模板、生成规则的另一套机制，还可能终止超额慢查询；
`SLOW_SQL_CCL BACK` 关闭该机制并删除其创建的规则。它们不能与普通定向 CCL 等同。
本页解释这些能力，不自动开启或执行；应急 Skill 当前仅支持用户触发的定向规则。

## 来源

- [SQL 限流语法与语义](https://help.aliyun.com/zh/polardb/polardb-for-xscale/sql-throttling-2)
- [慢 SQL 限流实践](https://help.aliyun.com/zh/polardb/polardb-for-xscale/throttle-slow-sql-requests)

官方文档复核及补充实测记录核查日期：2026-10-21。具体版本能力以当前实例及可用工具验证为准。
