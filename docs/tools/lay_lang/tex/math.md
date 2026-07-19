---
comments: true
---

# 数学公式基础

!!! note "主要参考资料"

    [Learn LaTeX with a tutorial](https://cn.overleaf.com/learn/latex/Learn_LaTeX_in_30_minutes)

!!! note "超好用的练习工具"

    [TeXnique](https://texnique.xyz/)

## 符号表示

### 上标与下标

#### 语法

```latex title="上标与下标"
a_{subscripts} 
b^{superscripts}
```


!!! warning "注意"

    在下标或上标只有单个字符时，大括号可以省略

#### 效果

$$
a_{subscripts} 
$$

$$
b^{superscripts}
$$

#### 练习

$$
x^{y^z}=(1+e^x)^{-2xy^w}
$$

$$
a_1^2+a_2^2=y_{ij}+y_{ji}
$$

#### 使用上下标的运算符

!!! note

    一些数学运算符可能需要上标和下标。最常见的情况是积分运算符 `\int` 和求和运算符 `\sum` ，它们的边界用上标和下标精确排版。
    
    $$
    \sum_{i=1}^{\infty} \frac{1}{n^s} 
    = \prod_p \frac{1}{1 - p^{-s}}
    $$

#### 参考

| LATEX标记             | 渲染为                |
| --------------------- | --------------------- |
| `a_{n_i}`             | $a_{n_i}$             |
| `\int_{i=1} ^n`       | $\int_{i=1} ^n$       |
| `\sum_{i=1}^{\infty}` | $\sum_{i=1}^{\infty}$ |
| `\prod_{i=1}^n`       | $\prod_{i=1}^n$       |
| `\cup_{i=1}^n`        | $\cup_{i=1}^n$        |
| `\cap_{i=1}^n`        | $\cap_{i=1}^n$        |
| `\oint_{i=1}^n`       | $\oint_{i=1}^n$       |
| `\coprod_{i=1}^n`     | $\coprod_{i=1}^n$     |

!!! note

    还有与 `cup` 和 `cap` 类似的 `bigcup` 和 `bigcap` 命令，但它们用于更大的表达式。

### 分数

#### 语法

```latex title="分数"
\frac{a}{b}
```

#### 效果

$$
\frac{a}{b}
$$

### 开方

#### 语法

```latex title="开方"
\sqrt{2} \quad \sqrt[3]{2}
```

!!! note "分隔符"

    \quad指的是分隔符
    
    \quad指的是一个分隔符，q的个数代表连续分隔符的个数
    
    如：\qquad指的是2个分隔符 \qqquad指的是3个分隔符，以此类推

#### 效果

$$
\sqrt{2} \quad \sqrt[3]{2}
$$

!!! warning "省略"

    在开平方的时候，方括号及其中的内容可以省略

### 括号

#### 语法参考

| 类型         | LATEX标记             | 渲染为                |
| ------------ | --------------------- | --------------------- |
| `圆括号`     | `(x+y)`               | $(x+y)$               |
| `方括号`     | `[x+y]`               | $[x+y]$               |
| `大括号`     | `\{x+y\}`             | $\{x+y\}$             |
| `尖括号`     | `\langle x+y \rangle` | $\langle x+y \rangle$ |
| `垂直括号`   | `|x+y|`               | \|$x+y$\|             |
| `双垂直括号` | `\|x+y\|`             | $\|x+y\|$             |
| `上取整括号` | `\lceil x+y \rceil`   | $\lceil x+y \rceil$   |
| `下取整括号` | `\lfloor x+y \rfloor` | $\lfloor x+y \rfloor$ |

#### 大括号与行标

!!! note

    使用`\left`和`\right`来创建自动匹配高度的`()`、`[]`、`{}`、`.`。在每个公式末尾使用`\tag{行标}`来实现行标。

##### 代码

```latex title="大括号与行标"
f\left(
\left[
\dfrac{1+\{x,y\}}{\left(\dfrac{x}{y}+\dfrac{y}{x}\right)(u+1)}+a
\right]
^{\dfrac{3}{2}}
\right)
\tag{行标}
```

##### 效果

$$
f\left(\left[\dfrac{1+\{x,y\}}{\left(\dfrac{x}{y}+\dfrac{y}{x}\right)(u+1)}+a\right]^{\dfrac{3}{2}}\right)\tag{行标}
$$

!!! note

    如果你想将行内显示的分隔符也变大,也可以使用`\middle`命令。

#### 示例

```latex
F = G \left( \frac{m_1 m_2}{r^2} \right)
```

$$
F = G \left( \frac{m_1 m_2}{r^2} \right)
$$

!!! warning "注意"

    要插入括号或方括号，需要使用 `\left` 和 `\right` 命令。即使只使用一个方括号，这两个命令也都是必需的。 `\left` 和 `\right` 可以动态调整大小

```latex
\left[  \frac{ N } { \left( \frac{L}{p} \right)  - (m+n) }  \right
```

$$
\left[  \frac{ N } { \left( \frac{L}{p} \right)  - (m+n) }  \right]
$$

### 运算符

#### 普通运算符

**三角函数、对数等可以通过一些特殊命令写在文档中。**

##### 示例

```latex title="三角函数"
\sin(a + b) = \sin a \cos b + \cos b \sin a
```

##### 效果

$$
\sin(a + b) = \sin a \cos b + \cos b \sin a
$$

!!! warning "注意"

    该命令将以直立（罗马）文本而不是斜体打印函数的名称。

#### 极限运算符

##### 示例

```latex title="极限运算符"
\lim_{h \to 0 } \frac{f(x+h)-f(x)}{h}
```

##### 效果

$$
\lim_{h \to 0 } \frac{f(x+h)-f(x)}{h}
$$

#### 参考

| 操作符    | 渲染为      |
| --------- | ----------- |
| `\cos`    | **cos**     |
| `\csc`    | **csc**     |
| `\exp`    | **exp**     |
| `\ker`    | **ker**     |
| `\limsup` | **lim sup** |
| `\min`    | **min**     |
| `\sinh`   | **sinh**    |
| `\arcsin` | **arcsin**  |
| `\cosh`   | **cosh**    |
| `\deg`    | **deg**     |
| `\gcd`    | **gcd**     |
| `\lg`     | **lg**      |
| `\ln`     | **ln**      |
| `\Pr`     | **Pr**      |
| `\sup`    | **sup**     |
| `\arctan` | **arctan**  |
| `\cot`    | **cot**     |
| `\det`    | **det**     |
| `\hom`    | **hom**     |
| `\lim`    | **lim**     |
| `\log`    | **log**     |
| `\sec`    | **sec**     |
| `\tan`    | **tan**     |
| `\arg`    | **arg**     |
| `\coth`   | **coth**    |
| `\dim`    | **dim**     |
| `\liminf` | **lim inf** |
| `\max`    | **max**     |
| `\sin`    | **sin**     |
| `\tanh`   | **tanh**    |

### 矢量与均值

#### 示例

```latex title="矢量与均值"
\overrightarrow{E(\vec{r})}
\quad
\overleftarrow{E(\vec{r})}
\quad
\overleftrightarrow{E(\vec{r})}
\quad
\underrightarrow{E(\vec{r})}
\quad
\underleftarrow{E(\vec{r})}
\quad
\underleftrightarrow{E(\vec{r})}
\quad
\overline{v}=\bar{v}\quad\underline{v}
```

#### 效果

$$
\overrightarrow{E(\vec{r})}
\quad
\overleftarrow{E(\vec{r})}
\quad
\overleftrightarrow{E(\vec{r})}
\quad
\underrightarrow{E(\vec{r})}
\quad
\underleftarrow{E(\vec{r})}
\quad
\underleftrightarrow{E(\vec{r})}
\quad
\overline{v}=\bar{v}\quad\underline{v}
$$

### 省略号

#### 示例

```latex title="省略号"
\cdots \quad \ldots \quad \vdots \quad \ddots
```

#### 效果

$$
\cdots \quad \ldots \quad \vdots \quad \ddots
$$

### 连分式

!!! note "说明"

    就像`\frac`一样,使用`\cfrac`或`\dfrac`来创建一个连分式,不要使用普通的`\frac`或`\over`来创建,否则看起来会**很恶心**。

#### 示例

```latex title="连分式"
x=a_0+\cfrac{1^2}{a_1+\cfrac{2^2}{a_2+\cfrac{3^2}{a_3+\cfrac{4^2}{a_4+\cdots}}}}
```

#### 效果

$$
x=a_0+\cfrac{1^2}{a_1+\cfrac{2^2}{a_2+\cfrac{3^2}{a_3+\cfrac{4^2}{a_4+\cdots}}}}
$$

#### 反例

```latex title="反例"
x=a_0+\frac{1^2}{a_1+\frac{2^2}{a_2+\frac{3^2}{a_3+\frac{4^2}{a_4+\cdots}}}}
```

##### 效果

$$
x=a_0+\frac{1^2}{a_1+\frac{2^2}{a_2+\frac{3^2}{a_3+\frac{4^2}{a_4+\cdots}}}}
$$

#### 补充

!!! note "补充"

    当然,你可以使用`\frac`来表达连分数的**紧缩记法**。

```latex title="紧缩记法"
x=a_0+\frac{1^2}{a_1+}\frac{2^2}{a_2+}\frac{3^2}{a_3+}\frac{4^2}{a_4+}\cdots
```

##### 效果

$$
x=a_0+\frac{1^2}{a_1+}\frac{2^2}{a_2+}\frac{3^2}{a_3+}\frac{4^2}{a_4+}\cdots
$$

## 积分、和与积

### 积分

#### 单次积分

##### 格式

```latex title="单次积分"
\int_{lower}^{upper}
```

##### 示例

```latex title="示例"
\int_{a}^{b} x^2 \,dx\
```

##### 效果

$$
\int_{a}^{b} x^2 \,dx\
$$

#### 多重积分

!!! note "重数"

    int中i的个数代表积分的“重数”
    
    比如，iint代表二重积分，iiint代表三重积分，以此类推

##### 示例

```latex title="多重积分"
\iint_V \mu(u,v) \,du\,dv
```

##### 效果

$$
\iint_V \mu(u,v) \,du\,dv
$$

#### 循环积分

##### 示例

```latex title="循环积分"
\oint_V f(s) \,ds
```

##### 效果

$$
\oint_V f(s) \,ds
$$

### 和

#### 格式

```latex title="和"
\sum_{lower}^{upper} 
```

#### 示例

```latex title="示例"
\sum_{n=1}^{\infty} 2^{-n} = 1
```

#### 效果

$$
\sum_{n=1}^{\infty} 2^{-n} = 1
$$

### 积

#### 格式

```latex title="格式"
\prod_{lower}^{upper}
```

#### 示例

```latex title="示例"
\prod_{i=a}^{b} f(i)
```

#### 效果

$$
\prod_{i=a}^{b} f(i)
$$

## 矩阵

### 无框矩阵

#### 示例

```latex title="无框矩阵"
\begin{matrix}
1&x&x^2\\
1&y&y^2\\
1&z&z^2\\
\end{matrix}
```

#### 效果

$$
\begin{matrix}
1&x&x^2\\
1&y&y^2\\
1&z&z^2\\
\end{matrix}
$$

### 边框矩阵

!!! note "说明"

    其实就是在开头将无框矩阵的`matrix`替换为`pmatrix`、`bmatrix`、`Bmatrix`、`vmatrix`、`Vmatrix`

| matrix                               | pmatrix                                | bmatrix                                | Bmatrix                                | vmatrix                                | Vmatrix                                |
| ------------------------------------ | -------------------------------------- | -------------------------------------- | -------------------------------------- | -------------------------------------- | -------------------------------------- |
| $\begin{matrix}1&2\\3&4\end{matrix}$ | $\begin{pmatrix}1&2\\3&4\end{pmatrix}$ | $\begin{bmatrix}1&2\\3&4\end{bmatrix}$ | $\begin{Bmatrix}1&2\\3&4\end{Bmatrix}$ | $\begin{vmatrix}1&2\\3&4\end{vmatrix}$ | $\begin{Vmatrix}1&2\\3&4\end{Vmatrix}$ |

### 带分割线的矩阵

!!! note "说明"

    可以使用`cc|c`来在一个三列矩阵中插入分割线。

#### 示例

```latex title="带分割线的矩阵"
\left[
\begin{array}{cc|c}
1&2&3\\
4&5&6
\end{array}
\right]
```

#### 效果

$$
\left[
\begin{array}{cc|c}
1&2&3\\
4&5&6
\end{array}
\right]
$$

## 方程

### 方程式

#### 对齐方程

!!! note "符号"

    **双反斜杠用作换行符。使用 `&` 符号来设置公式垂直对齐的位置。**

##### 示例

```latex title="对齐方程"
\begin{align}
S & = \frac{1}{2} \pi r^2 \\
& = \frac{\pi r^2}{2}
\end{align}
```

##### 效果

$$
\begin{align}
S & = \frac{1}{2} \pi r^2 \\
& = \frac{\pi r^2}{2}
\end{align}
$$

#### 方程式序列

!!! note "说明"

    可以使用`\begin{align}...\end{align}`来创建一列整齐且默认右对齐的方程式序列。请注意`{align}`是**自动编号**的，使用`{align*}`来声明停止自动编号，也可以使用`\notag`来取消特定行的自动编号。在需要的时候，你可以使用`\begin{equation}...\end{equation}`来强制表达式自动编号。

##### 示例与效果

=== "示例1"

    **代码**
    
    ```latex title="示例1"
    \begin{align}
    \sqrt{37}&=\sqrt{\dfrac{73^2-1}{12^2}}\\
    &=\sqrt{\dfrac{73^2}{12^2}\cdot\dfrac{73^2-1}{73^2}}\\
    &=\sqrt{\dfrac{73^2}{12^2}}\sqrt{\dfrac{73^2-1}{73^2}}\notag\\
    &=\dfrac{73}{12}\sqrt{1-\dfrac{1}{73^2}}\\
    &\approx\dfrac{73}{12}\left(1-\dfrac{1}{2\cdot73^2}\right)\label{A}
    \end{align}
    ```
    
    **效果**
    
    $$
    \begin{align}
    \sqrt{37}&=\sqrt{\dfrac{73^2-1}{12^2}}\\
    &=\sqrt{\dfrac{73^2}{12^2}\cdot\dfrac{73^2-1}{73^2}}\\
    &=\sqrt{\dfrac{73^2}{12^2}}\sqrt{\dfrac{73^2-1}{73^2}}\notag\\
    &=\dfrac{73}{12}\sqrt{1-\dfrac{1}{73^2}}\\
    &\approx\dfrac{73}{12}\left(1-\dfrac{1}{2\cdot73^2}\right)\label{A}
    \end{align}
    $$

=== "示例2"

    **代码**
    
    ```latex title="示例2"
    \begin{align*}
    v+m&=0&\text{Given}\tag1\\
    -w&=-w+0&\text{additive identity}\tag2\\
    -w+0&=-w+(v+w)&\text{equations $(1)$ and $(2)$}
    \end{align*}
    ```
    
    **效果**
    
    $$
    \begin{align*}
    v+m&=0&\text{Given}\tag1\\
    -w&=-w+0&\text{additive identity}\tag2\\
    -w+0&=-w+(v+w)&\text{equations $(1)$ and $(2)$}
    \end{align*}
    $$

!!! note "笔记"

    你可以使用`\label{标签}`来创建一个标签，就如上面的方程式序列中展示的那样，之后使用`\eqref{标签}`引用你想引用的公式。如果不想要括号，可以输入`\ref{标签}`。
    
    两个公式的不同列之间存在间隔，如果你不想要，可以通过将`align`替换为`alignat{1}`来去除列间隔。

### 方程组及其配置

#### 方程组

!!! note "说明"

    使用`\begin{array}...\end{array}`和`\left\{...\right.`来创建一个方程组,或者你也可以使用条件表达式组`\begin{cases}...\end{cases}`来实现相同效果。

##### 示例

```latex title="方程组"
\left\{
\begin{array}{l}
a_1x+b_1y+c_1z=d_1\\
a_2x+b_2y+c_2z=d_2\\
a_3x+b_3y+c_1z=d_3
\end{array}
\right.
\quad\text{或者}\quad
\begin{cases}
a_1x+b_1y+c_1z=d_1\\
a_2x+b_2y+c_2z=d_2\\
a_3x+b_3y+c_1z=d_3
\end{cases}
```

##### 效果

$$
\left\{
\begin{array}{l}
a_1x+b_1y+c_1z=d_1\\
a_2x+b_2y+c_2z=d_2\\
a_3x+b_3y+c_1z=d_3
\end{array}
\right.
\quad\text{或者}\quad
\begin{cases}
a_1x+b_1y+c_1z=d_1\\
a_2x+b_2y+c_2z=d_2\\
a_3x+b_3y+c_1z=d_3
\end{cases}
$$

#### 注释文字

##### 格式

```latex title="注释文字"
$\text{文字}$
```

##### 示例

```latex title="示例"
f(n)=\begin{cases}n/2,&\text{if $n$ is even}\\3n+1,&\text{if $n$ is odd}\end{cases}
```

##### 效果

$$
f(n)=\begin{cases}n/2,&\text{if $n$ is even}\\3n+1,&\text{if $n$ is odd}\end{cases}
$$

#### 配置行高

!!! note "说明"

    可以使用`\\[2ex]`语句替代该行末尾的`\\`来让编译器适配 , 其中`[ex]`指一个"X-Height" , 即x字母高度 , 也可以使用`[3ex]`或`[4ex]`等。

##### 示例及效果

=== "适配[2ex]"

    **示例**
    
    ```latex title="适配[2ex]"
    f(n)=
    \begin{cases}
    \dfrac n2,&\text{if $n$ is even}\\
    3n+1,&\text{if $n$ is odd}
    \end{cases}\tag{适配[2ex]}
    ```
    
    **效果**
    
    $$
    f(n)=
    \begin{cases}
    \dfrac n2,&\text{if $n$ is even}\\[2ex]
    3n+1,&\text{if $n$ is odd}
    \end{cases}\tag{适配[2ex]}
    $$

=== "不适配[2ex]"

    **示例**
    
    ```latex title="不适配[2ex]"
    f(n)=
    \begin{cases}
    \dfrac n2,&\text{if $n$ is even}\\
    3n+1,&\text{if $n$ is odd}
    \end{cases}\tag{不适配[2ex]}
    ```
    
    **效果**
    
    $$
    f(n)=
    \begin{cases}
    \dfrac n2,&\text{if $n$ is even}\\
    3n+1,&\text{if $n$ is odd}
    \end{cases}\tag{不适配[2ex]}
    $$

## 表格与图表

### 表格

#### 数组与表格

!!! note "说明"

    数组与表格均以`\begin{array}`开头,并在其后定义列数及每一列的文本对齐方式,`c` `l` `r`分别代表居中、左对齐及右对齐。若要插入垂直分割线，在定义中插入`|`，若要插入水平分割线，在定义中加入`\hline`。

##### 示例

```latex title="数组与表格"
\begin{array}{c|lcr}
n&\text{左对齐}&\text{居中对齐}&\text{右对齐}\\
\hline
1&0.24&1&125\\
2&-1&189&-8\\
3&-20&2000&1+10i
\end{array}
```

##### 效果

$$
\begin{array}{c|lcr}
n&\text{左对齐}&\text{居中对齐}&\text{右对齐}\\
\hline
1&0.24&1&125\\
2&-1&189&-8\\
3&-20&2000&1+10i
\end{array}
$$

#### 嵌套表格与数组

##### 示例

```latex title="嵌套表格与数组"
% outer vertical array of arrays 外层垂直表格
\begin{array}{c}
% inner horizontal array of arrays 内层水平表格
\begin{array}{cc}
% inner array of minimum values 内层"最小值"数组
\begin{array}{c|cccc}
\text{min}&0&1&2&3\\
\hline
0&0&0&0&0\\
1&0&1&1&1\\
2&0&1&2&2\\
3&0&1&2&3\\
\end{array}
&
% inner array of maximum values 内层"最大值"数组
\begin{array}{c|cccc}
\text{max}&0&1&2&3\\
\hline
0&0&1&2&3\\
1&1&1&2&3\\
2&2&2&2&3\\
3&3&3&3&3
\end{array}
\end{array}
% 内层第一行表格组结束
\\
% inner array of delta values 内层第二行Delta值数组
\begin{array}{c|cccc}
\Delta&0&1&2&3\\
\hline
0&0&1&2&3\\
1&1&0&1&2\\
2&2&1&0&1\\
3&3&2&1&0
\end{array}
% 内层第二行表格组结束
\end{array}
```

##### 效果

$$
% outer vertical array of arrays 外层垂直表格
\begin{array}{c}
% inner horizontal array of arrays 内层水平表格
\begin{array}{cc}
% inner array of minimum values 内层"最小值"数组
\begin{array}{c|cccc}
\text{min}&0&1&2&3\\
\hline
0&0&0&0&0\\
1&0&1&1&1\\
2&0&1&2&2\\
3&0&1&2&3\\
\end{array}
&
% inner array of maximum values 内层"最大值"数组
\begin{array}{c|cccc}
\text{max}&0&1&2&3\\
\hline
0&0&1&2&3\\
1&1&1&2&3\\
2&2&2&2&3\\
3&3&3&3&3
\end{array}
\end{array}
% 内层第一行表格组结束
\\
% inner array of delta values 内层第二行Delta值数组
\begin{array}{c|cccc}
\Delta&0&1&2&3\\
\hline
0&0&1&2&3\\
1&1&0&1&2\\
2&2&1&0&1\\
3&3&2&1&0
\end{array}
% 内层第二行表格组结束
\end{array}
$$

### 图表

#### 交换图表

!!! note "说明"

    使用一行`$\require{AMScd}$`语句来允许交换图表的显示,并通过在开头使用`\begin{CD}`,结尾使用`\end{CD}`来创建。

???+ note "解释"

    `@>>>`代表右箭头
    
    `@<<<`代表左箭头
    
    `@VVV`代表下箭头
    
    `@AAA`代表上箭头
    
    `@=`代表水平双实线
    
    `@|`代表竖直双实线
    
    `@.`代表没有箭头
    
    在`@>>>`的`>>>`之间任意插入文字即代表该箭头的注释文字。

##### 示例

```latex title="交换图表"
\require{AMScd}
\begin{CD}
A@>>>B@>{\text{very long label}}>>C\\
@.@AAA@|\\
D@=E@<<<F
\end{CD}
```

##### 效果

$$
\require{AMScd}
\begin{CD}
A@>>>B@>{\text{very long label}}>>C\\
@.@AAA@|\\
D@=E@<<<F
\end{CD}
$$

## 字符与字体

### 希腊字母

| 语法                     | 字母                     | 语法                      | 字母                      | 语法               | 字母               |
| ------------------------ | ------------------------ | ------------------------- | ------------------------- | ------------------ | ------------------ |
| `A(\alpha)`              | $A(\alpha)$              | `B(\beta)`                | $B(\beta)$                | `\Gamma(\gamma)`   | $\Gamma(\gamma)$   |
| `E(\epsilon)\varepsilon` | $E(\epsilon)\varepsilon$ | `Z(\zeta)`                | $Z(\zeta)$                | `H(\eta)`          | $H(\eta)$          |
| `I(\iota)`               | $I(\iota)$               | `K(\kappa)\varkappa`      | $K(\kappa)\varkappa$      | `\Lambda(\lambda)` | $\Lambda(\lambda)$ |
| `N(\nu)`                 | $N(\nu)$                 | `\Xi(\xi)`                | $\Xi(\xi)$                | `O(\omicron)`      | $O(\omicron)$      |
| `P(\rho)\varrho`         | $P(\rho)\varrho$         | `\Sigma(\sigma)\varsigma` | $\Sigma(\sigma)\varsigma$ | `T(\tau)`          | $T(\tau)$          |
| `\Phi(\phi)\varphi`      | $\Phi(\phi)\varphi$      | `X(\chi)`                 | $X(\chi)$                 | `\Psi(\psi)`       | $\Psi(\psi)$       |
| `\Delta(\delta)`         | $\Delta(\delta)$         | `\Theta(\theta)\vartheta` | $\Theta(\theta)\vartheta$ | `M(\mu)`           | $M(\mu)$           |
| `\Pi(\pi)\varpi`         | $\Pi(\pi)\varpi$         | `\Omega(\omega)`          | $\Omega(\omega)$          | `\upsilon`         | $\upsilon$         |
| `\ell`                   | $\ell$                   | `\eth`                    | $\eth$                    | `\hbar`            | $\hbar$            |
| `\hslash`                | $\hslash$                | `\mho`                    | $\mho$                    | `\partial`         | $\partial$         |

### 常见符号

#### 杂项符号

| 输入           | 显示           | 输入          | 显示          |
| -------------- | -------------- | ------------- | ------------- |
| `\infty`       | $\infty$       | `\forall`     | $\forall$     |
| `\Re`          | $\Re$          | `\Im`         | $\Im$         |
| `\nabla`       | $\nabla$       | `\exists`     | $\exists$     |
| `\partial`     | $\partial$     | `\nexists`    | $\nexists$    |
| `\emptyset`    | $\emptyset$    | `\varnothing` | $\varnothing$ |
| `\wp`          | $\wp$          | `\complement` | $\complement$ |
| `\neg`         | $\neg$         | `\cdots`      | $\cdots$      |
| `\square`      | $\square$      | `\surd`       | $\surd$       |
| `\blacksquare` | $\blacksquare$ | `\triangle`   | $\triangle$   |

#### 箭头

| 输入               | 显示               | 输入                 | 显示                 |
| ------------------ | ------------------ | -------------------- | -------------------- |
| `\leftarrow`       | $\leftarrow$       | `\Leftarrow`         | $\Leftarrow$         |
| `\rightarrow`      | $\rightarrow$      | `\Rightarrow`        | $\Rightarrow$        |
| `\leftrightarrow`  | $\leftrightarrow$  | `\rightleftharpoons` | $\rightleftharpoons$ |
| `\uparrow`         | $\uparrow$         | `\downarrow`         | $\downarrow$         |
| `\Uparrow`         | $\Uparrow$         | `\Downarrow`         | $\Downarrow$         |
| `\Leftrightarrow`  | $\Leftrightarrow$  | `\Updownarrow`       | $\Updownarrow$       |
| `\mapsto`          | $\mapsto$          | `\longmapsto`        | $\longmapsto$        |
| `\nearrow`         | $\nearrow$         | `\searrow`           | $\searrow$           |
| `\swarrow`         | $\swarrow$         | `\nwarrow`           | $\nwarrow$           |
| `\leftharpoonup`   | $\leftharpoonup$   | `\rightharpoonup`    | $\rightharpoonup$    |
| `\leftharpoondown` | $\leftharpoondown$ | `\rightharpoondown`  | $\rightharpoondown$  |

#### 二元运算/关系符号

| 输入     | 显示     | 输入        | 显示        |
| -------- | -------- | ----------- | ----------- |
| `\times` | $\times$ | `\cdot`     | $\cdot$     |
| `\div`   | $\div$   | `\cap`      | $\cap$      |
| `\cup`   | $\cup$   | `\neq`      | $\neq$      |
| `\leq`   | $\leq$   | `\geq`      | $\geq$      |
| `\in`    | $\in$    | `\perp`     | $\perp$     |
| `\notin` | $\notin$ | `\subset`   | $\subset$   |
| `\simeq` | $\simeq$ | `\approx`   | $\approx$   |
| `\wedge` | $\wedge$ | `\vee`      | $\vee$      |
| `\oplus` | $\oplus$ | `\otimes`   | $\otimes$   |
| `\Box`   | $\Box$   | `\boxtimes` | $\boxtimes$ |
| `\equiv` | $\equiv$ | `\cong`     | $\cong$     |

### 特殊字符

!!! note "说明"

    可以在字符前使用`\large`或`\small`以显示更大或更小的字符。${\LARGE A}{\Large A}{\large A}A{\small A}$

#### 关系运算符

| 输入        | 显示        | 输入         | 显示         | 输入           | 显示         |
| ----------- | ----------- | ------------ | ------------ | -------------- | ------------ |
| `\pm(\mp)`  | $\pm(\mp)$  | `\times`     | $\times$     | `\div`         | $\div$       |
| `\nmid`     | $\nmid$     | `\cdot`      | $\cdot$      | `\mid`         | $\mid$       |
| `\bigodot`  | $\bigodot$  | `\bigotimes` | $\bigotimes$ | `\bigoplus`    | $\bigoplus$  |
| `\ge`       | $\ge$       | `\le`        | $\le$        | `\ll`          | $\ll$        |
| `\geqslant` | $\geqslant$ | `\leqslant`  | $\leqslant$  | `\neq`         | $\neq$       |
| `\approx`   | $\approx$   | `\bmod`      | $\bmod{2}$   | `\triangleq`   | $\triangleq$ |
| `\sim`      | $\sim$      | `\doteq`     | $\doteq$     | `\equiv`       | $\equiv$     |
| `\cong`     | $\cong$     | `\propto`    | $\propto$    | `\parallel(\\` | )            |
| `\prec`     | $\prec$     | `\pmod{2}`   | $\pmod{2}$   |                |              |

#### 集合运算符

| 输入        | 显示        | 输入          | 显示          | 输入         | 显示         |
| ----------- | ----------- | ------------- | ------------- | ------------ | ------------ |
| `\emptyset` | $\emptyset$ | `\varnothing` | $\varnothing$ | `\ni`        | $\ni$        |
| `\subset`   | $\subset$   | `\subseteq`   | $\subseteq$   | `\subsetneq` | $\subsetneq$ |
| `\supset`   | $\supset$   | `\supseteq`   | $\supseteq$   | `\supsetneq` | $\supsetneq$ |
| `\bigcap`   | $\bigcap$   | `\bigcup`     | $\bigcup$     | `\setminus`  | $\setminus$  |
| `\bigvee`   | $\bigvee$   | `\bigwedge`   | $\bigwedge$   | `\cap`       | $\cap$       |
| `\in`       | $\in$       | `\notin`      | $\notin$      | `\cup`       | $\cup$       |

#### 三角运算符

| 输入     | 显示     | 输入   | 显示   | 输入     | 显示     |
| -------- | -------- | ------ | ------ | -------- | -------- |
| `\circ`  | $\circ$  | `\bot` | $\bot$ | `\angle` | $\angle$ |
| `^\circ` | $^\circ$ |        |        |          |          |

#### 微积分运算符

| 输入    | 显示    | 输入     | 显示                 | 输入        | 显示     |
| ------- | ------- | -------- | -------------------- | ----------- | -------- |
| `\int`  | $\int$  | `\iint`  | $\iint$              | `\iiint`    | $\iiint$ |
| `\oint` | $\oint$ | `\oiint` | $\oint\!\!\!\!\oint$ | `\prime(‘)` | $\prime$ |
| `\lim`  | $\lim$  | `\infty` | $\infty$             | `\nabla`    | $\nabla$ |

#### 逻辑运算符

| 输入       | 显示       | 输入         | 显示         | 输入     | 显示     |
| ---------- | ---------- | ------------ | ------------ | -------- | -------- |
| `\because` | $\because$ | `\therefore` | $\therefore$ | `\lnot`  | $\lnot$  |
| `\forall`  | $\forall$  | `\exists`    | $\exists$    | `\vDash` | $\vDash$ |
| `\not>`    | $\not>$    | `\not<`      | $\not<$      |          |          |
| `\land`    | $\land$    | `\lor`       | $\lor$       |          |          |
| `\top`     | $\top$     | `\vdash`     | $\vdash$     |          |          |

#### 带帽符号

| 输入             | 显示             | 输入              | 显示              |
| ---------------- | ---------------- | ----------------- | ----------------- |
| `\hat{xy}`       | $\hat{xy}$       | `\widehat{xyz}`   | $\widehat{xyz}$   |
| `\tilde{xy}`     | $\tilde{xy}$     | `\widetilde{xyz}` | $\widetilde{xyz}$ |
| `\check{x}`      | $\check{x}$      | `\breve{y}`       | $\breve{y}$       |
| `\grave{x}`      | $\grave{x}$      | `\acute{y}`       | $\acute{y}$       |
| `\dot{x}`        | $\dot{x}$        | `\ddot{x}`        | $\ddot{x}$        |
| `\overparen{xy}` | $\overparen{xy}$ |                   |                   |

#### 选取符号

| 输入                             | 显示                             | 输入                              | 显示                              |
| -------------------------------- | -------------------------------- | --------------------------------- | --------------------------------- |
| `\fbox{a+b+c+d}`                 | $\fbox{a+b+c+d}$                 | `\underbrace{xx\cdots x}_{10个x}` | $\underbrace{xx\cdots x}_{10个x}$ |
| `\overbrace{xx\cdots x}^{10个x}` | $\overbrace{xx\cdots x}^{10个x}$ |                                   |                                   |

#### 箭头符号

| 输入             | 显示             | 输入                | 显示                | 输入                  | 显示                  |
| ---------------- | ---------------- | ------------------- | ------------------- | --------------------- | --------------------- |
| `\leftarrow`     | $\leftarrow$     | `\rightarrow`       | $\rightarrow$       | `\leftrightarrow`     | $\leftrightarrow$     |
| `\longleftarrow` | $\longleftarrow$ | `\longrightarrow`   | $\longrightarrow$   | `\longleftrightarrow` | $\longleftrightarrow$ |
| `\Leftarrow`     | $\Leftarrow$     | `\Rightarrow`       | $\Rightarrow$       | `\Leftrightarrow`     | $\Leftrightarrow$     |
| `\Longleftarrow` | $\Longleftarrow$ | `\Longrightarrow`   | $\Longrightarrow$   | `\Longleftrightarrow` | $\Longleftrightarrow$ |
| `\uparrow`       | $\uparrow$       | `\downarrow`        | $\downarrow$        | `\updownarrow`        | $\updownarrow$        |
| `\Uparrow`       | $\Uparrow$       | `\Downarrow`        | $\Downarrow$        | `\Updownarrow`        | $\Updownarrow$        |
| `\to`            | $\to$            | `\swarrow`          | $\swarrow$          | `\nearrow`            | $\nearrow$            |
| `\gets`          | $\gets$          | `\searrow`          | $\searrow$          | `\nwarrow`            | $\nwarrow$            |
| `\mapsto`        | $\mapsto$        | `\rightrightarrows` | $\rightrightarrows$ |                       |                       |

#### 空格

| 输入  | 效果   | 输入      | 效果   | 输入     | 效果       |
| ----- | ------ | --------- | ------ | -------- | ---------- |
| `\\!` | $|\!|$ | `默认`    | $||$   | `\quad`  | $|\quad|$  |
| `\,`  | $|\,|$ | `\;(\\ )` | $|\;|$ | `\qquad` | $|\qquad|$ |

### 字体

!!! note "格式"

    ```latex title="格式"
    ${\字体{需要转换的字符}}$
    ```

| 输入  | 说明     | 显示            | 输入    | 说明       | 显示              |
| ----- | -------- | --------------- | ------- | ---------- | ----------------- |
| `\rm` | 罗马体   | ${\rm{Sample}}$ | `\cal`  | 花体       | ${\cal{Sample}}$  |
| `\it` | 意大利体 | ${\it{Sample}}$ | `\Bbb`  | 黑板粗体   | ${\Bbb{Sample}}$  |
| `\bf` | 粗体     | ${\bf{Sample}}$ | `\mit`  | 数学斜体   | ${\mit{Sample}}$  |
| `\sf` | 等线体   | ${\sf{Sample}}$ | `\scr`  | 手写体     | ${\scr{Sample}}$  |
| `\tt` | 打字机体 | ${\tt{Sample}}$ | `\frak` | 旧德式字体 | ${\frak{Sample}}$ |
