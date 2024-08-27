1. https://help.apple.com/itc/booksassetguide/en.lproj/itc56959c420.html
2. unzip xxx.epub -d ./
2. modifie the content of the file `EPUB/content.opf` to add the following line:
```xml
    <meta property="rendition:flow">scrolled-continuous</meta>
```
3. run zip.py