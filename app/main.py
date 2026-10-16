import sys, json, webbrowser
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import *
from . import database as db
from .bareacts import BareActsWidget

BG="#f3f6fb"; INK="#19283f"; BLUE="#315fe9"; BORDER="#e1e8f2"
def btn(text, primary=False):
    b=QPushButton(text); b.setCursor(Qt.CursorShape.PointingHandCursor); b.setObjectName("primary" if primary else "normal"); return b

class DetailDialog(QDialog):
    def __init__(self,title,fields,parent=None):
        super().__init__(parent); self.setWindowTitle(title); self.resize(720,560)
        lay=QVBoxLayout(self); lay.setContentsMargins(24,20,24,18); h=QLabel(title); h.setStyleSheet("font-size:22px;font-weight:800"); lay.addWidget(h)
        for label,value in fields:
            if not value: continue
            x=QLabel(label.upper()); x.setStyleSheet("font-size:10px;font-weight:800;letter-spacing:1px;color:#7b899f")
            y=QLabel(value); y.setWordWrap(True); y.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); y.setStyleSheet("font-size:13px;color:#293951")
            lay.addWidget(x); lay.addWidget(y)
        lay.addStretch(); close=btn("Close"); close.clicked.connect(self.accept); lay.addWidget(close,0,Qt.AlignmentFlag.AlignRight)

