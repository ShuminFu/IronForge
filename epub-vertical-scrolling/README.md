1. [Apple's suggestion](https://help.apple.com/itc/booksassetguide/en.lproj/itc56959c420.html)
2. ```bash
   unzip xxx.epub -d ./
   ```
3. modifie the content of the file `EPUB/content.opf` to add the following line:
    ```xml
    <meta property="rendition:flow">scrolled-continuous</meta>
    ```
4. run zip.py
5. [Alternative apps](https://www.reddit.com/r/macapps/comments/119piqz/vertical_scrolling_epub_reader_recommends/)