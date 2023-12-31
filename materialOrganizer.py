from functools import partial
from Qt import QtCore, QtGui, QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
import maya.cmds as cmds

import sys

#TO RUN: 
# import importlib
# import materialSets
# importlib.reload(materialSets)

# ui = materialSets.MaterialToolsDialog()
# ui.show_dialog()

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class ColorButton(QtWidgets.QLabel):

    color_changed = QtCore.Signal()

    def __init__(self, color=QtCore.Qt.white, parent=None):
        super(ColorButton, self).__init__(parent)

        self._color = QtGui.QColor()

        self.set_size(50, 14)
        self.set_color(color)

    def set_size(self, width, height):
        self.setFixedSize(width, height)
    
    def set_color(self, color):
        color = QtGui.QColor(color)
        
        if self._color != color:
            self._color = color
            
            pixmap = QtGui.QPixmap(self.size())
            pixmap.fill(self._color)
            self.setPixmap(pixmap)

            self.color_changed.emit()

    def get_color(self):
        return  self._color
    
    def select_color(self):
        color = QtWidgets.QColorDialog.getColor(self.get_color(), self, options=QtWidgets.QColorDialog.DontUseNativeDialog)
        if color.isValid():
            self.set_color(color)
    
    def mouseReleaseEvent(self, mouse_event):
        if mouse_event.button() == QtCore.Qt.LeftButton:
            self.select_color()

class CollapsibleHeader(QtWidgets.QWidget):

    COLLAPSED_PIXMAP = QtGui.QPixmap(":teRightArrow.png")
    EXPANDED_PIXMAP = QtGui.QPixmap(":teDownArrow.png")

    clicked = QtCore.Signal()

    def __init__(self, text, parent=None):
        super(CollapsibleHeader, self).__init__(parent)
        
        self.setAutoFillBackground(True)
        self.set_background_color()

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedWidth(self.COLLAPSED_PIXMAP.width())

        self.text_label = QtWidgets.QLabel()

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.addWidget(self.icon_label)
        self.main_layout.addWidget(self.text_label)

        self.set_text(text)
        self.set_expanded(False)

    def set_text(self, text):
        self.text_label.setText("&nbsp;&nbsp;&nbsp;&nbsp;<b>{0}</b>".format(text))
    
    def set_background_color(self):
        color = QtWidgets.QPushButton().palette().color(QtGui.QPalette.Button)
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, color)
        self.setPalette(palette)
    
    def is_expanded(self):
        return self._expanded
    
    def set_expanded(self, expanded):
        self._expanded = expanded

        if self._expanded:
            self.icon_label.setPixmap(self.EXPANDED_PIXMAP)
        else:
            self.icon_label.setPixmap(self.COLLAPSED_PIXMAP)
    
    def mouseReleaseEvent(self, event):
        self.clicked.emit()

class CollapsibleWidget(QtWidgets.QWidget):

    def __init__(self, text, parent=None):
        super(CollapsibleWidget, self).__init__(parent)

        self.header_wdg = CollapsibleHeader(text)
        self.header_wdg.clicked.connect(self.on_header_clicked)
        self.body_wdg = QtWidgets.QWidget()

        self.body_layout = QtWidgets.QVBoxLayout(self.body_wdg)
        self.body_layout.setContentsMargins(4, 2, 4, 2)
        self.body_layout.setSpacing(3)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.header_wdg)
        self.main_layout.addWidget(self.body_wdg)

        self.set_expanded(False)

    def add_widget(self, widget):
        self.body_layout.addWidget(widget)

    def add_layout(self, layout):
        self.body_layout.addLayout(layout)

    def set_expanded(self, expanded):
        self.header_wdg.set_expanded(expanded)
        self.body_wdg.setVisible(expanded)
 
    def on_header_clicked(self):
        self.set_expanded(not self.header_wdg.is_expanded())

