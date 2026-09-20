import pytest
from nativeelements.baseelement import BaseElementModel
from PyQt6.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    QMimeData,
    QModelIndex,
    QSize,
    Qt,
    QXmlStreamWriter,
)
from tcha.resmanager import ResourceObject, ResourceType


# Mock BaseElementModel for testing
class MockElementModel(BaseElementModel):
    """Mock implementation of BaseElementModel for testing."""

    def __init__(self, width=100, height=30, number=0, parent=None):
        super().__init__(parent)
        self._item_size = QSize(width, height)
        self._num = number

    def recalculate_size(self, width: int) -> None:
        """Recalculate size based on width."""
        self._item_size = QSize(width, self._item_size.height())

    def xml(self, writer: QXmlStreamWriter) -> QXmlStreamWriter:
        """Mock XML serialization."""
        writer.writeStartElement("mock")
        writer.writeAttribute("number", str(self.number))
        writer.writeEndElement()
        return writer

    @classmethod
    def from_mime_data(cls, resobj: ResourceObject, mime_data: QMimeData):
        """Mock from_mime_data."""
        return cls()

    @classmethod
    def from_bytes(cls, resobj: ResourceObject, bytearr: QByteArray):
        """Mock from_bytes."""
        return cls()

    @property
    def name(self) -> str:
        return "MockElement"

    @staticmethod
    def restype() -> ResourceType:
        """Returns the ResourceType used for the ResourceObject"""
        return ResourceType.NoResource

    def delegate(self, toolset, parent=None):
        """Mock delegate."""
        return

    def sizeHint(self, width: int) -> QSize:
        return QSize(width, 30)

    def presentable_item(self):
        """Mock presentable_item."""
        return

    @property
    def toolset(self) -> str:
        return "mock_toolset"

    def shcopy(self):
        """Creates a shallow copy of the model."""
        return MockElementModel(self._item_size.width(), self._item_size.height(), self._num)

    def attrs(self) -> tuple[str]:
        return tuple()  # noqa: C408

    @staticmethod
    def definitions():
        """Mock definitions."""
        return

    def to_byte_array(self) -> QByteArray:
        """Mock to_byte_array."""
        return QByteArray()

    def close(self) -> None:
        return


# Import after mocks
from tcha.tablemodel import (
    TCHA_IDENTIFIER,
    CellItem,
    CellModel,
    HeaderDataItem,
    MimeData,
    TableModel,
    decode_mime_data,
)


class TestHeaderDataItem:
    def test_horizontal_header_creation(self):
        """Test creating a horizontal header item."""
        header = HeaderDataItem.horizontal(0)
        assert header.visual_index == 0
        assert header.orientation == Qt.Orientation.Horizontal
        assert header.section_size == 100
        assert header.editable is True
        assert header.text == ""

    def test_vertical_header_creation(self):
        """Test creating a vertical header item."""
        header = HeaderDataItem.vertical(2)
        assert header.visual_index == 2
        assert header.orientation == Qt.Orientation.Vertical
        assert header.section_size == 30
        assert header.editable is False
        assert header.text == ""

    def test_custom_header_creation(self):
        """Test creating a custom header item."""
        header = HeaderDataItem(
            visual_index=5,
            orientation=Qt.Orientation.Horizontal,
            section_size=150,
            editable=False,
            text="Custom Header",
        )
        assert header.visual_index == 5
        assert header.section_size == 150
        assert header.editable is False
        assert header.text == "Custom Header"


