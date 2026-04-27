import pymupdf

doc = pymupdf.open('song.pdf')
page = doc.load_page(0)  # load the first page
pix = page.get_pixmap(dpi=150)
pix.save("song_page_1.png")
print("Saved song_page_1.png")
