# VeighNa框架的AkShare数据服务接口

<p align="center">
  <img src ="https://vnpy.oss-cn-shanghai.aliyuncs.com/vnpy-logo.png"/>
</p>

<p align="center">
    <img src ="https://img.shields.io/badge/version-1.2.64.3-blueviolet.svg"/>
    <img src ="https://img.shields.io/badge/platform-windows|linux|macos-yellow.svg"/>
    <img src ="https://img.shields.io/badge/python-3.7|3.8|3.9|3.10-blue.svg"/>
    <img src ="https://img.shields.io/github/license/vnpy/vnpy.svg?color=orange"/>
</p>

## 说明


## 数据使用事项


## 安装

安装环境推荐基于3.0.0版本以上的【[**VeighNa Studio**](https://www.vnpy.com)】。

直接使用pip命令：

```
pip install vnpy_akshare
```


或者下载源代码后，解压后在cmd中运行：

```
pip install .
```


## 使用

在VeighNa中使用AkShare时，需要在全局配置中填写以下字段信息：

|名称|含义|必填|举例|
|---------|----|---|---|
|datafeed.name|名称|是|akshare|
|datafeed.username|用户名|否|token|
|datafeed.password|密码|否|token|
