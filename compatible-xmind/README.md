.xmind文件其实是一个压缩包，解压后有两种类型：
一种是只有content.xml；
一种是既有content.xml，又有content.json文件。   

打开这两个文件分析，会发现：当只有content.xml文件的时候，该文件内存储的就是整个xmind的内容，格式等数据，而后续只需要让代码去读取这个文件就可以还原xmind的内容了。

但是若打开压缩包发现既有content.xml，又有content.json文件时，我们打开其中的content.xml会发现，里面并不是正常的数据，而是xmind的警告信息，而真正的文件内容等都存在content.json文件里面

因此我们只需要让代码去读这个json文件，就可以还原xmind的内容了。