class NoteDialog(QDialog):
    def __init__(self,n=None,parent=None):
        super().__init__(parent); n=n or {}; self.setWindowTitle("Matter note"); self.resize(650,560)
        self.title=QLineEdit(n.get("title","")); self.state=QComboBox(); self.state.addItems(["Haryana","Punjab"]); self.state.setCurrentText(n.get("state","Haryana"))
        self.issue=QComboBox(); self.issue.addItems(["Possession / injunction","Mutation / inheritance","Partition","Succession / will","Forged document","Tenancy","Other"]); self.issue.setCurrentText(n.get("issue","Possession / injunction"))
        self.stage=QComboBox(); self.stage.addItems(["Pre-litigation","Revenue proceedings","Civil court","Police / criminal","Appeal / revision"]); self.stage.setCurrentText(n.get("stage","Pre-litigation"))
        self.notes=QTextEdit(); self.notes.setPlainText(n.get("notes","")); self.notes.setPlaceholderText("Facts, dates, documents, witnesses, questions for counsel…")
        form=QFormLayout(); form.addRow("Matter title",self.title); form.addRow("State",self.state); form.addRow("Issue",self.issue); form.addRow("Stage",self.stage)
        lay=QVBoxLayout(self); lay.setContentsMargins(22,20,22,18); lay.addLayout(form); lay.addWidget(QLabel("Private notes (stored locally)")); lay.addWidget(self.notes,1)
        row=QHBoxLayout(); row.addStretch(); c=btn("Cancel"); s=btn("Save note",True); c.clicked.connect(self.reject); s.clicked.connect(self.accept); row.addWidget(c); row.addWidget(s); lay.addLayout(row)
    def value(self): return {"title":self.title.text().strip(),"state":self.state.currentText(),"issue":self.issue.currentText(),"stage":self.stage.currentText(),"notes":self.notes.toPlainText().strip()}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("JASS Land Law Ready Reckoner"); self.resize(1400,880)
        self.setStyleSheet(f"""
        QMainWindow,QWidget#root{{background:{BG};color:{INK};font-family:'Segoe UI',Arial}}
        QPushButton{{padding:10px 13px;border-radius:9px;border:1px solid {BORDER};background:white;color:#293951;font-weight:600}}
        QPushButton:hover{{border-color:{BLUE};background:#f6f8ff}} QPushButton#primary{{background:{BLUE};color:white;border:0}}
        QLineEdit,QComboBox,QTextEdit{{background:white;border:1px solid {BORDER};border-radius:9px;padding:9px;color:{INK}}}
        QTableWidget{{background:white;border:1px solid {BORDER};border-radius:10px;gridline-color:#edf1f7;selection-background-color:#e8efff;selection-color:{INK}}}
        QHeaderView::section{{background:#f7f9fd;color:#66758d;border:0;border-bottom:1px solid {BORDER};padding:10px;font-weight:700}}
        QListWidget{{background:transparent;border:0;outline:0}} QListWidget::item{{padding:12px;border-radius:9px;color:#c4d0e1;margin:2px 0}} QListWidget::item:selected{{background:#2c4265;color:white}}
        """)
        root=QWidget(); root.setObjectName("root"); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        side=QFrame(); side.setFixedWidth(246); side.setStyleSheet("background:#14243b;border:0"); sl=QVBoxLayout(side); sl.setContentsMargins(16,24,16,18)
        br=QHBoxLayout(); mark=QLabel("§"); mark.setFixedSize(42,42); mark.setAlignment(Qt.AlignmentFlag.AlignCenter); mark.setStyleSheet("background:#dce8ff;color:#244ca8;border-radius:12px;font-size:27px;font-weight:800")
        brand=QVBoxLayout(); a=QLabel("JASS LEGAL"); a.setStyleSheet("color:white;font-size:13px;font-weight:900;letter-spacing:1px"); b=QLabel("LAND LAW READY RECKONER"); b.setStyleSheet("color:#91a5c2;font-size:8px;font-weight:800"); brand.addWidget(a); brand.addWidget(b); br.addWidget(mark); br.addLayout(brand); sl.addLayout(br)
        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet("background:#2b3c55"); sl.addWidget(sep)
        self.nav=QListWidget()
        for s in ["Home","Legal Issues","Acts & Statutes","Bare Acts & Sources","Leading Cases","Evidence Planner","My Matter Notes","Sources & About"]: self.nav.addItem(s)
        self.nav.setCurrentRow(0); self.nav.currentTextChanged.connect(self.show_page); sl.addWidget(self.nav,1)
        foot=QLabel("LOCAL-FIRST REFERENCE\\nResearch aid, not legal advice"); foot.setStyleSheet("color:#91a5c2;font-size:10px;padding:8px"); sl.addWidget(foot); outer.addWidget(side)
        main=QWidget(); ml=QVBoxLayout(main); ml.setContentsMargins(28,24,28,20); ml.setSpacing(16)
        top=QHBoxLayout(); titles=QVBoxLayout(); self.eyebrow=QLabel("PUNJAB & HARYANA  /  AGRICULTURAL LAND"); self.eyebrow.setStyleSheet("font-size:10px;font-weight:900;letter-spacing:1.5px;color:#7e8ca2")
        self.heading=QLabel("Land Law Ready Reckoner"); self.heading.setStyleSheet("font-size:28px;font-weight:850"); self.subtitle=QLabel("A practical research desk for land and revenue litigation"); self.subtitle.setStyleSheet("color:#7c8aa0;font-size:13px")
        titles.addWidget(self.eyebrow); titles.addWidget(self.heading); titles.addWidget(self.subtitle); top.addLayout(titles); top.addStretch(); top.addWidget(QLabel("State")); self.state=QComboBox(); self.state.addItems(["Haryana","Punjab"]); self.state.setMinimumWidth(130); top.addWidget(self.state); ml.addLayout(top)
        self.content=QWidget(); self.content_l=QVBoxLayout(self.content); self.content_l.setContentsMargins(0,0,0,0); self.content_l.setSpacing(15); ml.addWidget(self.content,1)
        bottom=QHBoxLayout(); f=QLabel("JASS LAND LAW READY RECKONER  •  OFFLINE REFERENCE"); f.setStyleSheet("font-size:9px;font-weight:900;letter-spacing:1px;color:#a0adbf"); bottom.addWidget(f); bottom.addStretch(); bottom.addWidget(QLabel("Matter notes stay on this computer")); ml.addLayout(bottom); outer.addWidget(main,1)
        self.show_page("Home")
    def clear(self):
        while self.content_l.count():
            it=self.content_l.takeAt(0)
            if it.widget(): it.widget().deleteLater()
    def panel(self,title,sub=""):
        f=QFrame(); f.setStyleSheet(f"QFrame{{background:white;border:1px solid {BORDER};border-radius:13px}}"); l=QVBoxLayout(f); l.setContentsMargins(17,15,17,15); l.setSpacing(10)
        h=QLabel(title); h.setStyleSheet("font-size:17px;font-weight:800"); l.addWidget(h)
        if sub:
            x=QLabel(sub); x.setWordWrap(True); x.setStyleSheet("font-size:12px;color:#7c8aa0"); l.addWidget(x)
        return f,l
    def metric_card(self,title,value,desc,color):
        f=QFrame(); f.setStyleSheet(f"QFrame{{background:white;border:1px solid {BORDER};border-radius:13px}}"); l=QVBoxLayout(f); l.setContentsMargins(15,14,15,14)
        a=QLabel(title.upper()); a.setStyleSheet("font-size:10px;font-weight:900;letter-spacing:1px;color:#7d8ba1")
        b=QLabel(value); b.setStyleSheet(f"font-size:27px;font-weight:850;color:{color}")
        c=QLabel(desc); c.setWordWrap(True); c.setStyleSheet("font-size:11px;color:#8290a5")
        l.addWidget(a); l.addWidget(b); l.addWidget(c); return f
    def show_page(self,page):
        self.clear(); self.heading.setText("Land Law Ready Reckoner" if page=="Home" else page)
        self.subtitle.setText({"Home":"A practical research desk for land and revenue litigation","Legal Issues":"Start from the problem, then map law, proof and possible remedies","Acts & Statutes":"Core statutes and official research sources","Bare Acts & Sources":"Open authoritative bare acts and cache supported full texts for offline reading","Leading Cases":"Starter authorities with summaries and links to full judgments","Evidence Planner":"Build an issue-specific document and witness checklist","My Matter Notes":"Private working notes stored locally on this computer","Sources & About":"Source policy, scope and legal safeguards"}.get(page,""))
        {"Home":self.home,"Legal Issues":self.guides_page,"Acts & Statutes":lambda:self.library_page("acts"),"Bare Acts & Sources":self.bare_acts_page,"Leading Cases":lambda:self.library_page("cases"),"Evidence Planner":self.evidence_page,"My Matter Notes":self.notes_page,"Sources & About":self.about_page}.get(page,self.home)()
    def home(self):
        row=QHBoxLayout()
        for args in [("ACTS & STATUTES",str(len(db.query_all("acts"))),"Core reference entries",BLUE),("LEADING CASES",str(len(db.query_all("cases"))),"Starter case-law library","#15966b"),("ISSUE GUIDES",str(len(db.query_all("guides"))),"Practical litigation scenarios","#b57813"),("STATE COVERAGE","2","Punjab and Haryana","#8157cb")]: row.addWidget(self.metric_card(*args))
        self.content_l.addLayout(row)
        left,l=self.panel("Start with a legal problem","Select an issue to see a research path and evidence checklist.")
        for t,d in [("Threatened forcible dispossession","Possession, injunction and police/civil routes"),("Mutation challenged as incorrect","Revenue record vs title/succession dispute"),("Partition of joint agricultural land","Shares, forum, procedure and record set"),("Suspected forged deed or false record","Preserve records and assess civil/criminal tracks"),("Inheritance and succession dispute","Family tree, will, shares and property character")]:
            b=QPushButton(t+"  →"); b.setStyleSheet("text-align:left;padding:11px;background:#fbfcff"); b.clicked.connect(lambda checked=False,title=t:self.open_guide(title)); l.addWidget(b)
        right,r=self.panel("Research workflow","Use the app as a checklist-driven companion.")
        r.addWidget(QLabel("1. Identify the precise issue and dates.\\n\\n2. Verify the state-specific statute and forum.\\n\\n3. Map each fact to documents and witnesses.\\n\\n4. Open the full judgment and verify paragraphs and later treatment."))
        warning=QLabel("Legal verification required: statutes may be amended; judgments may be distinguished or overruled. Check jurisdiction, limitation, transition rules and current law before filing."); warning.setWordWrap(True); warning.setStyleSheet("background:#fff4dc;color:#825711;border-radius:8px;padding:12px;font-size:11px;font-weight:600"); r.addWidget(warning)
        row2=QHBoxLayout(); row2.addWidget(left,3); row2.addWidget(right,2); self.content_l.addLayout(row2)
        panel,p=self.panel("Search the library","Find terms across Acts, case summaries and issue guides.")
        q=QLineEdit(); q.setPlaceholderText("e.g. mutation, possession, partition, evidence…"); go=btn("Search legal issues",True); go.clicked.connect(lambda:self.go_search(q.text()))
        p.addWidget(q); p.addWidget(go); self.content_l.addWidget(panel)
    def go_search(self,q):
        self.nav.setCurrentRow(1); self.show_page("Legal Issues"); self.guide_search.setText(q)
    def open_guide(self,title):
        self.nav.setCurrentRow(1)
        self.show_page("Legal Issues")
        if hasattr(self,"guide_search"):
            self.guide_search.setText(title)
            for i in range(self.guide_list.count()):
                item=self.guide_list.item(i)
                if title.lower() in item.text().split("\\n")[0].lower():
                    self.guide_list.setCurrentItem(item)
                    self.detail_guide(item.data(Qt.ItemDataRole.UserRole))
                    break
    def guides_page(self):
        row=QHBoxLayout(); self.guide_search=QLineEdit(); self.guide_search.setPlaceholderText("Search issue, remedy, document, keyword…"); row.addWidget(self.guide_search,1); self.content_l.addLayout(row)
        split=QSplitter(Qt.Orientation.Horizontal); self.guide_list=QListWidget(); self.guide_list.setStyleSheet(f"QListWidget{{background:white;border:1px solid {BORDER};border-radius:12px;padding:6px}} QListWidget::item{{padding:12px;color:{INK};border-radius:7px}} QListWidget::item:selected{{background:#eaf0ff;color:#244dd0}}")
        self.guide_view=QTextBrowser(); self.guide_view.setOpenExternalLinks(True); self.guide_view.setStyleSheet(f"background:white;border:1px solid {BORDER};border-radius:12px;padding:12px")
        split.addWidget(self.guide_list); split.addWidget(self.guide_view); split.setStretchFactor(0,1); split.setStretchFactor(1,2); self.content_l.addWidget(split,1)
        self.guide_search.textChanged.connect(self.fill_guides); self.guide_list.currentItemChanged.connect(lambda cur,old:self.detail_guide(cur.data(Qt.ItemDataRole.UserRole)) if cur else None)
        self.fill_guides()
    def fill_guides(self):
        self.guide_list.clear()
        for r in db.query_all("guides",self.guide_search.text()):
            it=QListWidgetItem(r["title"]+"\\n"+r["category"]); it.setData(Qt.ItemDataRole.UserRole,r); self.guide_list.addItem(it)
        if self.guide_list.count(): self.guide_list.setCurrentRow(0)
        else: self.guide_view.clear()
    def detail_guide(self,r):
        if not r or not hasattr(self,"guide_view"): return
        def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\\n","<br>")
        self.guide_view.setHtml(f"<h2>{esc(r['title'])}</h2><p style='color:#718099'><b>{esc(r['category'])}</b></p><h3>When this issue arises</h3><p>{esc(r['when_text'])}</p><h3>Evidence checklist</h3><p>{esc(r['checklist'])}</p><h3>Research path</h3><p>{esc(r['research'])}</p><h3>Case-law leads</h3><p>{esc(r['cases'])}</p><h3>Caution</h3><p style='background:#fff4dc;padding:10px'>{esc(r['warning'])}</p>")
    def library_page(self,table):
        iscase=table=="cases"; panel,l=self.panel("Searchable "+("case-law library" if iscase else "statute library"),"Open source links and verify the full text before relying on an entry.")
        search=QLineEdit(); search.setPlaceholderText("Search cases, citations, topics…" if iscase else "Search statutes, category, jurisdiction…"); l.addWidget(search)
        tw=QTableWidget(); tw.setColumnCount(4); tw.setHorizontalHeaderLabels(["Case / citation","Court / year","Topics","Details"] if iscase else ["Act / statute","Category","Jurisdiction","Details"]); tw.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); tw.verticalHeader().setVisible(False); tw.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); tw.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); l.addWidget(tw,1); self.content_l.addWidget(panel,1)
        def fill():
            rows=db.query_all(table,search.text()); tw.setRowCount(len(rows))
            for i,r in enumerate(rows):
                vals=[r["title"]+" · "+r["citation"],r["court"]+" · "+r["year"],r["topics"]] if iscase else [r["title"],r["category"],r["jurisdiction"]]
                for j,v in enumerate(vals): tw.setItem(i,j,QTableWidgetItem(v))
                b=QPushButton("View"); b.clicked.connect(lambda checked=False,x=r:self.show_record(table,x)); tw.setCellWidget(i,3,b)
        search.textChanged.connect(fill); fill()
    def bare_acts_page(self):
        self.content_l.addWidget(BareActsWidget(self),1)
    def show_record(self,table,r):
        if table=="cases":
            fields=[("Citation",r["citation"]),("Court / year",r["court"]+" · "+r["year"]),("Topics",r["topics"]),("Principle",r["principle"]),("Caution",r["caution"]),("Source",r["url"])]
            url=r["url"]; label="Open judgment"
        else:
            local_file = Path(__file__).resolve().parent.parent / "bare_acts" / r.get("local_file", "")
            pdf_url = r.get("pdf_url", "")
            fields=[("Category",r["category"]),("Jurisdiction",r["jurisdiction"]),("Summary",r["summary"]),("Verification status",r["status"]),("Official source",r["source"]),("Bundled/local copy", str(local_file) if local_file.exists() else "No local PDF currently bundled. Run download-bare-acts.ps1 to fetch available official PDFs into the app folder.")]
            d=DetailDialog(r["title"],fields,self)
            if local_file.exists():
                b=btn("Open local bare Act PDF",True); b.clicked.connect(lambda p=str(local_file):webbrowser.open(Path(p).resolve().as_uri()))
            else:
                online_url = pdf_url if pdf_url.lower().endswith(".pdf") else r["source"]
                b=btn("Open official bare Act / PDF"); b.clicked.connect(lambda checked=False, u=online_url: webbrowser.open(u) if isinstance(u, str) and u.startswith(("http://", "https://")) else None)
            d.layout().insertWidget(d.layout().count()-1,b)
            source_btn=btn("Open official Act page"); source_btn.clicked.connect(lambda checked=False, u=r["source"]: webbrowser.open(u) if isinstance(u, str) and u.startswith(("http://", "https://")) else None); d.layout().insertWidget(d.layout().count()-1,source_btn)
            d.exec(); return
        d=DetailDialog(r["title"],fields,self); b=btn(label); b.clicked.connect(lambda:webbrowser.open(url)); d.layout().insertWidget(d.layout().count()-1,b); d.exec()
    def evidence_page(self):
        row=QHBoxLayout(); self.ev_issue=QComboBox(); self.ev_issue.addItems([r["title"] for r in db.query_all("guides")]); row.addWidget(QLabel("Issue")); row.addWidget(self.ev_issue,1); self.content_l.addLayout(row)
        self.ev_text=QTextBrowser(); self.ev_text.setStyleSheet(f"background:white;border:1px solid {BORDER};border-radius:12px;padding:15px"); self.content_l.addWidget(self.ev_text,1)
        copy=btn("Copy checklist"); copy.clicked.connect(lambda:QApplication.clipboard().setText(self.ev_text.toPlainText())); self.content_l.addWidget(copy,0,Qt.AlignmentFlag.AlignRight)
        self.ev_issue.currentTextChanged.connect(self.refresh_evidence); self.refresh_evidence()
    def refresh_evidence(self):
        r=next((x for x in db.query_all("guides") if x["title"]==self.ev_issue.currentText()),None)
        if r: self.ev_text.setPlainText(f"{r['title']}\\n\\nWHEN\\n{r['when_text']}\\n\\nDOCUMENTS AND EVIDENCE\\n{r['checklist']}\\n\\nRESEARCH PATH\\n{r['research']}\\n\\nCASE-LAW LEADS\\n{r['cases']}\\n\\nCAUTION\\n{r['warning']}")
    def notes_page(self):
        top=QHBoxLayout(); new=btn("＋ New matter note",True); new.clicked.connect(self.new_note); exp=btn("Export notes JSON"); exp.clicked.connect(self.export_notes); top.addWidget(new); top.addWidget(exp); top.addStretch(); self.content_l.addLayout(top)
        self.notes_table=QTableWidget(); self.notes_table.setColumnCount(5); self.notes_table.setHorizontalHeaderLabels(["Matter","State","Issue","Stage","Actions"]); self.notes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.notes_table.verticalHeader().setVisible(False); self.notes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.content_l.addWidget(self.notes_table,1); self.refresh_notes()
    def refresh_notes(self):
        rows=db.list_notes(); self.notes_table.setRowCount(len(rows))
        for i,n in enumerate(rows):
            for j,k in enumerate(["title","state","issue","stage"]): self.notes_table.setItem(i,j,QTableWidgetItem(n[k]))
            w=QWidget(); h=QHBoxLayout(w); h.setContentsMargins(2,2,2,2); e=QPushButton("Open / edit"); d=QPushButton("Delete"); e.clicked.connect(lambda checked=False,x=n:self.edit_note(x)); d.clicked.connect(lambda checked=False,x=n["id"]:self.delete_note(x)); h.addWidget(e); h.addWidget(d); self.notes_table.setCellWidget(i,4,w)
    def new_note(self):
        d=NoteDialog(parent=self)
        if d.exec()==QDialog.DialogCode.Accepted:
            n=d.value()
            if not n["title"]: QMessageBox.warning(self,"Title required","Enter a matter title."); return
            db.save_note(n); self.refresh_notes()
    def edit_note(self,n):
        d=NoteDialog(n,self)
        if d.exec()==QDialog.DialogCode.Accepted:
            x=d.value()
            if not x["title"]: QMessageBox.warning(self,"Title required","Enter a matter title."); return
            db.save_note(x,n["id"]); self.refresh_notes()
    def delete_note(self,ident):
        if QMessageBox.question(self,"Delete note","Delete this local matter note?")==QMessageBox.StandardButton.Yes: db.delete_note(ident); self.refresh_notes()
    def export_notes(self):
        p,_=QFileDialog.getSaveFileName(self,"Export matter notes","land_law_matter_notes.json","JSON files (*.json)")
        if p: Path(p).write_text(json.dumps(db.list_notes(),ensure_ascii=False,indent=2),encoding="utf-8"); QMessageBox.information(self,"Export complete","Matter notes exported.")
    def about_page(self):
        panel,l=self.panel("About this application","Local-first research aid for agricultural land litigation in Punjab and Haryana.")
        l.addWidget(QLabel("The app organizes topics, statute references, starter judgments, issue guides and evidence checklists. It does not determine title or replace advice from a qualified advocate."))
        for title,desc,url in [("Haryana Revenue Department — Acts, Rules & Manuals","Official state portal for revenue and related legislation.","https://revenueharyana.gov.in/acts-rules-manuals/"),("India Code","Official central legislation portal.","https://www.indiacode.nic.in/"),("Anathula Sudhakar judgment","Full judgment on injunction suits, possession and title.","https://indiankanoon.org/doc/540361/")]:
            h=QLabel(title); h.setStyleSheet("font-size:14px;font-weight:800"); l.addWidget(h); d=QLabel(desc); d.setWordWrap(True); d.setStyleSheet("color:#6f7e94"); l.addWidget(d); b=QPushButton("Open source"); b.clicked.connect(lambda checked=False,u=url:webbrowser.open(u)); l.addWidget(b)
        warn=QLabel("LEGAL VERIFICATION REQUIRED: Check current statutory text, amendments, state applicability, limitation, forum and later treatment of cases. For conduct/proceedings around 1 July 2024, review BNS/BNSS/BSA alongside IPC/CrPC/Indian Evidence Act and all transition/savings provisions."); warn.setWordWrap(True); warn.setStyleSheet("background:#fff3dc;color:#825711;border-radius:9px;padding:14px;font-weight:600"); l.addWidget(warn); self.content_l.addWidget(panel)
def main():
    db.initialize(); app=QApplication(sys.argv); app.setStyle("Fusion"); app.setFont(QFont("Segoe UI",10)); w=MainWindow(); w.show(); sys.exit(app.exec())
if __name__=="__main__": main()

