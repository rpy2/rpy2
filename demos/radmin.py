import pygtk
pygtk.require('2.0')
import gtk
import rpy2.robjects as robjects



class LibraryPanel(gtk.VBox):

    cell = gtk.CellRendererText()
    cell.set_property('cell-background', 'black')
    cell.set_property('foreground', 'white')
    
    def __init__(self):
        super(LibraryPanel, self).__init__()
        self._table = gtk.ListStore(str, str, str)
        self.updateInstalledLibraries()
        self._treeView = gtk.TreeView(model = self._table)
        self._treeView.show()
        self._valueColumns = [gtk.TreeViewColumn('Package'),
                              gtk.TreeViewColumn('Installed'),
                              gtk.TreeViewColumn('Available')]
        self._valueCells = []
        for col_i, col in enumerate(self._valueColumns):
            self._treeView.append_column(col)
            cr = gtk.CellRendererText()
            col.pack_start(cr, True)
            self._valueCells.append(cr)
            col.set_attributes(cr, text=col_i)
 
        sbox = gtk.HBox(homogeneous=False, spacing=0)
        sbox.show()
        self.sentry = gtk.Entry()
        self.sentry.show()
        sbox.add(self.sentry)
        sbutton = gtk.Button("Search")
        sbutton.connect("clicked", self.searchAction, "search")
        sbutton.show()
        sbox.add(sbutton)
        self.pack_start(sbox, expand=False, fill=False, padding=0)
        s_window = gtk.ScrolledWindow()
        s_window.set_policy(gtk.POLICY_AUTOMATIC, 
                            gtk.POLICY_AUTOMATIC)
        s_window.show()
        s_window.add(self._treeView)
        self.add(s_window)

    def updateInstalledLibraries(self):
        self._table.clear()
        installedLibraries = robjects.r["installed.packages"]()
        nrows = robjects.r.nrow(installedLibraries)[0]
        ncols = robjects.r.ncol(installedLibraries)[0]
        for i in range(1, nrows._sexp[0]+1):
            row = []
            pack = installedLibraries.subset(i, 1)._sexp[0]
            row.append(pack)
            pack = installedLibraries.subset(i, 3)._sexp[0]
            row.append(pack)
            pack = installedLibraries.subset(i, 4)._sexp[0]
            row.append(pack)
            self._table.append(row)

    def searchAction(self, widget, data=None):
        string = (self.sentry.get_text())
        self.updateInstalledLibraries()
        if string is None:
            return
        matches = robjects.r["help.search"](string).subset("matches")[0]
        spacks = [x for x in matches.subset(True, "Package")._sexp]
        spacks = set(spacks)
        toremove = []
        for ii, row in enumerate(self._table):
            if not (row[0] in spacks):
                toremove.append(ii)
        toremove.reverse()
        for r in toremove:
            self._table.remove(self._table.get_iter(r))


class VignetteExplorer(gtk.VBox):

    def __init__(self):
        super(VignetteExplorer, self).__init__()
        self._table = gtk.ListStore(str, str, str)
        self.updateKnownVignettes()
        self._treeView = gtk.TreeView(model = self._table)
        self._treeView.show()
        self._valueColumns = [gtk.TreeViewColumn('Package'),
                              gtk.TreeViewColumn('Item'),
                              gtk.TreeViewColumn('Title')]
        self._valueCells = []
        for col_i, col in enumerate(self._valueColumns):
            self._treeView.append_column(col)
            cr = gtk.CellRendererText()
            col.pack_start(cr, True)
            self._valueCells.append(cr)
            col.set_attributes(cr, text=col_i)
        sbox = gtk.HBox(homogeneous=False, spacing=0)
        #sbox.show()
        sentry = gtk.Entry()
        sentry.show()
        sbox.add(sentry)
        sbutton = gtk.Button("Search")
        sbutton.show()
        sbox.add(sbutton)
        self.pack_start(sbox, expand=False, fill=False, padding=0)
        s_window = gtk.ScrolledWindow()
        s_window.set_policy(gtk.POLICY_AUTOMATIC, 
                            gtk.POLICY_AUTOMATIC)
        s_window.show()
        s_window.add(self._treeView)
        self.add(s_window)

    def updateKnownVignettes(self):
        self._table.clear()
        vignettes = robjects.r["vignette"]().subset("results")[0]
        nrows = robjects.r.nrow(vignettes)[0]
        ncols = robjects.r.ncol(vignettes)[0]
        for i in range(1, nrows._sexp[0]+1):
            row = []
            pack = vignettes.subset(i, 1)._sexp[0]
            row.append(pack)
            pack = vignettes.subset(i, 3)._sexp[0]
            row.append(pack)
            pack = vignettes.subset(i, 4)._sexp[0]
            row.append(pack)
            self._table.append(row)

