import pygtk
pygtk.require('2.0')
import gtk
import rpy.robjects as robjects



class LibraryPanel(object):

    cell = gtk.CellRendererText()
    cell.set_property('cell-background', 'black')
    cell.set_property('foreground', 'white')
    
    def __init__(self, parent):
        self._table = gtk.ListStore(str, str, str)
        self.updateInstalledLibraries()
        self._treeView = gtk.TreeView(model = self._table)
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
        parent.add(self._treeView)

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

    def show(self):
        self._treeView.show()

class VignetteExplorer(object):

    def __init__(self, parent):
        self._table = gtk.ListStore(str, str, str)
        self.updateKnownVignettes()
        self._treeView = gtk.TreeView(model = self._table)
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
        parent.add(self._treeView)
        self.parent = parent

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
    def show(self):
        self._treeView.show()

class DocumentationExplorer(object):

    def __init__(self, parent):
        self._table = gtk.ListStore(str, str, str)
        self.updateRelevantDoc("foo")
        self._treeView = gtk.TreeView(model = self._table)
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
        parent.add(self._treeView)
        self.parent = parent

    def updateRelevantDoc(self, string):
        self._table.clear()
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
    def show(self):
        self._treeView.show()

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
        vbox_lib = gtk.VBox(homogeneous=False, spacing=0)
        vbox_lib.show()
        sbox_lib = gtk.HBox(homogeneous=False, spacing=0)
        sbox_lib.show()
        sentry_lib = gtk.Entry()
        sentry_lib.show()
        sbox_lib.add(sentry_lib)
        sbutton_lib = gtk.Button("Search")
        sbutton_lib.show()
        sbox_lib.add(sbutton_lib)
        vbox_lib.pack_start(sbox_lib, expand=False, fill=False, padding=0)

        s_window_lib = gtk.ScrolledWindow()
        s_window_lib.set_policy(gtk.POLICY_AUTOMATIC, 
                                gtk.POLICY_AUTOMATIC)
        s_window_lib.show()
        libPanel = LibraryPanel(s_window_lib)
        libPanel.show()
        vbox_lib.add(s_window_lib)
        notebook.append_page(vbox_lib, gtk.Label("Libraries"))

        # vignettes
        vbox_vig = gtk.VBox(homogeneous=False, spacing=0)
        vbox_vig.show()
        sbox_vig = gtk.HBox(homogeneous=False, spacing=0)
        sbox_vig.show()
        sentry_vig = gtk.Entry()
        sentry_vig.show()
        sbox_vig.add(sentry_vig)
        sbutton_vig = gtk.Button("Search")
        sbutton_vig.show()
        sbox_vig.add(sbutton_vig)
        vbox_vig.pack_start(sbox_vig, expand=False, fill=False, padding=0)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, 
                                   gtk.POLICY_AUTOMATIC)
        scrolled_window.show()
        vigPanel = VignetteExplorer(scrolled_window)
        vigPanel.show()
        vbox_vig.add(scrolled_window)
        notebook.append_page(vbox_vig, gtk.Label("Vignettes"))

        # doc
        s_window = gtk.ScrolledWindow()
        s_window.set_policy(gtk.POLICY_AUTOMATIC, 
                                   gtk.POLICY_AUTOMATIC)
        s_window.show()
        docPanel = DocumentationExplorer(s_window)
        docPanel.show()
        notebook.append_page(s_window, gtk.Label("Documentation"))

        # search 
        #window.add(vbox)
        window.add(notebook)

        window.show()

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

w = Main()
gtk.main()


