from PyQt6 import QtCore, QtGui, QtWidgets
from ui.UI_Table import Table
from educ.tablemodel import TableModel, Cell

class WidgetTable(Table):
    cellSelected = QtCore.pyqtSignal()
    cellDeselected = QtCore.pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model: TableModel
        self.sectionPositions: list
        self.selectedCell: None | Cell = None

        self._instantiated = False
        self._row_count: int = 0
        self._column_count: int = 0

        self.grid_widget.resized2.connect(self.on_width_resized)
        self.grid_widget.resized.connect(self.on_height_resized)
        self.hheaders.sectionResized.connect(self.on_section_resized)

    def row_count(self) -> int:
        return self._row_count
    
    def column_count(self) -> int:
        return self._column_count

    def new_table(self, row: int, column: int) -> None:
        data = [[Cell(self) for _ in range(column)] for _ in range(row)]
        model = TableModel(data, self)
        self.set_table(model)
    
    def set_table(self, model: TableModel) -> None:
        self.model = model
        self.hheaders.setModel(self.model)
        self.vheaders.setModel(self.model)
        self.model.rowsInserted.connect(self.updateTable)
        self.model.columnsInserted.connect(self.updateTable)
        self.model.rowsRemoved.connect(self.updateTable)
        self.model.columnsRemoved.connect(self.updateTable)
        self.model.rowsMoved.connect(self.updateTable)
        self.model.columnsMoved.connect(self.updateTable)
        self.updateTable()
        self._instantiated = True
        self._row_count = self.model.rowCount()
        self._column_count = self.model.columnCount()
        print("Instantiated")

    def clear(self) -> None:
        """Removes alls rows and columns."""
        for i in reversed(range(self.grid.count())):
            w = self.grid.takeAt(i).widget()
            self.grid.removeWidget(w)

        # This more efficient remove-algorithm is abandoned because of not working reliably every time.

        # if self._column_count > self.model.column_count():
        #     print("More Columns")
        #     columns_to_delete = self._column_count - self.model.column_count()
        #     for _ in range(columns_to_delete):
        #         for i in reversed(range(self._row_count)):
        #             w = self.grid.itemAtPosition(i, self._column_count-1).widget()
        #             print("Remove", i, self._column_count-1)
        #             self.grid.removeWidget(w)
        #         self._column_count -= 1

        # elif self._row_count > self.model.row_count():
        #     print("More rows")
        #     rows_to_delete = self._row_count - self.model.row_count()
        #     for _ in range(rows_to_delete):
        #         for i in reversed(range(self._column_count)):
        #             w = self.grid.itemAtPosition(self._row_count-1, i).widget()
        #             print("Remove", self._row_count-1, i)
        #             self.grid.removeWidget(w)
        #         self._row_count -= 1

        print(self._row_count, self._column_count, self.grid.count())

    def updateTable(self) -> None:
        """Updates table according to the model."""
        self.clear()
        for irow in range(self.model.rowCount()):
            for icolumn in range(self.model.columnCount()):
                if not self.compare(irow, icolumn):
                    cell = self.model.data(irow, icolumn)
                    self.grid.addWidget(cell, irow, icolumn)
                else:
                    continue

        self.sa_hheaders.horizontalScrollBar().setMaximum(self.horizontalScrollBar().maximum())
        self.sa_vheaders.verticalScrollBar().setMaximum(self.verticalScrollBar().maximum())
        self.sa_hheaders.horizontalScrollBar().setValue(self.horizontalScrollBar().value())
        self.sa_vheaders.verticalScrollBar().setValue(self.verticalScrollBar().value())

        self._row_count = self.model.rowCount()
        self._column_count = self.model.columnCount()

    def compare(self, row: int, column: int) -> bool: # unused
        try:
            table_element = self.grid.itemAtPosition(row, column).widget()
            model_element = self.model.data(row, column)
            if table_element == model_element:
                return True
            else:
                return False
        except AttributeError:
            return False
        
    def on_section_resized(self, section: int, old: int, new: int) -> None:
        self.grid_widget.resized2.disconnect()
        visual_index = self.hheaders.visualIndex(section)
        print("Section", section, visual_index)
        cell = self.model.data(0, visual_index)
        cell.setMinimumWidth(new)
        self.grid_widget.updateGeometry()
        self.hheaders.sectionResized.disconnect()
        self.model.setHeaderData(visual_index, self.hheaders.orientation(), cell.width(), QtCore.Qt.ItemDataRole.SizeHintRole)
        self.hheaders.resizeSection(section, cell.width())
        self.hheaders.sectionResized.connect(self.on_section_resized)
        self.grid_widget.resized2.connect(self.on_width_resized)

    def on_height_resized(self) -> None:
        for i in range(self.model.rowCount()):
            cell = self.model.data(i, 0)
            self.vheaders.resizeSection(self.vheaders.logicalIndex(i) , cell.height())

    def on_width_resized(self) -> None:
        self.hheaders.sectionResized.disconnect()
        for i in range(self.model.columnCount()):
            cell = self.model.data(0, i)
            self.hheaders.resizeSection(self.hheaders.logicalIndex(i), cell.width())
        self.hheaders.sectionResized.connect(self.on_section_resized)

    # @QtCore.pyqtSlot(bool)
    # def setResizing(self, on: bool) -> None:
    #     print("Resizing signal received")
    #     self._resizing = on

    def resizing(self) -> bool:
        return self._resizing

    def newRow(self) -> None:
        if self.hasSelectedCell():
            self.model.insert_row(self.grid.getItemPosition(self.grid.indexOf(self.selectedCell))[0]+1)
            self.updateTable()

    def newColumn(self) -> None:
        if self.hasSelectedCell():
            self.model.insert_column(self.grid.getItemPosition(self.grid.indexOf(self.selectedCell))[1]+1)
            self.resize(self.width()+100, self.height())
            self.updateTable()           

    def removeRow(self) -> None:
        if self.hasSelectedCell():
            self.model.remove_row(self.grid.getItemPosition(self.grid.indexOf(self.selectedCell))[0]) 
            self.setSelectedCell(self.selectedCell)
            self.updateTable()            

    def removeColumn(self) -> None:
        if self.hasSelectedCell():
            self.model.remove_column(self.grid.getItemPosition(self.grid.indexOf(self.selectedCell))[1])
            self.setSelectedCell(self.selectedCell)
            self.updateTable()

    def add_element(self, element) -> None:
        if self.hasSelectedCell():
            self.selectedCell.layout().addWidget(element)
            self.setSelectedCell(self.selectedCell)

    def delete_element(self, element) -> None:
        element.setParent(None)
        element.destroy()
        element.deleteLater()

    def setSelectedCell(self, cell: Cell|None) -> None:
        if isinstance(cell, Cell):
            if cell == self.selectedCell:
                self.selectedCell.setSelected(False)
                self.selectedCell = None
            elif self.selectedCell != None:
                self.selectedCell.setSelected(False)
                cell.setSelected(True)
                self.selectedCell = cell
            else:
                cell.setSelected(True)
                self.selectedCell = cell
        else:
            if self.selectedCell != None:
                self.selectedCell.setSelected(False)  
                self.selectedCell = None            
        self.hasSelectedCell()

    def hasSelectedCell(self) -> bool:
        if self.selectedCell != None:
            self.cellSelected.emit()
            return True
        else:
            self.cellDeselected.emit()
            return False
        
    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        # print("Mouse Pressed")
        pos = e.position()
        print("Mouse Pos", pos.x(), pos.y())
        pos.setX(pos.x() + 30.0)
        pos.setY(pos.y() + 30.0)
        corrected = QtGui.QMouseEvent(e.type(), pos, e.button(), e.buttons(), e.modifiers(), e.device())
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setSelectedCell(self.childAt(corrected.pos()))
        super().mousePressEvent(corrected)