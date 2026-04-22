# Phase 1: Hadoop Optimization for Deep Learning Ingestion

To successfully transition to a CNN-based architecture, we must process massive multidimensional tensors. Optimizing the underlying Hadoop Distributed File System (HDFS) is critical to feed data into PySpark and PyTorch efficiently.

## 1. Hadoop Parallelism (128MB Block Sizing)

### The Configuration
You must edit your Hadoop `hdfs-site.xml` file (typically located in `%HADOOP_HOME%\etc\hadoop\hdfs-site.xml` on Windows) to explicitly define the block size.

```xml
<configuration>
    <!-- Set default block size to 128MB (134217728 bytes) -->
    <property>
        <name>dfs.blocksize</name>
        <value>134217728</value>
    </property>
</configuration>
```

### Technical Justification for Spark
When Spark reads data from HDFS, its RDD (Resilient Distributed Dataset) partitions are directly derived from the HDFS blocks. 
- A 1.2GB PGN file chunked into 128MB blocks results in exactly **10 partitions** ($1200 / 128 \approx 9.3$).
- This perfectly aligns with PySpark's parallel task scheduling. When an executor requests data, Spark spawns exactly one task per 128MB block. This prevents **Memory Overhead** (which happens if blocks are too large, e.g., 512MB) and **Task Scheduling Latency** (which happens if blocks are too small, e.g., 32MB, creating too many tiny tasks).

## 2. Data Locality (Replication Factor 3)

### The Configuration
In the same `hdfs-site.xml`, configure the replication factor:

```xml
<configuration>
    <!-- ... blocksize config ... -->
    
    <!-- Set replication factor to 3 -->
    <property>
        <name>dfs.replication</name>
        <value>3</value>
    </property>
</configuration>
```

*(Note: On a single-node pseudo-distributed setup for a laptop, setting replication to 1 is standard, but for a true production cluster, 3 is mandatory).*

### Technical Justification for Spark & CNNs
**Data Locality** is the principle of moving the computation to the data, rather than moving the data to the computation.
- When generating massive $8 \times 8 \times 12$ tensors, network bandwidth becomes the primary bottleneck.
- By replicating every 128MB block across 3 different DataNodes, the Spark Resource Manager (YARN) has a 3x higher probability of assigning a computation task to a Node that **already holds that specific block on its local hard drive**.
- This completely bypasses the network layer. PySpark reads the tensor data from the local disk at maximum I/O speed, drastically reducing the time required to feed the PyTorch DataLoader during CNN training.
