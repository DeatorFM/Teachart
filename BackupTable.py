class TextDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter | None, option: QStyleOptionViewItem, index: QModelIndex, data: QTextDocument) -> None:
        # data.setTextWidth(option.rect.width() - 5)
        # data.setDocumentMargin(8.0)
        # option.rect = QRect(option.rect.topLeft(), data.size().toSize())
        # option.rect = option.rect.marginsAdded(QMargins(5, 5, 5, 5))

        painter.save()
        text_rect = QRectF(
            option.rect.left() + 5,
            option.rect.top() + 5,
            option.rect.width() - 10,
            option.rect.height() - 10
        )
        data.setTextWidth(text_rect.width())
        painter.translate(option.rect.topLeft() + QPoint(5, 5))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        data.drawContents(painter, QRectF(-5.0, -5.0, text_rect.width(), text_rect.height()))
        painter.restore()

    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget | None:
        # option.rect.setHeight(index.data().expected_height(option.rect.width()))
        editor = CustomTextEdit(parent)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return editor
    
    def setEditorData(self, editor: QTextEdit | None, index: QModelIndex, model: QTextDocument) -> None:
        editor.setDocument(model)

    def setModelData(self, editor: QTextEdit | None, model: QAbstractItemModel | None, index: QModelIndex) -> None:
        model.setData(index, editor.document())

    def updateEditorGeometry(self, editor: QTextEdit | None, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        option.rect = option.rect.marginsAdded(QMargins(-5, -5, -5, -5))
        editor.setGeometry(option.rect)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex, model: TextModel) -> QSize:
        size = model.size().toSize()
        size.setWidth(size.width() + 10)
        size.setHeight(size.height() + 10)
        return size