class CreateMaterialWidget(QtWidgets.QWidget):

    MATERIAL_TYPES = [
                      ["aiStandardSurface", "baseColor"], 
                      ["lambert", "color"],
                      ["blinn", "color"],
                      ["phong", "color"],
                      ["standardSurface", "baseColor"]
                     ]

    def __init__(self, parent=None):
        super(CreateMaterialWidget, self).__init__(parent)
    
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        self.material_name_le = QtWidgets.QLineEdit()
        self.materials_combo_box = QtWidgets.QComboBox()

        combo_items = []
        for material in self.MATERIAL_TYPES:
            combo_items.append(material[0])

        self.materials_combo_box.addItems(combo_items)
        self.color_button = ColorButton(QtCore.Qt.white)
        self.assign_cb = QtWidgets.QCheckBox()
        self.create_material_btn = QtWidgets.QPushButton("Create Material")
    
    def create_layouts(self):
        material_layout = QtWidgets.QFormLayout()
        material_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        material_layout.setFormAlignment(QtCore.Qt.AlignLeft)
        material_layout.addRow("Material Name", self.material_name_le)
        material_layout.addRow("Material Type", self.materials_combo_box)
        material_layout.addRow("Base Color", self.color_button)
        material_layout.addRow("Assign to Selected", self.assign_cb)
        
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.create_material_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 10, 4, 10)
        main_layout.setSpacing(8)
        
        main_layout.addLayout(material_layout)
        main_layout.addLayout(btn_layout)
    
    def create_connections(self):
        self.create_material_btn.clicked.connect(self.create_material)

    def create_material(self, selection=False):

        material_name = self.material_name_le.text()
        node_type = self.materials_combo_box.currentText()
        base_color = self.color_button.get_color()
        selected = cmds.ls(selection=True)
        attr = ""

        for material in self.MATERIAL_TYPES:
            if node_type == material[0]:
                attr = ".{0}".format(material[1])

        if not material_name: 
            return
        
        material, sg = self.create_shader(material_name, node_type, base_color, attr)

        if self.assign_cb.isChecked():
            cmds.sets(selected, forceElement=sg)

        self.material_name_le.setText("")

    def create_shader(self, name, node_type, base_color, attr):
        material = cmds.shadingNode(node_type, name=name, asShader=True)
        print(base_color.blue())

        sg = cmds.sets(name="%sSG" % name, empty=True, renderable=True, noSurfaceShader=True)
        cmds.setAttr("{0}{1}".format(name, attr), float(base_color.red() / 255), float(base_color.green() / 255), float(base_color.blue() / 255), type='double3')
       
        cmds.connectAttr("%s.outColor" % material, "%s.surfaceShader" % sg)
        return material, sg

class ViewMaterialsTable(QtWidgets.QDialog):
    
    ATTR_ROLE = QtCore.Qt.UserRole
    VALUE_ROLE = QtCore.Qt.UserRole + 1

    def __init__(self, parent=None):
        super(ViewMaterialsTable, self).__init__(parent)
    
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        self.material_table = QtWidgets.QTableWidget()
        self.material_table.setColumnCount(2)
        self.material_table.setHorizontalHeaderLabels(["Name", "Type"])

        self.select_assigned_btn = QtWidgets.QPushButton("Select")
        self.assign_selected_btn = QtWidgets.QPushButton("Assign")
        self.refresh_btn = QtWidgets.QPushButton("Refresh")

    def create_layouts(self):
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.select_assigned_btn)
        btn_layout.addWidget(self.assign_selected_btn)
        btn_layout.addWidget(self.refresh_btn)
    
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 2, 4, 2)
        main_layout.setSpacing(2)
        main_layout.addWidget(self.material_table)
        main_layout.addLayout(btn_layout)
    
    def create_connections(self):
        self.set_cell_changed_connection_enabled(True)
        self.material_table.cellClicked.connect(self.on_cell_clicked)
        self.refresh_btn.clicked.connect(self.refresh_table)
        self.select_assigned_btn.clicked.connect(self.select_assigned)
        self.assign_selected_btn.clicked.connect(self.assign_selected)

    def set_cell_changed_connection_enabled(self, enabled):
        if enabled: 
            self.material_table.cellChanged.connect(self.on_cell_changed)
        else:
            self.material_table.cellChanged.disconnect(self.on_cell_changed)

    def showEvent(self, e):
        super(ViewMaterialsTable, self).showEvent(e)
        self.refresh_table()

    def keyPressEvent(self, e):
        super(ViewMaterialsTable, self).keyPressEvent(e)
        e.accept()
    
    def refresh_table(self):
        self.set_cell_changed_connection_enabled(False)

        self.material_table.setRowCount(0)

        materials = cmds.ls(mat=True)
        print(materials)
        for i in range(len(materials)):
            material_name = materials[i]
            material_type = cmds.nodeType(materials[i])

            self.material_table.insertRow(i)
            self.insert_item(i, 0, material_name, None, material_name, True)
            self.insert_item(i, 1, material_type, "nodeType", material_type, False)
        
        self.set_cell_changed_connection_enabled(True)

    def insert_item(self, row, column, text, attr, value, editable):
        item = QtWidgets.QTableWidgetItem(text)
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        
        self.set_item_attr(item, attr)
        self.set_item_value(item, value)

        if not editable:
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            
        self.material_table.setItem(row, column, item)
    
    def on_cell_clicked(self):
        curr_row = self.material_table.currentRow()
        selected_mat = self.material_table.item(curr_row, 0).text()
        print(selected_mat)
        cmds.select(selected_mat)

    def on_cell_changed(self, row, column):
        self.set_cell_changed_connection_enabled(False)

        item = self.material_table.item(row, column)
        self.rename(item)

        self.set_cell_changed_connection_enabled(True)
    
    def rename(self, item):
        old_name = self.get_item_value(item)
        new_name = self.get_item_text(item)

        if old_name != new_name:
            actual_new_name = cmds.rename(old_name, new_name)
            if actual_new_name != new_name:
                self.set_item_text(item, actual_new_name)
            
            self.set_item_value(item, actual_new_name)

    def set_item_text(self, item, text):
        item.setText(text)
    
    def get_item_text(self, item):
        return item.text()
    
    def set_item_attr(self, item, attr):
        item.setData(self.ATTR_ROLE, attr)
    
    def get_item_attr(self, item, attr):
        return item.data(self.ATTR_ROLE)
    
    def set_item_value(self, item, value):
        item.setData(self.VALUE_ROLE, value)

    def get_item_value(self, item):
        return item.data(self.VALUE_ROLE)

    def assign_selected(self):
        curr_row = self.material_table.currentRow()
        selected_mat = self.material_table.item(curr_row, 0).text()
        cmds.hyperShade(a=selected_mat)

    def select_assigned(self):
        print(cmds.hyperShade(objects=""))