class TestCellItem:
    """Test suite for CellItem class."""

    @pytest.fixture
    def horizontal_header(self):
        """Fixture providing a horizontal header."""
        return HeaderDataItem.horizontal(0)

    @pytest.fixture
    def cell_item(self, horizontal_header):
        """Fixture providing a basic CellItem."""
        return CellItem(horizontal_header, num=1)

    def test_cell_item_initialization(self, horizontal_header):
        """Test CellItem initialization."""
        cell = CellItem(horizontal_header, num=1)
        assert len(cell) == 0
        assert cell.num == 1
        assert cell.header == horizontal_header
        assert cell.width == horizontal_header.section_size - 9

    def test_cell_item_requires_horizontal_header(self):
        """Test that CellItem raises error for non-horizontal header."""
        vertical_header = HeaderDataItem.vertical(0)
        with pytest.raises(ValueError, match="horizontal orientation"):
            CellItem(vertical_header, num=1)

    def test_append_element_model(self, cell_item):
        """Test appending an element model to cell."""
        model = MockElementModel(number=0)
        cell_item.append(model)
        assert len(cell_item) == 1
        assert cell_item[0] == model
        assert model.number == 1  # Should be auto-numbered

    def test_append_invalid_type_raises_error(self, cell_item):
        """Test that appending non-BaseElementModel raises TypeError."""
        with pytest.raises(TypeError, match="BaseElementModel"):
            cell_item.append("not a model")

    def test_insert_element_model(self, cell_item):
        """Test inserting an element model."""
        model1 = MockElementModel(number=1)
        model2 = MockElementModel(number=0)
        cell_item.append(model1)
        cell_item.insert(0, model2)
        assert len(cell_item) == 2
        assert cell_item[0] == model2
        assert cell_item[1] == model1

    def test_insert_invalid_type_raises_error(self, cell_item):
        """Test that inserting non-BaseElementModel raises TypeError."""
        with pytest.raises(TypeError, match="BaseElementModel"):
            cell_item.insert(0, {"not": "a model"})

    def test_height_property_with_elements(self, cell_item):
        """Test height calculation with elements."""
        cell_item.append(MockElementModel(height=30))
        cell_item.append(MockElementModel(height=40))
        expected_height = 30 + 40
        assert cell_item.height >= expected_height

    def test_height_property_empty_cell(self, cell_item):
        """Test height of empty cell."""
        assert cell_item.height == 30  # Default height

    def test_width_property(self, cell_item):
        """Test width calculation."""
        assert cell_item.width == cell_item.header.section_size - 9

    def test_recalculate_items(self, cell_item):
        """Test recalculating item sizes."""
        model = MockElementModel(width=50, height=30)
        cell_item.append(model)
        cell_item.recalculate_items()
        assert model.item_size.width() == cell_item.width

    def test_set_header_item(self, cell_item):
        new_header = HeaderDataItem.horizontal(1)
        new_header.section_size = 200
        cell_item.set_header_item(new_header)
        assert cell_item.header == new_header
        assert cell_item.width == 200 - 9

    def test_copy(self, cell_item):
        model = MockElementModel(number=1)
        cell_item.append(model)
        cell_copy = cell_item.copy()
        assert len(cell_copy) == len(cell_item)
        assert cell_copy[0] is cell_item[0]  # Shallow copy
        assert cell_copy is not cell_item

    def test_row_for_pos(self, cell_item):
        cell_item.append(MockElementModel(height=30))
        cell_item.append(MockElementModel(height=40))
        assert cell_item.row_for_pos(15) == 0
        row = cell_item.row_for_pos(50)
        assert row >= 0


