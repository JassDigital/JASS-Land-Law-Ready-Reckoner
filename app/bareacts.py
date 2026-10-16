import json, sys, re, html
from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTextBrowser, QFileDialog, QMessageBox,
    QSplitter, QFrame, QApplication
)

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "bare_act_sources.json"
if sys.platform == "win32":
    CACHE = Path.home() / "AppData" / "Local" / "JASS" / "LandLawReadyReckoner" / "acts"
else:
    CACHE = Path.home() / ".local" / "share" / "jass" / "land-law-ready-reckoner" / "acts"
CACHE.mkdir(parents=True, exist_ok=True)
BLUE = "#315fe9"

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","noscript"): self.skip += 1
        if tag in ("p","div","br","tr","li","h1","h2","h3","h4","section","article"):
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script","style","noscript") and self.skip: self.skip -= 1
        if tag in ("p","div","br","tr","li","h1","h2","h3","h4","section","article"):
            self.parts.append("\n")
    def handle_data(self, data):
        if not self.skip and data.strip(): self.parts.append(data.strip()+" ")
    def result(self):
        text="".join(self.parts)
        text=re.sub(r"[ \t]+\n","\n",text)
        text=re.sub(r"\n{3,}","\n\n",text)
        return text.strip()

class BareActsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items=json.loads(SOURCES.read_text(encoding="utf-8"))
        self.selected=None
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(12)
        intro=QLabel("Search the catalogue, open authoritative source pages, or cache full statutory text for offline reading. The three new criminal codes have full-text NCRB compendium links.")
        intro.setWordWrap(True); intro.setStyleSheet("color:#6f7e94;font-size:12px")
        layout.addWidget(intro)
        top=QHBoxLayout()
        self.search=QLineEdit(); self.search.setPlaceholderText("Search Act name, subject, state or source…")
        self.search.textChanged.connect(self.fill_list)
        top.addWidget(self.search,1)
        self.import_btn=QPushButton("Import local text")
        self.import_btn.clicked.connect(self.import_text)
        top.addWidget(self.import_btn)
        layout.addLayout(top)
        split=QSplitter(Qt.Orientation.Horizontal)
        self.list=QListWidget()
        self.list.setStyleSheet("QListWidget{background:white;border:1px solid #e1e8f2;border-radius:11px;padding:5px} QListWidget::item{padding:10px;border-radius:7px;color:#19283f} QListWidget::item:selected{background:#eaf0ff;color:#244dd0}")
        self.list.currentItemChanged.connect(self.select_item)
        split.addWidget(self.list)
        right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(0,0,0,0); rl.setSpacing(8)
        self.detail_title=QLabel("Select an Act")
        self.detail_title.setStyleSheet("font-size:18px;font-weight:800;color:#19283f")
        self.meta=QLabel("Official-source catalogue"); self.meta.setWordWrap(True); self.meta.setStyleSheet("font-size:11px;color:#7c8aa0")
        self.text=QTextBrowser(); self.text.setOpenExternalLinks(True)
        self.text.setStyleSheet("background:white;border:1px solid #e1e8f2;border-radius:11px;padding:12px;color:#26364e")
        actions=QHBoxLayout()
        self.open_btn=QPushButton("Open official source"); self.open_btn.clicked.connect(self.open_source)
        self.cache_btn=QPushButton("Fetch full text for offline use"); self.cache_btn.clicked.connect(self.cache_text)
        self.copy_btn=QPushButton("Copy text"); self.copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.text.toPlainText()))
        actions.addWidget(self.open_btn); actions.addWidget(self.cache_btn); actions.addWidget(self.copy_btn)
        rl.addWidget(self.detail_title); rl.addWidget(self.meta); rl.addWidget(self.text,1); rl.addLayout(actions)
        split.addWidget(right); split.setStretchFactor(0,2); split.setStretchFactor(1,4)
        layout.addWidget(split,1)
        status=QLabel(f"Offline text cache: {CACHE}")
        status.setWordWrap(True); status.setStyleSheet("font-size:10px;color:#8997aa")
        layout.addWidget(status)
        self.fill_list()
        if self.list.count(): self.list.setCurrentRow(0)

    def cache_path(self, item):
        safe=re.sub(r"[^a-z0-9]+","_",item["title"].lower()).strip("_")
        return CACHE/(safe+".txt")

    def fill_list(self):
        current=self.selected.get("title") if self.selected else None
        self.list.clear()
        q=self.search.text().strip().lower()
        for item in self.items:
            hay=" ".join(str(item.get(k,"")) for k in ("title","category","jurisdiction","source_name","notes")).lower()
            if q and q not in hay: continue
            p=self.cache_path(item)
            suffix="  ·  OFFLINE" if p.exists() else ""
            li=QListWidgetItem(item["title"]+suffix+"\n"+item["category"])
            li.setData(Qt.ItemDataRole.UserRole,item)
            self.list.addItem(li)
            if current==item["title"]: self.list.setCurrentItem(li)
        if self.list.count() and not self.list.currentItem(): self.list.setCurrentRow(0)

    def select_item(self, current, previous=None):
        if not current: return
        self.selected=current.data(Qt.ItemDataRole.UserRole)
        r=self.selected; p=self.cache_path(r)
        self.detail_title.setText(r["title"])
        self.meta.setText(f"{r['category']}  •  {r['jurisdiction']}\\nSource: {r['source_name']}\\n{r['notes']}")
        if p.exists():
            content=p.read_text(encoding="utf-8",errors="replace")
            self.text.setPlainText(content)
            self.cache_btn.setText("Refresh cached text")
            self.meta.setText(self.meta.text()+f"\\nOffline copy cached locally · {p.stat().st_size:,} bytes")
        else:
            self.text.setHtml(
                "<h3>Official text source</h3>"
                f"<p>{html.escape(r['notes'])}</p>"
                f"<p><a href='{html.escape(r['official_url'],quote=True)}'>Open official legislation/source page</a></p>"
                + (f"<p><a href='{html.escape(r['full_text_url'],quote=True)}'>Open full text at {html.escape(r['source_name'])}</a></p>" if r.get("full_text_url") else "")
                + "<p><b>Offline use:</b> select “Fetch full text for offline use” where supported. For other Acts, open the official portal and use “Import local text” after saving a TXT/HTML copy. PDF files can be opened in your PDF reader.</p>"
            )
            self.cache_btn.setText("Fetch full text for offline use" if r.get("offline_supported") else "Offline cache not available")
        self.cache_btn.setEnabled(bool(r.get("offline_supported")))
        self.copy_btn.setEnabled(True)

    def open_source(self):
        if self.selected:
            import webbrowser
            webbrowser.open(self.selected["official_url"])

    def cache_text(self):
        if not self.selected or not self.selected.get("offline_supported"): return
        r=self.selected
        self.cache_btn.setEnabled(False); self.cache_btn.setText("Fetching…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            req=Request(r["full_text_url"],headers={"User-Agent":"JASS-Land-Law-Ready-Reckoner/0.2 (legal research reference)"})
            with urlopen(req,timeout=35) as response:
                raw=response.read()
                charset=response.headers.get_content_charset() or "utf-8"
            page=raw.decode(charset,errors="replace")
            parser=TextExtractor(); parser.feed(page); content=parser.result()
            if len(content)<1000:
                raise ValueError("The source returned too little text. Open the official source in a browser and try again later.")
            content=("SOURCE: "+r["source_name"]+"\\nTITLE: "+r["title"]+"\\nURL: "+r["full_text_url"]+"\\nFETCHED: current download time on this computer\\n\\n"
                     "NOTICE: This cached text is a convenience copy. Verify amendments, notifications and the official text before legal reliance.\\n\\n"+content)
            self.cache_path(r).write_text(content,encoding="utf-8")
            self.text.setPlainText(content)
            QMessageBox.information(self,"Full text cached",f"{r['title']} has been saved for offline reading. Re-fetch periodically to check for updates.")
            self.fill_list()
        except Exception as e:
            QMessageBox.warning(self,"Could not cache text",f"Could not fetch the source automatically.\\n\\n{e}\\n\\nUse Open official source to read it online.")
        finally:
            QApplication.restoreOverrideCursor()
            self.cache_btn.setEnabled(bool(r.get("offline_supported")))
            self.cache_btn.setText("Refresh cached text" if self.cache_path(r).exists() else "Fetch full text for offline use")

    def import_text(self):
        path,_=QFileDialog.getOpenFileName(self,"Import a local Act text file","","Text or HTML files (*.txt *.html *.htm);;All files (*)")
        if not path: return
        try:
            p=Path(path); content=p.read_text(encoding="utf-8",errors="replace")
            if p.suffix.lower() in (".html",".htm"):
                parser=TextExtractor(); parser.feed(content); content=parser.result()
            target=CACHE/(re.sub(r"[^a-z0-9]+","_",p.stem.lower()).strip("_")+".txt")
            target.write_text("IMPORTED LOCAL TEXT: "+p.name+"\\nVerify source, version and amendments before legal reliance.\\n\\n"+content,encoding="utf-8")
            QMessageBox.information(self,"Imported",f"Saved a local text copy at:\\n{target}")
            self.fill_list()
        except Exception as e:
            QMessageBox.critical(self,"Import failed",str(e))
