---
comments: true
---

# YAML基础

!!! note "参考资料"

    [YAML - 维基百科，自由的百科全书](https://zh.wikipedia.org/wiki/YAML)
    
    [一文看懂 YAML - 知乎](https://zhuanlan.zhihu.com/p/145173920)

## 核心基本数据结构

### 对象`Object`

!!! note

    又称**映射**`Mapping`/**字典**`Dictionary`

对象是YAML中最常用的结构，用于表示键值对的集合。也可以叫做**散列表/哈希`Hashes`**。

- **表示法**：键和值之间用冒号加空格 `:`分隔。

- **嵌套对象**：通过缩进实现层级关系。

  区块形式（常使用于YAML数据文档中）使用缩进和换行符分隔**key: value**对。

  内置形式（常使用于YAML数据流中）在大括号中使用逗号+空白字符分隔**key: value**对。

```yam title="对象"
 --- # 区块形式
   name: John Smith
   age: 33
 --- # 內置形式
 {name: John Smith, age: 33}
```

- **复杂对象**：使用**问号“?”**声明一个复杂对象，允许你使用多个词汇（数组）来组成键。

```yaml title="复杂对象"
?
  - keypart1
  - keypart2
:
  - value1
  - value2
```

### 数组`Array`

!!! note 

    又称**序列**`Sequence`/**列表**`List`

数组用于表示一系列按顺序排列的值.

- **表示法**：每个列表项以短横线加空格 `-`开头。

- **嵌套对象**：通过多级缩进和 `-`来表示多维列表。

  区块形式用短杠+空白字符作为起始。

  内置形式用方括号围住，并用逗号+空白区隔作为起始。

!!! note

    --- # 区块形式
     - Casablanca
     - North by Northwest
     - Notorious
     --- # 内置形式
     [milk, pumpkin pie, eggs, juice]

#### 清单与散列表的区别与联系

> 部分内容由`Deepseek`生成

|     特性     |          清单 (List)           |                   散列表 (Hash)                    |                          说明与联系                          |
| :----------: | :----------------------------: | :------------------------------------------------: | :----------------------------------------------------------: |
| **数据结构** |          数组 (Array)          |            映射 (Mapping) / 键值对集合             |                代表了两种不同的数据组织方式。                |
| **表示符号** |   以 `-`（短横线加空格）起始   |      以 `key: value`（冒号加空格）的形式表示       |                  这是它们最直观的语法区别。                  |
|  **有序性**  |           **有顺序**           | 通常**无顺序**（但有一些YAML实现支持保持输入顺序） | 清单中元素的顺序是重要的，散列表中键的顺序通常不重要（除非使用有序映射等高级类型）。 |
| **典型用途** |    表示一组同类项、有序列表    |            表示一个对象的属性、配置选项            |            清单用于罗列项目，散列表用于描述事物。            |
| **嵌套关系** | 清单中可以包含散列表或其他清单 |          散列表中可以包含清单或其他散列表          | **这是它们最重要的联系**，通过嵌套可以构建出任意复杂的层次化数据结构。 |

```yaml title="嵌套关系"
# 于清单中使用散列表
- {name: John Smith, age: 33}
- name: Mary Smith
  age: 27
# 于散列表中使用清单
men: [John Smith, Bill Jones]
women:
  - Mary Smith
  - Susan Williams
```

### 标量`Scalar`

标量是最基本的数据单位，代表单个不可再分的值。

#### 字符串

字符串**一般不需要用引号包裹**，但是如果字符串中使用了**特殊字符**（反斜杠“\”开头的转义字符）或**空格**就必须使用**单引号或双引号**包裹。**双引号**会对特殊字符（如 `\n`）进行**转义**，单引号则不会。

```yaml title="字符串"
strings:
  - Hello without quote # 不用引号包裹
  - Hello
   world # 拆成多行后会自动在中间添加空格
  - 'Hello with single quotes' # 单引号包裹
  - "Hello with double quotes" # 双引号包裹
  - "I am fine. \u263A" # 使用双引号包裹时支持 Unicode 编码
  - "\x0d\x0a is \r\n" # 使用双引号包裹时还支持 Hex 编码
  - 'He said: "Hello!"' # 单双引号支持嵌套
```

##### 换行语法支持

###### 保留换行

使用**竖线符“ | ”**来表示该语法，每行的缩进和行尾空白都会被去掉，而额外的缩进会被保留。

```yaml title="保留换行"
data: |
   There once was a man from Darjeeling     # 这里曾有一个人来自大吉岭
   Who got on a bus bound for Ealing        # 他搭上一班往伊灵的公车
       It said on the door                  # 门上这么说的
       "Please don't spit on the floor"     # “请勿在地上吐痰”
   So he carefully spat on the ceiling      # 所以他小心翼翼地吐在天花板上
```

###### `Chomping Final Line Break`

使用保留换行时，作为**最后一行结尾的换行**(\n)会包含在文本之内，若希望使用此缩进方式，但**不想要含有最后的换行**，可以使用`Chomping Final Line Break`。

```yaml title="Chomping Final Line Break"
data: |-
   ...
```

###### 折叠换行

使用**右尖括号“ > ”**来表示该语法，只有空白行才会被识别为换行，原来的换行符都会被转换成空格。

```yaml title="折叠换行"
data: >
   Wrapped text         # 折叠的文字
   will be folded       # 将会被收
   into a single        # 进单一个个段落
   paragraph            # 段落
   
   Blank lines denote   # 空白的行代表
   paragraph breaks     # 段落之间的区隔
```

#### 布尔值`Boolean`
!!! note

    - “true”、“True”、“TRUE”、“yes”、“Yes”和“YES”**均可**
    
    - “false”、“False”、“FALSE”、“no”、“No”和“NO”**均可**

#### 整数`Integer`

整数支持**二进制表示**。

```yaml title="整数"
int:
  - 666
  - 0001_0000 # 二进制表示
```

#### 浮点数`Floating Point`

浮点数支持**科学计数法**。

```yaml title="浮点数"
float:
  - 3.14
  - 6.8523015e+5 # 使用科学计数法
```

#### 空`NULL`

"null”、“Null”和“~”都是**空**，**不指定值**默认也是空。

#### 日期和时间`Timestamp`

日期应采用 **ISO 8601 格式**（`yyyy-MM-dd`），时间则使用 `yyyy-MM-dd T HH:mm:ss.sss±HH:mm`格式。

```yaml title="日期和时间"
date1: 2020-05-26
date2: 2020-05-26T01:00:00+08:00
dete3: 2020-05-26T02:00:00.10+08:00
date4: 2020-05-26 03:00:00.10 +8
```

#### 类型强制转换

YAML 支持使用**严格类型标签“!!”**（双感叹号+目标类型）来强制转换类型。

```yaml title="类型强制转换"
a: 123                     # 整数
b: "123"                   # 字串（使用双引号）
c: 123.0                   # 浮点数
d: !!float 123             # 浮点数，使用!!表达的严格形态
e: !!str 123               # 字串，使用严格形态
f: !!str Yes               # 字串，使用严格形态
g: Yes                     # 布尔值"真"（yaml1.1）或字串"Yes"（yaml1.2）
h: Yes we have No bananas  # 字串（包含"Yes"和"No"）
```

## 核心语法

!!! note

    YAML**大小写敏感**

### 缩进

- YAML使用**缩进**表示**层级关系**
- 缩进**只能使用空格**，不能用 TAB 字符

- **空白字符**的**数目并不是非常重要**，只要相同层次结构的元素**左侧对齐**就可以了

#### 注释

- YAML使用`#`表示注释
- YAML的`#`号可以出现在一行中的**任何位置**，而且范围只有一行（也就是一般所谓的**单行注解**）。

#### 多个文件

- YAML中一个文件中可以包含多个文件的内容
- 可用连续三个连字号（**---**）区分多个文件，还有选择性的连续三个点号（ **...** ）用来表示文件结尾（在利用流的通信中，这非常有用，可以在不关闭流的情况下，发送结束信号）。

#### 数据重用与合并

为了保持内容的简洁，避免过多重复的定义，YAML 提供了由**锚点标签**`&`和**引用标签**`*`组成的语法。重复的内容可使从参考标记星号`*`复制到锚点标记`&`。

```yaml title="数据重用与合并"
a: &anchor # 设置锚点
  one: 1
  two: 2
  three: 3
b: *anchor # 引用锚点
```

配合**合并标签**`<<`使用可以与任意数据进行合并。

```yaml title="合并标签"
- step:  &id001                  # 定义锚点标签 &id001
    instrument:      Lasik 2000
    pulseEnergy:     5.4
    pulseDuration:   12
    repetition:      1000
    spotSize:        1mm

- step:
     <<: *id001                  # 合并键值：使用在锚点标签定义的内容
     spotSize:       2mm         # 覆写"spotSize"键值
```