class TestCellModel:
    """Test suite for CellModel class."""

    @pytest.fixture
    def cell_item(self):
        """Fixture providing a CellItem with some data."""
        header = HeaderDataItem.horizontal(0)
        cell = CellItem(header, num=1)
        cell.append(MockElementModel(number=1))
        cell.append(MockElementModel(number=2))
        return cell

    @pytest.fixture
    def mock_table_model(self, qapp):
        """Fixture providing a mock table model."""
        return TableModel.new(2, 2)

    @pytest.fixture
    def cell_model(self, qapp, cell_item, mock_table_model):
        """Fixture providing a CellModel."""
        index = mock_table_model.index(0, 0)
        return CellModel(cell_item, index)

    def test_cell_model_initialization(self, qapp, cell_item, mock_table_model):
        """Test CellModel initialization."""
        index = mock_table_model.index(0, 0)
        model = CellModel(cell_item, index)
        assert model.item == cell_item
        assert len(model.work_item) == len(cell_item)

    def test_row_count(self, cell_model):
        """Test rowCount returns correct count."""
        assert cell_model.rowCount() == 2

    def test_add_model(self, cell_model):
        """Test adding a new model."""
        initial_count = cell_model.rowCount()
        new_model = MockElementModel(number=3)
        cell_model.add_model(new_model)
        assert cell_model.rowCount() == initial_count + 1
        assert cell_model.item[-1] == new_model

    def test_clear(self, cell_model):
        """Test clearing all models."""
        cell_model.clear()
        assert cell_model.rowCount() == 0
        assert len(cell_model.item) == 0

    def test_remove_rows(self, cell_model):
        """Test removing rows."""
        initial_count = cell_model.rowCount()
        result = cell_model.removeRows(0, 1)
        assert result is True
        assert cell_model.rowCount() == initial_count - 1

    def test_remove_rows_invalid_index(self, cell_model):
        """Test removing rows with invalid index."""
        result = cell_model.removeRows(-1, 1)
        assert result is False
        result = cell_model.removeRows(100, 1)
        assert result is False

    def test_pop_model(self, cell_model):
        """Test popping a model."""
        initial_count = cell_model.rowCount()
        model = cell_model.pop_model(0)
        assert isinstance(model, MockElementModel)
        assert cell_model.rowCount() == initial_count - 1

    def test_data_display_role(self, cell_model):
        """Test data retrieval with DisplayRole."""
        index = cell_model.index(0, 0)
        data = cell_model.data(index, Qt.ItemDataRole.DisplayRole)
        assert data is not None

    def test_data_invalid_index(self, cell_model):
        """Test data retrieval with invalid index."""
        invalid_index = QModelIndex()
        data = cell_model.data(invalid_index)
        assert data == None

    def test_set_data(self, cell_model):
        """Test setting data at an index."""
        index = cell_model.index(0, 0)
        new_model = MockElementModel(number=99)
        result = cell_model.setData(index, new_model, Qt.ItemDataRole.EditRole)
        # Implementation details may vary
        assert result is True

    def test_flags(self, cell_model):
        """Test item flags."""
        index = cell_model.index(0, 0)
        flags = cell_model.flags(index)
        assert Qt.ItemFlag.ItemIsEditable in flags
        assert Qt.ItemFlag.ItemIsEnabled in flags
        assert Qt.ItemFlag.ItemIsSelectable in flags

    def test_mime_types(self, cell_model):
        """Test supported mime types."""
        mime_types = cell_model.mimeTypes()
        assert "application/x-teachart" in mime_types