class HelpExplorer(gtk.VBox):

    def __init__(self):
        super(HelpExplorer, self).__init__()
        self._table = gtk.ListStore(str, str, str)
        self.updateRelevantHelp(None)
        self._treeView = gtk.TreeView(model = self._table)
        self._treeView.show()
        self._valueColumns = [gtk.TreeViewColumn('Topic'),
                              gtk.TreeViewColumn('Title'),
                              gtk.TreeViewColumn('Package'),]
        self._valueCells = []
        for col_i, col in enumerate(self._valueColumns):
            self._treeView.append_column(col)
            cr = gtk.CellRendererText()
            col.pack_start(cr, True)
            self._valueCells.append(cr)
            col.set_attributes(cr, text=col_i)
        sbox = gtk.HBox(homogeneous=False, spacing=0)
        sbox.show()
        self.sentry = gtk.Entry()
        self.sentry.show()
        sbox.add(self.sentry)
        sbutton = gtk.Button("Search")
        sbutton.connect("clicked", self.searchAction, "search")

        sbutton.show()
        sbox.add(sbutton)
        self.pack_start(sbox, expand=False, fill=False, padding=0)
        s_window = gtk.ScrolledWindow()
        s_window.set_policy(gtk.POLICY_AUTOMATIC, 
                            gtk.POLICY_AUTOMATIC)
        s_window.show()
        s_window.add(self._treeView)
        self.add(s_window)

    def updateRelevantHelp(self, string):
        self._table.clear()
        if string is None:
            return
        matches = robjects.r["help.search"](string).subset("matches")[0]
        #import pdb; pdb.set_trace()
        nrows = robjects.r.nrow(matches)[0]
        ncols = robjects.r.ncol(matches)[0]
        for i in range(1, nrows._sexp[0]+1):
            row = []
            pack = matches.subset(i, 1)._sexp[0]
            row.append(pack)
            pack = matches.subset(i, 2)._sexp[0]
            row.append(pack)
            pack = matches.subset(i, 3)._sexp[0]
            row.append(pack)
            self._table.append(row)

    def searchAction(self, widget, data=None):
         self.updateRelevantHelp(self.sentry.get_text())

class Main(object):

    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        window.set_title("R")
        window.connect("delete_event", self.delete_event)
        window.connect("destroy", self.destroy)
        window.set_size_request(350, 450)

        notebook = gtk.Notebook()
        notebook.set_tab_pos(gtk.POS_LEFT)
        notebook.set_show_tabs(True)
        notebook.show()
        #vbox = gtk.VBox(homogeneous=False, spacing=0)
        #vbox.show()

        # libraries/packages
        libPanel = LibraryPanel()
        libPanel.show()
        notebook.append_page(libPanel, gtk.Label("Libraries"))

        # vignettes
        vigPanel = VignetteExplorer()
        vigPanel.show()
        notebook.append_page(vigPanel, gtk.Label("Vignettes"))

        # doc
        docPanel = HelpExplorer()
        docPanel.show()
        notebook.append_page(docPanel, gtk.Label("Documentation"))

        window.add(notebook)

        window.show()

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

w = Main()
gtk.main()