class MaterialToolsDialog(QtWidgets.QDialog):
    
    ATTR_ROLE = QtCore.Qt.UserRole
    VALUE_ROLE = QtCore.Qt.UserRole + 1

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = MaterialToolsDialog()
        
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()
    
    def __init__(self, parent=maya_main_window()):
        super(MaterialToolsDialog, self).__init__(parent)

        self.setWindowTitle("Material Tools")
        self.setMinimumSize(500, 300)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        
        self.geometry = None

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        self.body_wdg = QtWidgets.QWidget()
        self.create_mat_wdg = CreateMaterialWidget()
        self.view_materials_table = ViewMaterialsTable()

        self.table_wdg = QtWidgets.QTableWidget()
        self.table_wdg.setColumnCount(2)
        self.table_wdg.setHorizontalHeaderLabels(["Mesh Name", "Material"])
        header_view = self.table_wdg.horizontalHeader()

        self.table_wdg.setColumnWidth(1, 200)
        header_view.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header_view.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        self.check_uvs_btn = QtWidgets.QPushButton("Check for Missing UVs")
        self.auto_layout_uvs_btn = QtWidgets.QPushButton("Auto Layout UVs")

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.close_btn = QtWidgets.QPushButton("Close")

        self.create_mat_collapsible_wdg = CollapsibleWidget("Create Material")
        self.create_mat_collapsible_wdg.add_widget(self.create_mat_wdg)

        self.view_materials_collapsible_wdg = CollapsibleWidget("View Materials")
        self.view_materials_collapsible_wdg.add_widget(self.view_materials_table)

        self.mat_table_collapsible_wdg = CollapsibleWidget("Assigned Materials")
        self.mat_table_collapsible_wdg.add_widget(self.table_wdg)

        self.uv_tools_collapsible_wdg = CollapsibleWidget("Check & Export UVs")

    def create_layouts(self):
        uv_btn_layout = QtWidgets.QHBoxLayout()
        uv_btn_layout.setSpacing(2)

        uv_btn_layout.addWidget(self.check_uvs_btn)
        uv_btn_layout.addWidget(self.auto_layout_uvs_btn)

        self.uv_tools_collapsible_wdg.add_layout(uv_btn_layout)

        btm_btn_layout = QtWidgets.QHBoxLayout()
        btm_btn_layout.setSpacing(2)
        btm_btn_layout.addStretch()

        btm_btn_layout.addWidget(self.refresh_btn)
        btm_btn_layout.addWidget(self.close_btn)

        self.body_layout = QtWidgets.QVBoxLayout(self.body_wdg)
        self.body_layout.setContentsMargins(4, 2, 4, 2)
        self.body_layout.setSpacing(3)
        self.body_layout.setAlignment(QtCore.Qt.AlignTop)

        self.body_layout.addWidget(self.create_mat_collapsible_wdg)
        self.body_layout.addWidget(self.view_materials_collapsible_wdg)
        self.body_layout.addWidget(self.mat_table_collapsible_wdg)
        self.body_layout.addWidget(self.uv_tools_collapsible_wdg)
        self.body_layout.addLayout(btm_btn_layout)

        self.body_scroll_area = QtWidgets.QScrollArea()
        self.body_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.body_scroll_area.setWidgetResizable(True)
        self.body_scroll_area.setWidget(self.body_wdg)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.body_scroll_area)
        
    def create_connections(self):
        self.check_uvs_btn.clicked.connect(self.check_uvs)
        self.auto_layout_uvs_btn.clicked.connect(self.auto_layout_uvs)
        self.refresh_btn.clicked.connect(self.refresh_table)
        self.close_btn.clicked.connect(self.close)

    def refresh_table(self):
        self.table_wdg.setRowCount(0)
        
        meshes = cmds.ls(type="mesh")
        materials = cmds.ls(mat=True)
        for i in range(len(meshes)):
            transform_name = cmds.listRelatives(meshes[i], parent=True)[0]

            curr_material = self.get_curr_material(meshes[i])
            curr_index = materials.index(curr_material)
            combo_box = QtWidgets.QComboBox()
            combo_box.addItems(materials)
            combo_box.setCurrentIndex(curr_index)
            combo_box.currentTextChanged.connect(partial(self.on_combo_change, mesh=transform_name))
    
            self.table_wdg.insertRow(i)
            self.insert_item(i, 0, transform_name, None, transform_name)
            self.table_wdg.setCellWidget(i, 1, combo_box)

    def on_combo_change(self, value, mesh):
        cmds.select(mesh)
        print(mesh)
        cmds.hyperShade(a=value)

    def insert_item(self, row, column, text, attr, value):
        item = QtWidgets.QTableWidgetItem("{0}{1}".format("  ", text))
        self.set_item_attr(item, attr)
        self.set_item_value(item, value)

        self.table_wdg.setItem(row, column, item)

    def get_curr_material(self, mesh):
        cmds.select(mesh)
        nodes = cmds.ls(sl=True, dag=True, s=True)
        shade_eng = cmds.listConnections(nodes, type='shadingEngine')
        mats = cmds.ls(cmds.listConnections(shade_eng), materials=True)

        return mats[0]

    def set_item_text(self, item, text):
        item.setText(text)
    
    def get_item_text(self, item, text):
        return item.text()
    
    def set_item_attr(self, item, attr):
        item.setData(self.ATTR_ROLE, attr)

    def get_item_attr(self, item):
        return item.data(self.ATTR_ROLE)
    
    def set_item_value(self, item, value):
        item.setData(self.VALUE_ROLE, value)
    
    def get_item_value(self, item):
        return item.data(self.VALUE_ROLE)
    
    def check_uvs(self):
        meshes = cmds.ls(type="mesh")
        uvs_good = True
        bad_uvs = []

        for mesh in meshes:
            if cmds.polyEvaluate(mesh, uvShell=True) == 0:
                uvs_good = False
                print("Mesh {0} has no uv shells!".format(mesh))
                bad_uvs.append(mesh)
        
        if uvs_good:
            print("All meshes have uv shells")
            QtWidgets.QMessageBox.information(self, "UVs Checked", "All meshes have UV shells")
        else: 
            print("There are some meshes without uv shells")
            QtWidgets.QMessageBox.warning(self, "Missing UVs", "The following meshes are missing UV shells: {0}".format(bad_uvs))


    def auto_layout_uvs(self):
        meshes = cmds.ls(type="mesh")
        cmds.u3dLayout(meshes, scl=1)

    def showEvent(self, e):
        super(MaterialToolsDialog, self).showEvent(e)

        self.refresh_table()

        if self.geometry: 
            self.restoreGeometry(self.geometry)
    
    def closeEvent(self, e):
        if isinstance(self, MaterialToolsDialog):
            super(MaterialToolsDialog, self).closeEvent(e)
            self.geometry = self.saveGeometry()

if __name__ == "__main__":
    try: 
        material_tools_dialog.close()
        material_tools_dialog.deleteLater()
    except: 
        pass

    material_tools_dialog = MaterialToolsDialog()
    material_tools_dialog.show()