class TestTableModel:
    """Test suite for TableModel class."""

    @pytest.fixture
    def table_model(self, qapp):
        """Fixture providing a TableModel."""
        return TableModel.new(3, 4)

    def test_table_model_new(self, qapp):
        """Test creating new TableModel with rows and columns."""
        model = TableModel.new(2, 3)
        assert model.rowCount() == 2
        assert model.columnCount() == 3

    def test_table_model_new_invalid_dimensions(self, qapp):
        """Test that invalid dimensions raise ValueError."""
        with pytest.raises(ValueError):
            TableModel.new(0, 3)
        with pytest.raises(ValueError):
            TableModel.new(3, 0)
        with pytest.raises(ValueError):
            TableModel.new(-1, 3)

    def test_row_count(self, table_model):
        """Test rowCount."""
        assert table_model.rowCount() == 3

    def test_column_count(self, table_model):
        """Test columnCount."""
        assert table_model.columnCount() == 4

    def test_model_id_is_unique(self, qapp):
        """Test that each model gets a unique ID."""
        model1 = TableModel.new(2, 2)
        model2 = TableModel.new(2, 2)
        assert model1.model_id != model2.model_id

    def test_insert_rows(self, table_model):
        """Test inserting rows."""
        initial_rows = table_model.rowCount()
        result = table_model.insertRows(1, 1)
        assert result is True
        assert table_model.rowCount() == initial_rows + 1

    def test_insert_columns(self, table_model):
        """Test inserting columns."""
        initial_cols = table_model.columnCount()
        result = table_model.insertColumns(1, 1)
        assert result is True
        assert table_model.columnCount() == initial_cols + 1

    def test_remove_rows(self, table_model):
        """Test removing rows."""
        initial_rows = table_model.rowCount()
        result = table_model.removeRows(0, 1)
        assert result is True
        assert table_model.rowCount() == initial_rows - 1

    def test_remove_rows_last_row_fails(self, qapp):
        """Test that removing last row fails."""
        model = TableModel.new(1, 2)
        result = model.removeRows(0, 1)
        assert result is False  # Can't remove last row

    def test_remove_columns(self, table_model):
        """Test removing columns."""
        initial_cols = table_model.columnCount()
        result = table_model.removeColumns(0, 1)
        assert result is True
        assert table_model.columnCount() == initial_cols - 1

    def test_remove_columns_last_column_fails(self, qapp):
        """Test that removing last column fails."""
        model = TableModel.new(2, 1)
        result = model.removeColumns(0, 1)
        assert result is False  # Can't remove last column

    def test_data_retrieval(self, table_model):
        """Test retrieving data from model."""
        index = table_model.index(0, 0)
        data = table_model.data(index, Qt.ItemDataRole.DisplayRole)
        assert isinstance(data, CellItem)

    def test_data_invalid_index(self, table_model):
        """Test data retrieval with invalid index."""
        invalid_index = QModelIndex()
        data = table_model.data(invalid_index)
        assert data == None

    def test_header_data_horizontal(self, qapp, table_model):
        """Test retrieving horizontal header data."""
        header = table_model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert header is not None

    def test_header_data_vertical(self, qapp, table_model):
        """Test retrieving vertical header data."""
        header = table_model.headerData(0, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole)
        assert header is not None

    def test_set_header_data(self, table_model):
        """Test setting header data."""
        result = table_model.setHeaderData(
            0, Qt.Orientation.Horizontal, "New Header", Qt.ItemDataRole.DisplayRole
        )
        # Implementation may vary
        assert isinstance(result, bool)

    def test_get_row(self, table_model):
        """Test getting a complete row."""
        row = table_model.get_row(0)
        assert isinstance(row, tuple)
        assert len(row) == table_model.columnCount()
        assert all(isinstance(cell, CellItem) for cell in row)

    def test_get_column(self, table_model):
        """Test getting a complete column."""
        column = table_model.get_column(0)
        assert isinstance(column, tuple)
        assert len(column) == table_model.rowCount()
        assert all(isinstance(cell, CellItem) for cell in column)

    def test_flags(self, table_model):
        """Test item flags."""
        index = table_model.index(0, 0)
        flags = table_model.flags(index)
        assert Qt.ItemFlag.ItemIsEditable in flags
        assert Qt.ItemFlag.ItemIsEnabled in flags
        assert Qt.ItemFlag.ItemIsSelectable in flags
        assert Qt.ItemFlag.ItemIsDropEnabled in flags
        assert Qt.ItemFlag.ItemIsDragEnabled in flags

    def test_mime_types(self, table_model):
        """Test supported mime types."""
        mime_types = table_model.mimeTypes()
        assert "application/x-teachart" in mime_types

    def test_supported_drop_actions(self, table_model):
        """Test supported drop actions."""
        actions = table_model.supportedDropActions()
        assert Qt.DropAction.MoveAction in actions
        assert Qt.DropAction.CopyAction in actions

    def test_clear(self, table_model):
        """Test clearing the table model."""
        table_model.clear()
        # After clear, internal data should be empty
        assert len(table_model._data) == 0
        assert len(table_model._header_data) == 0

    def test_counter_increments(self, table_model):
        """Test internal counter increments."""
        initial = table_model.counter()
        table_model.increase_counter()
        assert table_model.counter() == initial + 1


class TestMimeData:
    """Test suite for MIME data encoding and decoding."""

    def test_mime_data_dataclass(self):
        """Test MimeData dataclass creation."""
        mime_data = MimeData(
            model_id=123, level=1, table_row=2, table_column=3, cell_row=4, element_data=None
        )
        assert mime_data.model_id == 123
        assert mime_data.level == 1
        assert mime_data.table_row == 2
        assert mime_data.table_column == 3
        assert mime_data.cell_row == 4
        assert mime_data.element_data is None

    def test_encode_decode_mime_data_table_level(self, qapp):
        """Test encoding and decoding table-level mime data."""
        # Create QMimeData and encode
        mime_data = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        stream.writeUInt32(TCHA_IDENTIFIER)
        stream.writeInt16(999)  # model_id
        stream.writeInt8(0)  # level (table)
        stream.writeInt32(1)  # table_row
        stream.writeInt32(2)  # table_column
        stream.writeInt32(-1)  # cell_row

        mime_data.setData("application/x-teachart", encoded_data)

        # Decode
        decoded = decode_mime_data(mime_data)
        assert decoded is not None
        assert decoded.model_id == 999
        assert decoded.level == 0
        assert decoded.table_row == 1
        assert decoded.table_column == 2
        assert decoded.cell_row == -1

    def test_encode_decode_mime_data_cell_level(self, qapp):
        """Test encoding and decoding cell-level mime data."""
        mime_data = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        stream.writeUInt32(TCHA_IDENTIFIER)
        stream.writeInt16(777)  # model_id
        stream.writeInt8(1)  # level (cell)
        stream.writeInt32(0)  # table_row
        stream.writeInt32(1)  # table_column
        stream.writeInt32(2)  # cell_row

        mime_data.setData("application/x-teachart", encoded_data)

        # Decode
        decoded = decode_mime_data(mime_data)
        assert decoded is not None
        assert decoded.model_id == 777
        assert decoded.level == 1
        assert decoded.table_row == 0
        assert decoded.table_column == 1
        assert decoded.cell_row == 2

    def test_decode_invalid_identifier(self, qapp):
        """Test that invalid identifier returns None."""
        mime_data = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        stream.writeUInt32(0x12345678)  # Wrong identifier

        mime_data.setData("application/x-teachart", encoded_data)
        decoded = decode_mime_data(mime_data)
        assert decoded is None

    def test_decode_wrong_format(self, qapp):
        """Test that wrong MIME format returns None."""
        mime_data = QMimeData()
        mime_data.setText("plain text")
        decoded = decode_mime_data(mime_data)
        assert decoded is None

    def test_decode_with_element_data(self, qapp):
        """Test decoding mime data with element data."""
        mime_data = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        stream.writeUInt32(TCHA_IDENTIFIER)
        stream.writeInt16(555)
        stream.writeInt8(1)
        stream.writeInt32(0)
        stream.writeInt32(0)
        stream.writeInt32(0)

        # Write additional element data
        stream.writeQString("extra_data")

        mime_data.setData("application/x-teachart", encoded_data)

        decoded = decode_mime_data(mime_data)
        assert decoded is not None
        assert decoded.element_data is not None
        assert isinstance(decoded.element_data, QByteArray)


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for models working together."""

    def test_table_and_cell_model_integration(self, qapp):
        """Test TableModel and CellModel working together."""
        table = TableModel.new(2, 2)

        # Get a cell item from the table
        index = table.index(0, 0)
        cell_item = table.data(index, Qt.ItemDataRole.DisplayRole)

        # Create CellModel from the cell item
        cell_model = CellModel(cell_item, index)

        # Add a model to the cell
        mock_model = MockElementModel(number=0)
        cell_model.add_model(mock_model)

        # Verify it was added
        assert cell_model.rowCount() == 1
        assert len(cell_item) == 1

    def test_model_persistence_through_operations(self, qapp):
        """Test that model data persists through operations."""
        table = TableModel.new(3, 3)

        # Add some data to a cell
        index = table.index(1, 1)
        cell_item = table.data(index, Qt.ItemDataRole.DisplayRole)
        cell_item.append(MockElementModel(number=0))

        # Insert a row
        table.insertRows(0, 1)

        # The data should still exist (though index may change)
        assert table.rowCount() == 4

        # Remove the inserted row
        table.removeRows(0, 1)
        assert table.rowCount() == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
